from django.contrib import admin
from .models import PrimarySkill, SubSkill, Session, Pathway, BuilderRun


@admin.register(PrimarySkill)
class PrimarySkillAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(SubSkill)
class SubSkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'primary_skill']
    list_filter = ['primary_skill']
    search_fields = ['name']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_number', 'title', 'role_applicability', 'is_manager_only']
    list_filter = ['is_manager_only']
    search_fields = ['title']
    ordering = ['session_number']


@admin.register(Pathway)
class PathwayAdmin(admin.ModelAdmin):
    list_display = ['name', 'role']
    list_filter = ['role']
    search_fields = ['name']


@admin.register(BuilderRun)
class BuilderRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'company_name', 'status', 'current_stage', 'created_at']
    list_filter = ['status', 'current_stage']
    search_fields = ['company_name', 'contact_email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
