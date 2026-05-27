from rest_framework import serializers

from .models import Membership, Organization, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'created_at']


class MembershipSerializer(serializers.ModelSerializer):
    org = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'org', 'role', 'is_active', 'created_at']
