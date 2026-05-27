from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Membership, Organization
from .serializers import MembershipSerializer, UserSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
	return Response(UserSerializer(request.user).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orgs(request):
	memberships = (
		Membership.objects
		.select_related('org')
		.filter(user=request.user, is_active=True)
		.order_by('org__name')
	)
	return Response(MembershipSerializer(memberships, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ensure_demo_org(request):
	"""Convenience endpoint for local demos.

	Creates an org + membership for the current user if they have none.
	Disabled in non-debug environments.
	"""

	from django.conf import settings

	if not settings.DEBUG:
		return Response({'detail': 'Not available'}, status=404)

	if Membership.objects.filter(user=request.user, is_active=True).exists():
		return Response({'detail': 'Already has org'}, status=200)

	org = Organization.objects.create(name='Demo Corp', slug='demo-corp')
	Membership.objects.create(org=org, user=request.user, role=Membership.Role.ADMIN)
	return Response({'detail': 'Created', 'org': {'slug': org.slug, 'name': org.name}}, status=201)
