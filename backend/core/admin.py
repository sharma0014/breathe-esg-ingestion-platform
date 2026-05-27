from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Facility, Membership, Organization, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
	pass


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug', 'created_at')
	search_fields = ('name', 'slug')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
	list_display = ('org', 'user', 'role', 'is_active', 'created_at')
	list_filter = ('role', 'is_active')
	search_fields = ('org__slug', 'user__username', 'user__email')


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
	list_display = ('org', 'name', 'country', 'created_at')
	search_fields = ('org__slug', 'name')
