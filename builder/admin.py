"""
Bundle AI Training Builder — Django Admin
==========================================
Superadmin interface for managing AI agents, prompt sections, and run data.

Key features:
  • PromptSectionAdmin  — edit prompts with version history, one-click revert, cache invalidation
  • AgentConfigAdmin    — tune temperature / max_tokens / model per agent
  • BuilderRunAdmin     — view all runs, chat history, outputs
  • Standard CRUD admins for PrimarySkill, SubSkill, Session, Pathway
"""

from django import forms
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db import models as db_models
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe

from .models import (
    PrimarySkill, SubSkill, Session, Pathway, BuilderRun,
    AgentConfig, PromptSection, PromptSectionVersion,
)
from .ai_engine import invalidate_prompt_cache


# ─────────────────────────────────────────────────────────────────────────────
# Custom widgets / forms
# ─────────────────────────────────────────────────────────────────────────────

class PromptTextarea(forms.Textarea):
    """Large monospace textarea with word/char counter for prompt editing."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].update({
            'class':       'prompt-editor-textarea',
            'rows':        30,
            'spellcheck':  'false',
            'wrap':        'soft',
        })
        super().__init__(*args, **kwargs)


class PromptSectionForm(forms.ModelForm):
    class Meta:
        model = PromptSection
        fields = '__all__'
        widgets = {
            'content': PromptTextarea(),
            'description': forms.Textarea(attrs={'rows': 4, 'style': 'width:100%'}),
        }


# ─────────────────────────────────────────────────────────────────────────────
# AgentConfig admin
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AgentConfig)
class AgentConfigAdmin(admin.ModelAdmin):
    list_display  = ['label', 'key', 'model_name', 'temperature', 'max_tokens',
                     'is_active', 'section_count', 'updated_at']
    list_editable = ['model_name', 'temperature', 'max_tokens', 'is_active']
    readonly_fields = ['key', 'updated_at', 'section_list']

    fieldsets = [
        ('Agent Identity', {
            'fields': ('key', 'label', 'description'),
        }),
        ('Model Parameters', {
            'description': 'These settings are applied to every OpenAI call for this agent.',
            'fields': ('model_name', 'temperature', 'max_tokens', 'is_active'),
        }),
        ('Prompt Sections', {
            'fields': ('section_list',),
        }),
        ('Meta', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    ]

    def section_count(self, obj):
        n = obj.sections.filter(is_active=True).count()
        url = reverse('admin:builder_promptsection_changelist') + f'?agent__id__exact={obj.pk}'
        return format_html('<a href="{}">{} section{}</a>', url, n, 's' if n != 1 else '')
    section_count.short_description = 'Active sections'

    def section_list(self, obj):
        if not obj.pk:
            return '—'
        sections = obj.sections.order_by('order', 'key')
        if not sections:
            return 'No sections assigned yet.'
        rows = ''.join(
            f'<tr><td style="padding:4px 8px">{s.order}</td>'
            f'<td style="padding:4px 8px"><a href="{reverse("admin:builder_promptsection_change", args=[s.pk])}">'
            f'{escape(s.label)}</a></td>'
            f'<td style="padding:4px 8px">{"✅" if s.is_active else "❌"}</td></tr>'
            for s in sections
        )
        return format_html(
            '<table style="border-collapse:collapse;font-size:13px">'
            '<thead><tr><th style="padding:4px 8px;text-align:left">Order</th>'
            '<th style="padding:4px 8px;text-align:left">Section</th>'
            '<th style="padding:4px 8px">Active</th></tr></thead>'
            '<tbody>{}</tbody></table>', mark_safe(rows)
        )
    section_list.short_description = 'Prompt Sections'

    def has_delete_permission(self, request, obj=None):
        return False  # Agents are fixed — never delete

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        invalidate_prompt_cache(obj.key)
        self.message_user(request, f'Agent "{obj.label}" saved. Prompt cache cleared.', messages.SUCCESS)


# ─────────────────────────────────────────────────────────────────────────────
# PromptSectionVersion inline (read-only history)
# ─────────────────────────────────────────────────────────────────────────────

class PromptSectionVersionInline(admin.TabularInline):
    model     = PromptSectionVersion
    extra     = 0
    max_num   = 0   # no "add" rows
    can_delete = False
    readonly_fields = ['saved_at', 'saved_by', 'note', 'content_preview', 'revert_link']
    fields          = ['saved_at', 'saved_by', 'note', 'content_preview', 'revert_link']
    ordering        = ['-saved_at']
    verbose_name    = 'Previous Version'
    verbose_name_plural = 'Version History'

    def content_preview(self, obj):
        preview = obj.content[:200].replace('\n', '↵ ')
        if len(obj.content) > 200:
            preview += ' …'
        return format_html(
            '<code style="font-size:11px;white-space:pre-wrap;color:#555">{}</code>',
            preview,
        )
    content_preview.short_description = 'Content preview'

    def revert_link(self, obj):
        url = reverse('admin:builder_promptsection_change', args=[obj.section_id])
        return format_html(
            '<a class="button" style="font-size:11px;padding:3px 8px" '
            'href="{}?revert_version={}" '
            'onclick="return confirm(\'Revert to this version?\')">↩ Revert</a>',
            url, obj.pk,
        )
    revert_link.short_description = ''

    def has_add_permission(self, request, obj=None):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PromptSection admin — the main prompt editor
# ─────────────────────────────────────────────────────────────────────────────

class AgentFilter(SimpleListFilter):
    title        = 'agent'
    parameter_name = 'agent_scope'

    def lookups(self, request, model_admin):
        agents = AgentConfig.objects.order_by('key')
        choices = [('shared', '⚪ Shared (all agents)')]
        choices += [(str(a.pk), a.label) for a in agents]
        return choices

    def queryset(self, qs, value):
        if value == 'shared':
            return qs.filter(agent__isnull=True)
        if value:
            try:
                return qs.filter(agent_id=int(value))
            except (ValueError, TypeError):
                pass
        return qs


@admin.register(PromptSection)
class PromptSectionAdmin(admin.ModelAdmin):
    form           = PromptSectionForm
    list_display   = ['label', 'key', 'agent_badge', 'order', 'char_count',
                      'is_active', 'updated_at', 'updated_by']
    list_filter    = [AgentFilter, 'is_active']
    search_fields  = ['label', 'key', 'content', 'description']
    ordering       = ['order', 'key']
    readonly_fields = ['key', 'updated_at', 'updated_by', 'char_count_display', 'assembled_preview']
    inlines        = [PromptSectionVersionInline]
    actions        = ['preview_agent_prompt']

    fieldsets = [
        ('Section Identity', {
            'description': (
                '<strong style="color:#d9534f">⚠ Changing prompt content affects ALL future '
                'AI conversations immediately after saving.</strong> A version snapshot is '
                'automatically saved before every edit so you can always revert.'
            ),
            'fields': ('key', 'label', 'description', 'agent', 'order', 'is_active'),
        }),
        ('Prompt Content', {
            'description': (
                'Write the prompt section below. '
                'Use plain text or markdown-style formatting. '
                'The AI reads this verbatim — be precise.'
            ),
            'fields': ('content', 'char_count_display'),
        }),
        ('Assembled Preview', {
            'description': 'Shows how this section looks when the full prompt is assembled.',
            'fields': ('assembled_preview',),
            'classes': ('collapse',),
        }),
        ('Meta', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    ]

    class Media:
        css = {'all': ('builder/css/prompt_admin.css',)}
        js  = ('builder/js/prompt_admin.js',)

    # ── List display helpers ──────────────────────────────────────────────────

    def agent_badge(self, obj):
        if obj.agent is None:
            return format_html(
                '<span style="background:#6c757d;color:#fff;padding:2px 8px;'
                'border-radius:12px;font-size:11px">⚪ Shared</span>'
            )
        colours = {
            'context_collector': '#0d6efd',
            'analyzer':          '#198754',
            'plan_generator':    '#fd7e14',
            'general':           '#6f42c1',
        }
        colour = colours.get(obj.agent.key, '#555')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:12px;font-size:11px">{}</span>',
            colour, obj.agent.label.split('—')[0].strip(),
        )
    agent_badge.short_description = 'Agent'

    def char_count(self, obj):
        n = len(obj.content)
        colour = '#198754' if n < 2000 else ('#fd7e14' if n < 5000 else '#dc3545')
        return format_html('<span style="color:{};font-weight:600">{:,}</span>', colour, n)
    char_count.short_description = 'Chars'

    # ── Detail view helpers ───────────────────────────────────────────────────

    def char_count_display(self, obj):
        n = len(obj.content) if obj.content else 0
        words = len(obj.content.split()) if obj.content else 0
        return format_html(
            '<span style="font-size:13px;color:#666">'
            '{:,} characters · {:,} words</span>', n, words,
        )
    char_count_display.short_description = 'Content stats'

    def assembled_preview(self, obj):
        if not obj.content:
            return '—'
        lines = obj.content.split('\n')
        preview_lines = lines[:40]
        omitted = len(lines) - 40
        preview = '\n'.join(preview_lines)
        if omitted > 0:
            preview += f'\n\n… ({omitted} more lines)'
        return format_html(
            '<pre style="background:#f8f9fa;padding:12px;border-radius:4px;'
            'font-size:12px;white-space:pre-wrap;max-height:400px;overflow:auto;'
            'border:1px solid #dee2e6">{}</pre>',
            preview,
        )
    assembled_preview.short_description = 'Preview'

    # ── Save / revert logic ───────────────────────────────────────────────────

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        # Handle revert_version query param
        revert_pk = request.GET.get('revert_version')
        if revert_pk and obj:
            try:
                version = PromptSectionVersion.objects.get(pk=revert_pk, section=obj)
                obj.content = version.content
                request._revert_note = f'Reverted to version from {version.saved_at.strftime("%Y-%m-%d %H:%M")}'
            except PromptSectionVersion.DoesNotExist:
                pass
        return obj

    def save_model(self, request, obj, form, change):
        # Snapshot existing content BEFORE overwriting
        if change and 'content' in form.changed_data:
            note = getattr(request, '_revert_note', '')
            try:
                # Load the old content from DB before saving
                old = PromptSection.objects.get(pk=obj.pk)
                old.save_version(user=request.user, note=note)
            except PromptSection.DoesNotExist:
                pass

        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

        # Invalidate prompt cache for the affected agent
        agent_key = obj.agent.key if obj.agent else None
        if agent_key:
            invalidate_prompt_cache(agent_key)
        else:
            invalidate_prompt_cache()  # shared section → clear all agents

        msg = f'Prompt section "{obj.label}" saved.'
        if change and 'content' in form.changed_data:
            msg += ' Version snapshot created. Prompt cache cleared.'
        self.message_user(request, msg, messages.SUCCESS)

    # ── Admin actions ─────────────────────────────────────────────────────────

    @admin.action(description='🔍 Preview assembled prompt for this agent')
    def preview_agent_prompt(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Select exactly one section to preview its agent prompt.', messages.WARNING)
            return
        section = queryset.first()
        agent_key = section.agent.key if section.agent else 'shared'
        try:
            from .models import PromptSection as PS
            from django.db.models import Q
            sections = PS.objects.filter(is_active=True).filter(
                Q(agent__isnull=True) | Q(agent__key=agent_key)
            ).order_by('order', 'key')
            full = '\n\n---\n\n'.join(s.content for s in sections)
            return HttpResponse(
                f'<html><head><title>Prompt preview — {agent_key}</title>'
                '<style>body{{font-family:monospace;white-space:pre-wrap;padding:20px;'
                'line-height:1.6;max-width:900px;margin:0 auto}}'
                'h2{{font-family:sans-serif}}</style></head>'
                f'<body><h2>Assembled prompt — {agent_key}</h2>'
                f'<hr><pre>{escape(full)}</pre></body></html>'
            )
        except Exception as e:
            self.message_user(request, f'Preview error: {e}', messages.ERROR)

    def has_delete_permission(self, request, obj=None):
        # Prevent accidental deletion of seeded sections
        return request.user.is_superuser


# ─────────────────────────────────────────────────────────────────────────────
# Existing model admins
# ─────────────────────────────────────────────────────────────────────────────

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
    list_display  = ['id', 'company_name', 'agent_stage_badge', 'status',
                     'contact_email', 'created_at']
    list_filter   = ['status', 'current_stage', 'entry_point']
    search_fields = ['company_name', 'contact_email', 'contact_name']
    ordering      = ['-created_at']
    readonly_fields = [
        'created_at', 'updated_at',
        'chat_history_display', 'ai_analysis_display', 'final_plan_display',
    ]
    fieldsets = [
        ('Run Info', {
            'fields': ('user', 'status', 'current_stage', 'company_name',
                       'industry', 'team_size', 'created_at', 'updated_at'),
        }),
        ('Learner Profile', {
            'fields': ('role_title', 'seniority_level', 'training_goal',
                       'observed_challenges', 'success_metrics', 'training_constraints'),
        }),
        ('Data & Routing', {
            'fields': ('entry_point', 'focus_type', 'target_type', 'has_performance_data',
                       'budget_tier', 'timeline', 'selected_scenario', 'num_sessions'),
        }),
        ('Booking', {
            'fields': ('contact_name', 'contact_email', 'contact_phone',
                       'booked_date', 'booked_time'),
        }),
        ('Chat History', {
            'fields': ('chat_history_display',),
            'classes': ('collapse',),
        }),
        ('AI Analysis (Stage 4)', {
            'fields': ('ai_analysis_display',),
            'classes': ('collapse',),
        }),
        ('Final Plan (Stage 5)', {
            'fields': ('final_plan_display',),
            'classes': ('collapse',),
        }),
    ]

    def agent_stage_badge(self, obj):
        stage_labels = {
            1: ('Stage 1', '#0d6efd'),
            2: ('Stage 2', '#0d6efd'),
            3: ('Stage 3', '#198754'),
            4: ('Stage 4', '#198754'),
            5: ('Stage 5 — Plan', '#fd7e14'),
            6: ('Stage 6 — Booking', '#6f42c1'),
        }
        label, colour = stage_labels.get(obj.current_stage, (f'Stage {obj.current_stage}', '#555'))
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:12px;font-size:11px">{}</span>',
            colour, label,
        )
    agent_stage_badge.short_description = 'Stage'

    def chat_history_display(self, obj):
        try:
            import json
            history = json.loads(obj.chat_history or '[]')
            if not history:
                return 'No messages yet.'
            lines = []
            for msg in history[-30:]:
                role = '👤 User' if msg['role'] == 'user' else '🤖 AI'
                content = escape(str(msg.get('content', ''))[:400])
                lines.append(
                    f'<div style="margin-bottom:12px">'
                    f'<strong style="font-size:12px">{role}</strong><br>'
                    f'<span style="font-size:12px;white-space:pre-wrap">{content}</span></div>'
                )
            return format_html('<div style="max-height:500px;overflow-y:auto">{}</div>',
                               mark_safe(''.join(lines)))
        except Exception:
            return '(Could not parse chat history)'
    chat_history_display.short_description = 'Chat history'

    def ai_analysis_display(self, obj):
        if not obj.ai_analysis_json:
            return 'Not generated yet.'
        try:
            import json
            data = json.loads(obj.ai_analysis_json)
            return format_html(
                '<pre style="font-size:11px;max-height:400px;overflow:auto;'
                'background:#f8f9fa;padding:10px;border-radius:4px">{}</pre>',
                json.dumps(data, indent=2),
            )
        except Exception:
            return obj.ai_analysis_json[:2000]
    ai_analysis_display.short_description = 'AI Analysis JSON'

    def final_plan_display(self, obj):
        if not obj.final_plan_json:
            return 'Not generated yet.'
        try:
            import json
            data = json.loads(obj.final_plan_json)
            return format_html(
                '<pre style="font-size:11px;max-height:400px;overflow:auto;'
                'background:#f8f9fa;padding:10px;border-radius:4px">{}</pre>',
                json.dumps(data, indent=2),
            )
        except Exception:
            return obj.final_plan_json[:2000]
    final_plan_display.short_description = 'Final Plan JSON'
