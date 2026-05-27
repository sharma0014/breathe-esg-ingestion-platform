from django.contrib import admin

from .models import IngestionJob, IngestionSource, NormalizedRecord, RawRecord, RecordEditLog


@admin.register(IngestionSource)
class IngestionSourceAdmin(admin.ModelAdmin):
	list_display = ('org', 'source_type', 'name', 'created_at')
	list_filter = ('source_type',)
	search_fields = ('org__slug', 'name')


@admin.register(IngestionJob)
class IngestionJobAdmin(admin.ModelAdmin):
	list_display = ('id', 'org', 'source', 'status', 'received_rows', 'failed_rows', 'suspicious_rows', 'approved_rows', 'created_at')
	list_filter = ('status', 'source__source_type')


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
	list_display = ('job', 'row_number', 'status', 'created_at')
	list_filter = ('status',)


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
	list_display = ('id', 'org', 'job', 'category', 'scope', 'review_status', 'suspicious', 'is_locked', 'created_at')
	list_filter = ('category', 'scope', 'review_status', 'suspicious', 'is_locked')
	search_fields = ('org__slug', 'description', 'supplier', 'traveler', 'origin', 'destination')


@admin.register(RecordEditLog)
class RecordEditLogAdmin(admin.ModelAdmin):
	list_display = ('record', 'edited_by', 'edited_at', 'reason')
