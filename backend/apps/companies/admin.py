from django.contrib import admin

from apps.companies.models import Company, Membership, TeamInvitation


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    search_fields = ["name", "slug"]
    list_filter = ["is_active"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "company", "role", "is_active", "created_at"]
    search_fields = ["user__email", "company__name"]
    list_filter = ["role", "is_active"]


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "company", "role", "status", "expires_at", "created_at"]
    search_fields = ["email", "company__name"]
    list_filter = ["status", "role", "company"]
    readonly_fields = ["token_hash"]
