from rest_framework import serializers

from .models import IngestionJob, IngestionSource, NormalizedRecord, RawRecord


class IngestionSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionSource
        fields = ['id', 'source_type', 'name', 'config', 'created_at']


class IngestionJobSerializer(serializers.ModelSerializer):
    source = IngestionSourceSerializer(read_only=True)

    class Meta:
        model = IngestionJob
        fields = [
            'id',
            'source',
            'status',
            'received_rows',
            'parsed_rows',
            'failed_rows',
            'suspicious_rows',
            'approved_rows',
            'created_at',
            'processed_at',
            'locked_at',
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ['id', 'row_number', 'status', 'error', 'raw', 'parsed', 'created_at']


class NormalizedRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NormalizedRecord
        fields = [
            'id',
            'category',
            'scope',
            'source_row_ref',
            'activity_date',
            'period_start',
            'period_end',
            'description',
            'quantity',
            'unit',
            'normalized_quantity',
            'normalized_unit',
            'supplier',
            'spend_amount',
            'spend_currency',
            'traveler',
            'origin',
            'destination',
            'distance_km',
            'review_status',
            'suspicious',
            'suspicious_reasons',
            'is_locked',
            'approved_by',
            'approved_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['approved_by', 'approved_at', 'created_at', 'updated_at']
