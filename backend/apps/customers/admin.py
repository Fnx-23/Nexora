from django.contrib import admin

from apps.customers.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "company_name",
        "company",
        "email",
        "phone",
        "status",
        "is_active",
        "created_at",
    ]
    search_fields = ["name", "company_name", "email"]
    list_filter = ["status", "is_active"]
