from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Facility, Organization


class IngestionSource(models.Model):
	class SourceType(models.TextChoices):
		SAP = 'SAP', 'SAP (Fuel/Procurement Export)'
		UTILITY = 'UTILITY', 'Utility Portal Export'
		TRAVEL = 'TRAVEL', 'Corporate Travel Export'

	org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sources')
	source_type = models.CharField(max_length=20, choices=SourceType.choices)
	name = models.CharField(max_length=200)
	config = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['org', 'source_type', 'name'], name='uniq_source_per_org'),
		]

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.org.slug}:{self.source_type}:{self.name}"


def upload_to_job(instance: 'IngestionJob', filename: str) -> str:
	# org/job_id/filename
	org_slug = getattr(instance.org, 'slug', 'org')
	return f"uploads/{org_slug}/jobs/{instance.id}/{filename}"


class IngestionJob(models.Model):
	class Status(models.TextChoices):
		CREATED = 'CREATED', 'Created'
		PARSED = 'PARSED', 'Parsed'
		PARTIAL = 'PARTIAL', 'Partial (Some Errors)'
		FAILED = 'FAILED', 'Failed'
		LOCKED = 'LOCKED', 'Locked for Audit'

	org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='jobs')
	source = models.ForeignKey(IngestionSource, on_delete=models.PROTECT, related_name='jobs')
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
	input_file = models.FileField(upload_to=upload_to_job, null=True, blank=True)

	received_rows = models.PositiveIntegerField(default=0)
	parsed_rows = models.PositiveIntegerField(default=0)
	failed_rows = models.PositiveIntegerField(default=0)
	suspicious_rows = models.PositiveIntegerField(default=0)
	approved_rows = models.PositiveIntegerField(default=0)

	created_at = models.DateTimeField(default=timezone.now)
	processed_at = models.DateTimeField(null=True, blank=True)
	locked_at = models.DateTimeField(null=True, blank=True)

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.org.slug}:{self.source.source_type}:{self.id}"


class RawRecord(models.Model):
	class Status(models.TextChoices):
		PARSED = 'PARSED', 'Parsed'
		ERROR = 'ERROR', 'Error'

	job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='raw_records')
	row_number = models.PositiveIntegerField()
	raw = models.JSONField(default=dict, blank=True)
	parsed = models.JSONField(default=dict, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices)
	error = models.TextField(blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['job', 'row_number'], name='uniq_raw_row_per_job'),
		]


class NormalizedRecord(models.Model):
	class ReviewStatus(models.TextChoices):
		PENDING = 'PENDING', 'Pending Review'
		APPROVED = 'APPROVED', 'Approved'
		REJECTED = 'REJECTED', 'Rejected'

	class Category(models.TextChoices):
		FUEL = 'FUEL', 'Fuel'
		PROCUREMENT = 'PROCUREMENT', 'Procurement'
		ELECTRICITY = 'ELECTRICITY', 'Electricity'
		TRAVEL_FLIGHT = 'TRAVEL_FLIGHT', 'Travel: Flight'
		TRAVEL_HOTEL = 'TRAVEL_HOTEL', 'Travel: Hotel'
		TRAVEL_GROUND = 'TRAVEL_GROUND', 'Travel: Ground'

	class Scope(models.TextChoices):
		S1 = 'SCOPE_1', 'Scope 1'
		S2 = 'SCOPE_2', 'Scope 2'
		S3 = 'SCOPE_3', 'Scope 3'

	org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='normalized_records')
	job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name='records')
	raw_record = models.ForeignKey(RawRecord, on_delete=models.SET_NULL, null=True, blank=True)

	category = models.CharField(max_length=30, choices=Category.choices)
	scope = models.CharField(max_length=20, choices=Scope.choices)

	# Common / traceability
	source_row_ref = models.CharField(max_length=120, blank=True)
	activity_date = models.DateField(null=True, blank=True)
	facility = models.ForeignKey(Facility, on_delete=models.SET_NULL, null=True, blank=True)
	description = models.CharField(max_length=300, blank=True)

	# Quantity normalization
	quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
	unit = models.CharField(max_length=32, blank=True)
	normalized_quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
	normalized_unit = models.CharField(max_length=32, blank=True)

	# Period fields (utility)
	period_start = models.DateField(null=True, blank=True)
	period_end = models.DateField(null=True, blank=True)

	# Procurement fields
	supplier = models.CharField(max_length=200, blank=True)
	spend_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
	spend_currency = models.CharField(max_length=8, blank=True)

	# Travel fields
	traveler = models.CharField(max_length=200, blank=True)
	origin = models.CharField(max_length=16, blank=True)
	destination = models.CharField(max_length=16, blank=True)
	distance_km = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True)

	# Review + audit
	review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
	suspicious = models.BooleanField(default=False)
	suspicious_reasons = models.JSONField(default=list, blank=True)
	is_locked = models.BooleanField(default=False)
	locked_at = models.DateTimeField(null=True, blank=True)
	approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_records')
	approved_at = models.DateTimeField(null=True, blank=True)

	created_at = models.DateTimeField(default=timezone.now)
	updated_at = models.DateTimeField(default=timezone.now)

	def save(self, *args, **kwargs):
		self.updated_at = timezone.now()
		super().save(*args, **kwargs)


class RecordEditLog(models.Model):
	record = models.ForeignKey(NormalizedRecord, on_delete=models.CASCADE, related_name='edit_logs')
	edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	edited_at = models.DateTimeField(default=timezone.now)
	reason = models.CharField(max_length=300, blank=True)
	before = models.JSONField(default=dict, blank=True)
	after = models.JSONField(default=dict, blank=True)
