from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
	email = models.EmailField(blank=True, null=True, unique=True)

	def __str__(self) -> str:  # pragma: no cover
		return self.email or self.username


class Organization(models.Model):
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=64, unique=True)
	created_at = models.DateTimeField(default=timezone.now)

	def __str__(self) -> str:  # pragma: no cover
		return self.name


class Membership(models.Model):
	class Role(models.TextChoices):
		ADMIN = 'ADMIN', 'Admin'
		ANALYST = 'ANALYST', 'Analyst'

	org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
	role = models.CharField(max_length=20, choices=Role.choices)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['org', 'user'], name='uniq_membership_org_user'),
		]

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.org.slug}:{self.user_id}:{self.role}"


class Facility(models.Model):
	org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='facilities')
	name = models.CharField(max_length=200)
	address = models.CharField(max_length=300, blank=True)
	country = models.CharField(max_length=2, blank=True, help_text='ISO 3166-1 alpha-2')
	external_codes = models.JSONField(default=dict, blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=['org', 'name'], name='uniq_facility_org_name'),
		]

	def __str__(self) -> str:  # pragma: no cover
		return f"{self.org.slug}:{self.name}"
