from django.core.management import BaseCommand
from django.db import transaction

from user_models.jexpo_ingestion import ExhibitorSchema
from user_models.jexpo_sync import update_or_create_company
import json

class Command(BaseCommand):
    help = "Synchronizes companies from an external API with the local database."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting company synchronization...")

        try:
            with open("export.json", "r") as f:
                exhibitors: list[ExhibitorSchema] = [ExhibitorSchema(**d) for d in json.load(f)]


            self.stdout.write(f"Extracted {len(exhibitors)} companies from the file.")

            with transaction.atomic():
                for schema in exhibitors:
                    company, created = update_or_create_company(schema)
                    if company:
                        self.stdout.write(f"{'Created' if created else 'Updated'} company: {company.name}")

            self.stdout.write(self.style.SUCCESS("Company synchronization completed successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))