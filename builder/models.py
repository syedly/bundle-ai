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
            return json.loads(self.ai_analysis_json) if self.ai_analysis_json else None
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
