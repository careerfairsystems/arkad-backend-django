from django.core.management import BaseCommand
from django.db import transaction
from companies.jexpo_ingestion import ExhibitorSchema
from companies.jexpo_sync import update_or_create_company
import json
import os

class Command(BaseCommand):
    help = "Synchronizes companies from an external API with the local database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file", type=str, default="export.json",
            help="Path to the JSON file containing company data."
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        abs_path = os.path.abspath(file_path)
        self.stdout.write(f"Starting company synchronization using file: {abs_path}")

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"File not found: {abs_path}"))
            return

        try:
            with open(file_path, "r") as f:
                exhibitors: list[ExhibitorSchema] = [ExhibitorSchema(**d) for d in json.load(f)]
            self.stdout.write(f"Extracted {len(exhibitors)} companies from the file.")

            with transaction.atomic():
                for schema in exhibitors:
                    company, created = update_or_create_company(schema)
                    if company:
                        self.stdout.write(f"{'Created' if created else 'Updated'} company: {company.name}")

            self.stdout.write(self.style.SUCCESS("Company synchronization completed successfully!"))
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR(f"Invalid JSON format in file: {abs_path}"))
