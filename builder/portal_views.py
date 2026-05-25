"""
Bundle AI Control Portal — superuser-only web UI for managing prompts and agents.
All views require request.user.is_superuser — anything else → 404.
"""
import json
from datetime import timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import AgentConfig, BuilderRun, PromptSection, PromptSectionVersion
from .ai_engine import invalidate_prompt_cache


def _superuser_required(view_fn):
    """Decorator: allow only superusers; everyone else gets a 404."""
    from functools import wraps
    from django.http import Http404

    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            raise Http404
        return view_fn(request, *args, **kwargs)
    return wrapper


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@_superuser_required
def portal_dashboard(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    runs_today   = BuilderRun.objects.filter(created_at__gte=today_start).count()
    runs_week    = BuilderRun.objects.filter(created_at__gte=now - timedelta(days=7)).count()
    runs_total   = BuilderRun.objects.count()
    plans_made   = BuilderRun.objects.filter(status='plan_generated').count()
    bookings     = BuilderRun.objects.filter(status='cta_clicked').count()
    in_progress  = BuilderRun.objects.filter(status='in_progress').count()

    recent_runs = BuilderRun.objects.order_by('-created_at')[:8]
    agents      = AgentConfig.objects.all()
    prompt_count = PromptSection.objects.filter(is_active=True).count()

    # Stage distribution
    stage_dist = {}
    for run in BuilderRun.objects.values('current_stage'):
        s = run['current_stage']
        stage_dist[s] = stage_dist.get(s, 0) + 1

    return render(request, 'builder/portal/dashboard.html', {
        'runs_today':   runs_today,
        'runs_week':    runs_week,
        'runs_total':   runs_total,
        'plans_made':   plans_made,
        'bookings':     bookings,
        'in_progress':  in_progress,
        'recent_runs':  recent_runs,
        'agents':       agents,
        'prompt_count': prompt_count,
        'stage_dist':   json.dumps(stage_dist),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Sections — list
# ─────────────────────────────────────────────────────────────────────────────

@_superuser_required
def portal_prompts(request):
    agent_filter = request.GET.get('agent', '')
    sections = PromptSection.objects.select_related('agent', 'updated_by').order_by('order', 'key')
    if agent_filter == 'shared':
        sections = sections.filter(agent__isnull=True)
    elif agent_filter:
        sections = sections.filter(agent__key=agent_filter)

    agents = AgentConfig.objects.all()
    return render(request, 'builder/portal/prompts.html', {
        'sections':      sections,
        'agents':        agents,
        'agent_filter':  agent_filter,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Section — edit
# ─────────────────────────────────────────────────────────────────────────────

@_superuser_required
def portal_prompt_edit(request, key):
    section  = get_object_or_404(PromptSection, key=key)
    agents   = AgentConfig.objects.all()
    versions = section.versions.select_related('saved_by').order_by('-saved_at')[:15]

    # Revert from version
    revert_id = request.GET.get('revert')
    revert_content = None
    revert_note = ''
    if revert_id:
        try:
            v = PromptSectionVersion.objects.get(pk=revert_id, section=section)
            revert_content = v.content
            revert_note = f'Reverted to version from {v.saved_at.strftime("%d %b %Y %H:%M")}'
        except PromptSectionVersion.DoesNotExist:
            pass

    if request.method == 'POST':
        new_content = request.POST.get('content', '').strip()
        new_order   = request.POST.get('order', section.order)
        new_active  = request.POST.get('is_active') == 'on'
        new_agent_id = request.POST.get('agent') or None
        note        = request.POST.get('save_note', '').strip()

        if not new_content:
            messages.error(request, 'Content cannot be empty.')
            return redirect('portal_prompt_edit', key=key)

        # Snapshot before overwrite
        if new_content != section.content:
            section.save_version(user=request.user, note=note)

        section.content    = new_content
        section.is_active  = new_active
        section.updated_by = request.user
        try:
            section.order = int(new_order)
        except (ValueError, TypeError):
            pass
        if new_agent_id:
            try:
                section.agent = AgentConfig.objects.get(pk=new_agent_id)
            except AgentConfig.DoesNotExist:
                section.agent = None
        else:
            section.agent = None

        section.save()

        # Bust cache
        agent_key = section.agent.key if section.agent else None
        if agent_key:
            invalidate_prompt_cache(agent_key)
        else:
            invalidate_prompt_cache()

        messages.success(request, f'✅  "{section.label}" saved. Prompt cache cleared — changes are live.')
        return redirect('portal_prompts')

    return render(request, 'builder/portal/prompt_edit.html', {
        'section':        section,
        'agents':         agents,
        'versions':       versions,
        'revert_content': revert_content,
        'revert_note':    revert_note,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Agent Configs — list + inline edit
# ─────────────────────────────────────────────────────────────────────────────

@_superuser_required
def portal_agents(request):
    agents = AgentConfig.objects.prefetch_related('sections').all()
    return render(request, 'builder/portal/agents.html', {'agents': agents})


@_superuser_required
@require_POST
def portal_agent_save(request, pk):
    agent = get_object_or_404(AgentConfig, pk=pk)
    agent.model_name  = request.POST.get('model_name', agent.model_name).strip()
    agent.description = request.POST.get('description', agent.description).strip()
    agent.is_active   = request.POST.get('is_active') == 'on'
    try:
        agent.temperature = float(request.POST.get('temperature', agent.temperature))
    except (ValueError, TypeError):
        pass
    try:
        agent.max_tokens = int(request.POST.get('max_tokens', agent.max_tokens))
    except (ValueError, TypeError):
        pass
    agent.save()
    invalidate_prompt_cache(agent.key)
    messages.success(request, f'✅  Agent "{agent.label}" updated. Cache cleared.')
    return redirect('portal_agents')


# ─────────────────────────────────────────────────────────────────────────────
# Runs — list view
# ─────────────────────────────────────────────────────────────────────────────

@_superuser_required
def portal_runs(request):
    status_filter = request.GET.get('status', '')
    qs = BuilderRun.objects.select_related('user').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    runs = qs[:50]
    return render(request, 'builder/portal/runs.html', {
        'runs':          runs,
        'status_filter': status_filter,
        'status_choices': BuilderRun.STATUS_CHOICES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Prompt preview API (AJAX)
# ─────────────────────────────────────────────────────────────────────────────

@_superuser_required
def portal_prompt_preview(request, key):
    """Return the full assembled prompt for the agent this section belongs to."""
    section = get_object_or_404(PromptSection, key=key)
    from django.db.models import Q
    agent_key = section.agent.key if section.agent else 'context_collector'
    sections = (
        PromptSection.objects
        .filter(is_active=True)
        .filter(Q(agent__isnull=True) | Q(agent__key=agent_key))
        .order_by('order', 'key')
    )
    full = '\n\n' + ('─' * 60) + '\n\n'.join(
        f'[ {s.label.upper()} ]\n\n{s.content}' for s in sections
    )
    return JsonResponse({'agent_key': agent_key, 'prompt': full})
