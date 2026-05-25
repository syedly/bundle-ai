import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class PrimarySkill(models.Model):
    name = models.CharField(max_length=200, unique=True)
    definition = models.TextField()

    def __str__(self):
        return self.name


class SubSkill(models.Model):
    primary_skill = models.ForeignKey(PrimarySkill, on_delete=models.CASCADE, related_name='sub_skills')
    name = models.CharField(max_length=200)
    definition = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Session(models.Model):
    session_number = models.IntegerField(default=0)
    title = models.CharField(max_length=300)
    primary_skills_text = models.TextField(blank=True)
    sub_skills_text = models.TextField(blank=True)
    role_applicability = models.CharField(max_length=200, default='Mgr, NM, IC')
    is_manager_only = models.BooleanField(default=False)
    program_tag = models.CharField(max_length=100, blank=True)
    trainer_tag = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    foundational_outcomes = models.TextField(blank=True)
    intermediate_outcomes = models.TextField(blank=True)
    advanced_outcomes = models.TextField(blank=True)
    expert_outcomes = models.TextField(blank=True)

    class Meta:
        ordering = ['session_number']

    def __str__(self):
        return f"Session {self.session_number}: {self.title}"


class Pathway(models.Model):
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    session_titles = models.TextField(blank=True)

    def get_session_list(self):
        return [s.strip() for s in self.session_titles.split('\n') if s.strip()]

    def __str__(self):
        return self.name


class BuilderRun(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('recommendation_ready', 'Recommendation Ready'),
        ('plan_generated', 'Plan Generated'),
        ('cta_clicked', 'CTA Clicked'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='builder_runs',
    )
    session_key = models.CharField(max_length=200, db_index=True, blank=True)
    title = models.CharField(max_length=200, blank=True)  # display name in thread list
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='in_progress')
    current_stage = models.IntegerField(default=1)
    # Stage 1 context
    company_name = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=200, blank=True)
    team_size = models.CharField(max_length=100, blank=True)
    training_goal = models.TextField(blank=True)
    focus_type = models.CharField(max_length=50, blank=True)
    budget_tier = models.CharField(max_length=30, blank=True)
    timeline = models.CharField(max_length=200, blank=True)
    # Learner profile (new)
    role_title = models.CharField(max_length=200, blank=True)
    seniority_level = models.CharField(max_length=100, blank=True)
    observed_challenges = models.TextField(blank=True)
    success_metrics = models.TextField(blank=True)
    training_constraints = models.TextField(blank=True)
    # Stage 2 data
    entry_point = models.CharField(max_length=30, blank=True)
    target_type = models.CharField(max_length=20, blank=True)
    has_performance_data = models.CharField(max_length=20, blank=True)
    uploaded_data = models.TextField(blank=True)
    jd_content = models.TextField(blank=True)
    diagnostic_answers = models.TextField(blank=True)
    # Outputs
    selected_scenario = models.CharField(max_length=5, blank=True)
    num_sessions = models.IntegerField(default=0)
    ai_analysis_json = models.TextField(blank=True, default='')
    final_plan_json = models.TextField(blank=True, default='')
    final_plan = models.TextField(blank=True)
    # Chat
    chat_history = models.TextField(blank=True, default='[]')
    # User flags / feedback on recommendations
    user_flags = models.TextField(blank=True, default='[]')
    # Booking
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    booked_date = models.CharField(max_length=50, blank=True)
    booked_time = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def get_chat_history(self):
        try:
            return json.loads(self.chat_history)
        except Exception:
            return []

    def set_chat_history(self, history):
        self.chat_history = json.dumps(history)

    def display_title(self):
        if self.company_name:
            return self.company_name
        if self.title:
            return self.title
        return f"Conversation #{self.id}"

    def get_ai_analysis(self):
        try:
            if not self.ai_analysis_json:
                return None
            data = json.loads(self.ai_analysis_json)
            # Normalize old flat format (no 'people' key) to the new people-array format
            if 'people' not in data:
                data = {
                    'header_title': data.get('header_title', self.company_name or ''),
                    'people': [{
                        'name': data.get('header_title', 'Employee'),
                        'role_title': '',
                        'confidence': data.get('confidence', 'Moderate confidence'),
                        'confidence_rationale': data.get('confidence_rationale', ''),
                        'summary_paragraph': data.get('summary_paragraph', ''),
                        'growth_opportunities': data.get('growth_opportunities', []),
                        'recommended_delivery': '1:1 Training + Coaching',
                        'recommended_sessions': 6,
                        'delivery_options': data.get('delivery_options', []),
                        'depth_options': data.get('depth_options', {}),
                        'sequencing_logic': data.get('sequencing_logic', ''),
                    }],
                    'generated_at': data.get('generated_at', ''),
                }
            return data
        except (json.JSONDecodeError, TypeError):
            return None

    def get_final_plan_data(self):
        try:
            if self.final_plan_json:
                return json.loads(self.final_plan_json)
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    def __str__(self):
        return f"BuilderRun {self.id} — {self.display_title()}"


# ── Agent & Prompt management ─────────────────────────────────────────────────

class AgentConfig(models.Model):
    """One record per AI agent role. Tune temperature, tokens, model — all via admin."""

    AGENT_KEYS = [
        ('context_collector', 'Context Collector — Stage 1 & 2 (question flow)'),
        ('analyzer',          'Analyzer — Stage 3 & 4 (recommendation)'),
        ('plan_generator',    'Plan Generator — Stage 5 (full training plan)'),
        ('general',           'General — Stage 6 & fallback'),
    ]

    key         = models.CharField(max_length=50, unique=True, choices=AGENT_KEYS)
    label       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    model_name  = models.CharField(
        max_length=100, default='gpt-4o',
        help_text='OpenAI model for this agent (e.g. gpt-4o, gpt-4o-mini)',
    )
    temperature = models.FloatField(default=0.7)
    max_tokens  = models.IntegerField(default=8000)
    is_active   = models.BooleanField(default=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = 'Agent Config'
        verbose_name_plural = 'Agent Configs'

    def __str__(self):
        return self.label


class PromptSection(models.Model):
    """
    One named section of a system prompt.
    Shared sections (agent=None) are included in every agent.
    Agent-specific sections are included only for their agent.
    Sections are assembled in `order` sequence at runtime.
    """

    SECTION_KEYS = [
        # ── Shared (all agents) ──────────────────────────────────────
        ('identity',          'AI Identity & Role'),
        ('critical_rules',    'Critical Rules — Never Violate'),
        ('brand_tone',        'Brand Tone'),
        ('data_saving',       'Data Saving Instructions'),
        ('suggestions_rules', 'Suggestions — Rules & Format'),
        # ── Context Collector ────────────────────────────────────────
        ('stage_1_flow',      'Stage 1 — Context Collection Flow (Q1-Q14)'),
        ('stage_2_paths',     'Stage 2 — Data Input Paths (A / B / C)'),
        # ── Analyzer ────────────────────────────────────────────────
        ('confidence_logic',  'Confidence Score Logic'),
        ('stage_4_format',    'Stage 4 — Recommendation Format'),
        ('length_depth_rules','Length & Depth Rules'),
        # ── Plan Generator ───────────────────────────────────────────
        ('stage_5_format',    'Stage 5 — Training Plan Format'),
        ('stage_5_rules',     'Stage 5 — Critical Rules'),
        ('tool_instructions', 'Tool Call Instructions'),
        # ── General / Booking ────────────────────────────────────────
        ('stage_6_booking',   'Stage 6 — Booking Flow'),
    ]

    key         = models.CharField(max_length=60, unique=True, choices=SECTION_KEYS)
    label       = models.CharField(max_length=200)
    content     = models.TextField()
    description = models.TextField(
        blank=True,
        help_text='What this section controls and what to be careful about when editing.',
    )
    agent = models.ForeignKey(
        AgentConfig,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sections',
        help_text='Which agent uses this section. Leave blank = shared (all agents).',
    )
    order = models.PositiveSmallIntegerField(
        default=10,
        help_text='Assembly order — lower numbers appear earlier in the assembled prompt.',
    )
    is_active  = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='prompt_section_edits',
    )

    class Meta:
        ordering = ['order', 'key']
        verbose_name = 'Prompt Section'
        verbose_name_plural = 'Prompt Sections'

    def __str__(self):
        return self.label

    def save_version(self, user=None, note=''):
        """Snapshot current content as a version before overwriting."""
        if self.pk and self.content:
            PromptSectionVersion.objects.create(
                section=self,
                content=self.content,
                saved_by=user,
                note=note,
            )


class PromptSectionVersion(models.Model):
    """Immutable version history for PromptSection edits."""

    section  = models.ForeignKey(PromptSection, on_delete=models.CASCADE, related_name='versions')
    content  = models.TextField()
    saved_at = models.DateTimeField(auto_now_add=True)
    saved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note     = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-saved_at']

    def __str__(self):
        ts = self.saved_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.section.label} — {ts}"

    @property
    def truncated_content(self):
        return self.content[:300] + ' …' if len(self.content) > 300 else self.content


# ── Password reset (existing) ─────────────────────────────────────────────────

class PasswordResetToken(models.Model):
    """One-time token for custom Bundle password reset (not Django's built-in flow)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user_id} ({self.token})"

    @property
    def is_valid(self):
        if self.used:
            return False
        hours = getattr(settings, 'PASSWORD_RESET_TIMEOUT_HOURS', 24)
        return timezone.now() < self.created_at + timedelta(hours=hours)

    def mark_used(self):
        self.used = True
        self.save(update_fields=['used'])
