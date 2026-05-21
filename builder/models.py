import json
from django.conf import settings
from django.db import models


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
    final_plan = models.TextField(blank=True)
    # Chat
    chat_history = models.TextField(blank=True, default='[]')
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

    def __str__(self):
        return f"BuilderRun {self.id} — {self.display_title()}"
