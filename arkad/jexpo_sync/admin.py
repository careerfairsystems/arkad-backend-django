from typing import Any
from django.contrib import admin
from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
import json
import os
from .models import CompanySyncUpload
from jexpo_sync.jexpo_ingestion import ExhibitorSchema
from jexpo_sync.jexpo_sync import update_or_create_company


@admin.register(CompanySyncUpload)
class CompanySyncUploadAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = [
        "id",
        "file",
        "status",
        "companies_processed",
        "companies_created",
        "companies_updated",
        "uploaded_by",
        "uploaded_at",
        "processed_at",
    ]
    list_filter = ["status", "uploaded_at", "processed_at", "uploaded_by"]
    readonly_fields = [
        "uploaded_at",
        "processed_at",
        "companies_processed",
        "companies_created",
        "companies_updated",
        "error_message",
    ]
    actions = ["process_uploads", "delete_with_files"]

    def get_queryset(self, request: HttpRequest) -> QuerySet[CompanySyncUpload]:
        """Limit queryset to user's own uploads unless they're superuser"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(uploaded_by=request.user)
        return qs

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Check if user has permission to upload files"""
        return request.user.has_perm("jexpo_sync.can_upload_company_sync")

    def has_change_permission(
        self, request: HttpRequest, obj: CompanySyncUpload | None = None
    ) -> bool:
        """Users can only modify their own uploads"""
        if obj is None:
            return True
        return request.user.is_superuser or obj.uploaded_by == request.user

    def has_delete_permission(
        self, request: HttpRequest, obj: CompanySyncUpload | None = None
    ) -> bool:
        """Users can only delete their own uploads"""
        if obj is None:
            return True
        return request.user.is_superuser or obj.uploaded_by == request.user

    def save_model(
        self, request: HttpRequest, obj: CompanySyncUpload, form: Any, change: bool
    ) -> None:
        if not change:  # Only set user on creation
            obj.uploaded_by = request.user  # type: ignore[assignment]
        super().save_model(request, obj, form, change)

        # Auto-process the upload if it's pending
        if obj.status == "pending":
            self.process_single_upload(request, obj)

    def process_single_upload(
        self, request: HttpRequest, upload_obj: CompanySyncUpload
    ) -> None:
        """Process a single upload object with enhanced security"""
        # Check permissions
        if not self.has_change_permission(request, upload_obj):
            messages.error(request, "You don't have permission to process this file.")
            return

        try:
            upload_obj.status = "processing"
            upload_obj.save()

            # Validate file exists and is accessible
            if not upload_obj.file or not os.path.exists(upload_obj.file.path):
                raise ValueError("File not found or inaccessible")

            # Read and process the JSON file
            with upload_obj.file.open("r") as f:
                content = f.read()

                # Parse JSON with validation
                data = json.loads(content)

                # Validate it's a list
                if not isinstance(data, list):
                    raise ValueError("JSON must contain an array of exhibitor objects")

            # Process exhibitors
            exhibitors = []
            for i, d in enumerate(data):
                try:
                    exhibitor = ExhibitorSchema(**ExhibitorSchema.preprocess(d))
                    exhibitors.append(exhibitor)
                except Exception as e:
                    raise ValueError(f"Invalid exhibitor data at index {i}: {str(e)}")

            companies_created = 0
            companies_updated = 0
            companies_processed = 0

            with transaction.atomic():
                for schema in exhibitors:
                    company, created = update_or_create_company(schema)
                    if company:
                        companies_processed += 1
                        if created:
                            companies_created += 1
                        else:
                            companies_updated += 1

            # Update the upload record
            upload_obj.status = "completed"
            upload_obj.companies_processed = companies_processed
            upload_obj.companies_created = companies_created
            upload_obj.companies_updated = companies_updated
            upload_obj.processed_at = timezone.now()
            upload_obj.error_message = None
            upload_obj.save()

            messages.success(
                request,
                f"Successfully processed {companies_processed} companies "
                f"({companies_created} created, {companies_updated} updated)",
            )

        except json.JSONDecodeError as e:
            upload_obj.status = "failed"
            upload_obj.error_message = f"Invalid JSON format: {str(e)}"
            upload_obj.processed_at = timezone.now()
            upload_obj.save()
            messages.error(request, f"JSON decode error: {str(e)}")

        except Exception as e:
            upload_obj.status = "failed"
            upload_obj.error_message = str(e)
            upload_obj.processed_at = timezone.now()
            upload_obj.save()
            messages.error(request, f"Processing error: {str(e)}")

    def process_uploads(
        self, request: HttpRequest, queryset: QuerySet[CompanySyncUpload]
    ) -> None:
        """Admin action to process selected uploads"""
        processed_count = 0
        for upload_obj in queryset.filter(status="pending"):
            if self.has_change_permission(request, upload_obj):
                self.process_single_upload(request, upload_obj)
                processed_count += 1

        if processed_count == 0:
            messages.warning(
                request,
                "No pending uploads found to process (or insufficient permissions).",
            )
        else:
            messages.success(request, f"Processed {processed_count} uploads.")

    process_uploads.short_description = "Process selected uploads"  # type: ignore[attr-defined]

    def delete_with_files(
        self, request: HttpRequest, queryset: QuerySet[CompanySyncUpload]
    ) -> None:
        """Admin action to delete uploads and their files"""
        deleted_count = 0
        for upload_obj in queryset:
            if self.has_delete_permission(request, upload_obj):
                upload_obj.delete()  # This will trigger our custom delete method
                deleted_count += 1

        if deleted_count == 0:
            messages.warning(request, "No uploads deleted (insufficient permissions).")
        else:
            messages.success(
                request, f"Deleted {deleted_count} uploads and their files."
            )

    delete_with_files.short_description = "Delete selected uploads and files"  # type: ignore[attr-defined]

    def get_urls(self) -> list[Any]:
        urls = super().get_urls()
        custom_urls = [
            path(
                "upload-companies/",
                self.admin_site.admin_view(self.upload_companies_view),
                name="jexpo_sync_upload_companies",
            ),
        ]
        return custom_urls + urls

    def upload_companies_view(self, request: HttpRequest) -> HttpResponse:
        """Custom view for uploading company data with permission checks"""
        # Check permissions
        if not self.has_add_permission(request):
            raise PermissionDenied(
                "You don't have permission to upload company sync files."
            )

        if request.method == "POST" and request.FILES.get("json_file"):
            try:
                # Create upload record
                upload_obj = CompanySyncUpload.objects.create(  # type: ignore[attr-defined, misc]
                    file=request.FILES["json_file"],
                    uploaded_by=request.user,
                    status="pending",
                )

                # Process the upload
                self.process_single_upload(request, upload_obj)

                return HttpResponseRedirect("../")

            except Exception as e:
                messages.error(request, f"Upload failed: {str(e)}")

        context = {
            "title": "Upload Company Sync File",
            "opts": self.model._meta,
        }
        return render(request, "admin/jexpo_sync/upload_companies.html", context)
