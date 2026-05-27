import json
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Facility, Membership, Organization

from .models import IngestionJob, IngestionSource, NormalizedRecord, RawRecord, RecordEditLog
from .parsers import parse_sap_export, parse_travel_export, parse_utility_export
from .parsers.utils import _to_decimal, normalize_unit, parse_date, suspicious_reasons_for
from .serializers import (
	IngestionJobSerializer,
	IngestionSourceSerializer,
	NormalizedRecordSerializer,
	RawRecordSerializer,
)


def _require_org(request, org_slug: str) -> Organization:
	org = get_object_or_404(Organization, slug=org_slug)
	if request.user.is_superuser:
		return org
	if not Membership.objects.filter(org=org, user=request.user, is_active=True).exists():
		# avoid leaking whether the org exists
		raise PermissionError('Not a member')
	return org


def _json_safe(value):
	if isinstance(value, Decimal):
		return str(value)
	if isinstance(value, (date,)):
		return value.isoformat()
	if isinstance(value, dict):
		return {k: _json_safe(v) for k, v in value.items()}
	if isinstance(value, list):
		return [_json_safe(v) for v in value]
	return value


def _ensure_source(org: Organization, source_type: str, name: str) -> IngestionSource:
	src, _ = IngestionSource.objects.get_or_create(org=org, source_type=source_type, name=name, defaults={'config': {}})
	return src


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sources(request, org_slug: str):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	if request.method == 'GET':
		qs = IngestionSource.objects.filter(org=org).order_by('source_type', 'name')
		return Response(IngestionSourceSerializer(qs, many=True).data)

	serializer = IngestionSourceSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	src = IngestionSource.objects.create(
		org=org,
		source_type=serializer.validated_data['source_type'],
		name=serializer.validated_data['name'],
		config=serializer.validated_data.get('config') or {},
	)
	return Response(IngestionSourceSerializer(src).data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jobs(request, org_slug: str):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	qs = IngestionJob.objects.select_related('source').filter(org=org).order_by('-created_at')
	return Response(IngestionJobSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_detail(request, org_slug: str, job_id: int):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	job = get_object_or_404(IngestionJob.objects.select_related('source'), org=org, id=job_id)
	return Response(IngestionJobSerializer(job).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_records(request, org_slug: str, job_id: int):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	job = get_object_or_404(IngestionJob, org=org, id=job_id)
	status_filter = request.query_params.get('review_status')
	suspicious_only = request.query_params.get('suspicious') == '1'
	qs = NormalizedRecord.objects.filter(org=org, job=job).order_by('id')
	if status_filter:
		qs = qs.filter(review_status=status_filter)
	if suspicious_only:
		qs = qs.filter(suspicious=True)
	return Response(NormalizedRecordSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_errors(request, org_slug: str, job_id: int):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	job = get_object_or_404(IngestionJob, org=org, id=job_id)
	qs = RawRecord.objects.filter(job=job, status=RawRecord.Status.ERROR).order_by('row_number')
	return Response(RawRecordSerializer(qs, many=True).data)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def upload_and_ingest(request, org_slug: str):
	"""Upload a file and ingest it into an IngestionJob.

	Request fields:
	- source_type: SAP | UTILITY | TRAVEL
	- source_name: optional
	- file: multipart file
	"""

	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	source_type = (request.data.get('source_type') or '').strip().upper()
	if source_type not in {IngestionSource.SourceType.SAP, IngestionSource.SourceType.UTILITY, IngestionSource.SourceType.TRAVEL}:
		return Response({'detail': 'Invalid source_type'}, status=400)

	upload = request.FILES.get('file')
	if not upload:
		return Response({'detail': 'Missing file'}, status=400)

	# Read bytes *before* saving to a FileField; otherwise Django may consume the stream.
	data = upload.read()
	try:
		upload.seek(0)
	except Exception:
		pass

	source_name = (request.data.get('source_name') or f"{source_type} Upload").strip()

	src = _ensure_source(org, source_type, source_name)

	with transaction.atomic():
		job = IngestionJob.objects.create(org=org, source=src, created_by=request.user, input_file=upload)
	if source_type == IngestionSource.SourceType.SAP:
		parsed_rows = parse_sap_export(data, source_config=src.config)
	elif source_type == IngestionSource.SourceType.UTILITY:
		parsed_rows = parse_utility_export(data, source_config=src.config)
	else:
		parsed_rows = parse_travel_export(data, source_config=src.config)

	received_rows = len(parsed_rows)
	parsed_ok = 0
	failed = 0
	suspicious = 0

	# Persist
	with transaction.atomic():
		for pr in parsed_rows:
			if pr.error:
				RawRecord.objects.create(
					job=job,
					row_number=pr.row_number,
					raw=_json_safe(pr.raw),
					parsed=_json_safe(pr.parsed),
					status=RawRecord.Status.ERROR,
					error=pr.error,
				)
				failed += 1
				continue

			raw_rec = RawRecord.objects.create(
				job=job,
				row_number=pr.row_number,
				raw=_json_safe(pr.raw),
				parsed=_json_safe(pr.parsed),
				status=RawRecord.Status.PARSED,
				error='',
			)
			parsed_ok += 1

			facility = None
			facility_name = pr.parsed.get('facility_name')
			if facility_name:
				facility, _ = Facility.objects.get_or_create(org=org, name=facility_name, defaults={'external_codes': {}})

			rec = NormalizedRecord.objects.create(
				org=org,
				job=job,
				raw_record=raw_rec,
				category=pr.parsed['category'],
				scope=pr.parsed['scope'],
				source_row_ref=pr.parsed.get('source_row_ref', ''),
				activity_date=pr.parsed.get('activity_date'),
				period_start=pr.parsed.get('period_start'),
				period_end=pr.parsed.get('period_end'),
				facility=facility,
				description=pr.parsed.get('description', ''),
				quantity=pr.parsed.get('quantity'),
				unit=pr.parsed.get('unit', ''),
				normalized_quantity=pr.parsed.get('normalized_quantity'),
				normalized_unit=pr.parsed.get('normalized_unit', ''),
				supplier=pr.parsed.get('supplier', ''),
				spend_amount=pr.parsed.get('spend_amount'),
				spend_currency=pr.parsed.get('spend_currency', ''),
				traveler=pr.parsed.get('traveler', ''),
				origin=pr.parsed.get('origin', ''),
				destination=pr.parsed.get('destination', ''),
				distance_km=pr.parsed.get('distance_km'),
				suspicious=bool(pr.parsed.get('suspicious')),
				suspicious_reasons=pr.parsed.get('suspicious_reasons') or [],
			)
			if rec.suspicious:
				suspicious += 1

		job.received_rows = received_rows
		job.parsed_rows = parsed_ok
		job.failed_rows = failed
		job.suspicious_rows = suspicious
		job.processed_at = timezone.now()
		if parsed_ok == 0:
			job.status = IngestionJob.Status.FAILED
		elif failed > 0:
			job.status = IngestionJob.Status.PARTIAL
		else:
			job.status = IngestionJob.Status.PARSED
		job.save()

	return Response(IngestionJobSerializer(job).data, status=201)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_record(request, org_slug: str, record_id: int):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	record = get_object_or_404(NormalizedRecord, org=org, id=record_id)
	if record.is_locked or record.job.status == IngestionJob.Status.LOCKED:
		return Response({'detail': 'Record is locked'}, status=409)

	before = NormalizedRecordSerializer(record).data

	# allow edits to a limited set of fields
	for field in ['description', 'supplier', 'spend_currency', 'traveler', 'origin', 'destination', 'unit', 'normalized_unit']:
		if field in request.data:
			setattr(record, field, request.data.get(field) or '')

	for field in ['activity_date', 'period_start', 'period_end']:
		if field in request.data:
			setattr(record, field, parse_date(request.data.get(field)))

	for field in ['quantity', 'spend_amount', 'distance_km', 'normalized_quantity']:
		if field in request.data:
			setattr(record, field, _to_decimal(request.data.get(field)))

	# If quantity/unit changed, recompute normalized quantity/unit when possible
	if 'quantity' in request.data or 'unit' in request.data:
		nq, nu = normalize_unit(record.quantity, record.unit)
		record.normalized_quantity = nq
		record.normalized_unit = nu

	# recompute suspicious
	temp = {
		'category': record.category,
		'normalized_unit': record.normalized_unit,
		'normalized_quantity': record.normalized_quantity,
		'quantity': record.quantity,
		'period_start': record.period_start,
		'period_end': record.period_end,
		'activity_date': record.activity_date,
		'spend_amount': record.spend_amount,
		'spend_currency': record.spend_currency,
		'origin': record.origin,
		'destination': record.destination,
		'distance_km': record.distance_km,
	}
	reasons = suspicious_reasons_for(temp)
	record.suspicious_reasons = reasons
	record.suspicious = len(reasons) > 0
	record.save()

	after = NormalizedRecordSerializer(record).data
	RecordEditLog.objects.create(
		record=record,
		edited_by=request.user,
		reason=(request.data.get('reason') or '').strip(),
		before=before,
		after=after,
	)

	# Keep job suspicious_rows roughly correct
	job = record.job
	job.suspicious_rows = NormalizedRecord.objects.filter(job=job, suspicious=True).count()
	job.save(update_fields=['suspicious_rows'])

	return Response(after)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_record(request, org_slug: str, record_id: int):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	record = get_object_or_404(NormalizedRecord, org=org, id=record_id)
	if record.is_locked or record.job.status == IngestionJob.Status.LOCKED:
		return Response({'detail': 'Job is locked'}, status=409)

	if record.review_status != NormalizedRecord.ReviewStatus.APPROVED:
		record.review_status = NormalizedRecord.ReviewStatus.APPROVED
		record.approved_by = request.user
		record.approved_at = timezone.now()
		record.save()

	job = record.job
	job.approved_rows = NormalizedRecord.objects.filter(job=job, review_status=NormalizedRecord.ReviewStatus.APPROVED).count()
	job.save(update_fields=['approved_rows'])

	return Response(NormalizedRecordSerializer(record).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def lock_job(request, org_slug: str, job_id: int):
	try:
		org = _require_org(request, org_slug)
	except PermissionError:
		return Response({'detail': 'Not found'}, status=404)

	job = get_object_or_404(IngestionJob, org=org, id=job_id)
	if job.status == IngestionJob.Status.LOCKED:
		return Response(IngestionJobSerializer(job).data)

	pending = NormalizedRecord.objects.filter(job=job, review_status=NormalizedRecord.ReviewStatus.PENDING).count()
	if pending > 0:
		return Response({'detail': 'Cannot lock job with pending records', 'pending': pending}, status=409)

	with transaction.atomic():
		job.status = IngestionJob.Status.LOCKED
		job.locked_at = timezone.now()
		job.save(update_fields=['status', 'locked_at'])
		NormalizedRecord.objects.filter(job=job).update(is_locked=True, locked_at=job.locked_at)

	return Response(IngestionJobSerializer(job).data)
