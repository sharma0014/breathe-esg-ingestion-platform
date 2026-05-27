from django.core.management.base import BaseCommand

from core.models import Facility, Membership, Organization, User
from ingest.models import IngestionSource


class Command(BaseCommand):
    help = 'Seed a demo org, users, facilities, and sources for local testing.'

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(name='ACME Enterprise', slug='acme-enterprise')

        admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@acme.test'})
        if created:
            admin_user.set_password('demo1234')
            admin_user.is_staff = True
            admin_user.save()

        analyst_user, created = User.objects.get_or_create(username='analyst', defaults={'email': 'analyst@acme.test'})
        if created:
            analyst_user.set_password('demo1234')
            analyst_user.save()

        Membership.objects.get_or_create(org=org, user=admin_user, defaults={'role': Membership.Role.ADMIN})
        Membership.objects.get_or_create(org=org, user=analyst_user, defaults={'role': Membership.Role.ANALYST})

        # Facilities (used by SAP plant mapping)
        berlin, _ = Facility.objects.get_or_create(org=org, name='Berlin Plant', defaults={'country': 'DE'})
        munich, _ = Facility.objects.get_or_create(org=org, name='Munich DC', defaults={'country': 'DE'})

        sap_src, _ = IngestionSource.objects.get_or_create(
            org=org,
            source_type=IngestionSource.SourceType.SAP,
            name='SAP Upload',
            defaults={
                'config': {
                    'plant_code_to_facility': {
                        '1000': berlin.name,
                        '2000': munich.name,
                    }
                }
            },
        )

        IngestionSource.objects.get_or_create(
            org=org,
            source_type=IngestionSource.SourceType.UTILITY,
            name='Utility Upload',
            defaults={'config': {}},
        )

        IngestionSource.objects.get_or_create(
            org=org,
            source_type=IngestionSource.SourceType.TRAVEL,
            name='Travel Upload',
            defaults={'config': {}},
        )

        self.stdout.write(self.style.SUCCESS('Seeded demo data'))
        self.stdout.write('Org slug: acme-enterprise')
        self.stdout.write('Users: admin / demo1234, analyst / demo1234')
