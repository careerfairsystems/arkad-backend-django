from django.core.management import BaseCommand
from django.db import transaction

from user_models.jexpo_ingestion import CompanySchema
from user_models.jexpo_sync import update_or_create_company


class Command(BaseCommand):
    help = "Synchronizes companies from an external API with the local database."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting company synchronization...")

        try:
            schemas = CompanySchema.fetch()
            self.stdout.write(f"Fetched {len(schemas)} companies from the API.")

            with transaction.atomic():
                for schema in schemas:
                    company = update_or_create_company(schema)
                    if company:
                        self.stdout.write(f"Processed company: {company.name}")

            self.stdout.write(self.style.SUCCESS("Company synchronization completed successfully!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))