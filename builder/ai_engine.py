import re
import logging
from openai import OpenAI
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

logger = logging.getLogger(__name__)

# ── Tag parsers ────────────────────────────────────────────────────────────────

_SUGGESTION_RE = re.compile(r'\[SUGGESTIONS:\s*(.*?)\]', re.IGNORECASE | re.DOTALL)
_DATA_RE        = re.compile(r'\[DATA:\s*(.*?)\]',        re.IGNORECASE | re.DOTALL)


def parse_suggestions(text):
    """Strip [SUGGESTIONS:...] and [DATA:...] tags, return (clean_text, suggestions_list)."""
    text = _DATA_RE.sub('', text).strip()
    match = _SUGGESTION_RE.search(text)
    if match:
        raw = match.group(1)
        suggestions = [s.strip().strip('"').strip("'") for s in raw.split('|')]
        suggestions = [s for s in suggestions if s][:4]
        clean = text[:match.start()].rstrip()
        return clean, suggestions
    return text, []


def extract_data_tag(text):
    """Extract key=value pairs from [DATA: key=value | key=value] tag."""
    match = _DATA_RE.search(text)
    if not match:
        return {}
    raw = match.group(1)
    result = {}
    for part in raw.split('|'):
        part = part.strip()
        if '=' in part:
            k, v = part.split('=', 1)
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


# ── Fixed per-question suggestion sets ────────────────────────────────────────

STAGE_SUGGESTIONS = {
    # Q1 – company intro
    'q_company': [
        "A 200-person fintech operations team",
        "A healthcare clinic's leadership team",
        "A 1,000-person SaaS engineering org",
        "A mid-size manufacturing plant",
        "A regional retail chain's store managers",
    ],
    # Q2 – company size (smart follow-up with range labels)
    'q_team_size': [
        "200 is the whole company",
        "200 to 499 total",
        "500 to 999 total",
        "1,000 to 2,999 total",
        "3,000 or more",
    ],
    # Q3 – who is this training for
    'q_focus': [
        "One specific person",
        "A small group with shared gaps",
        "The whole operations team",
        "A cross-functional cohort",
    ],
    # Q4 – role and seniority
    'q_role': [
        "A mid-level manager stepping up",
        "A senior IC moving into leadership",
        "A new VP coming from director level",
        "A team lead with informal authority",
        "A director managing other managers",
    ],
    # Q5 – training goal
    'q_goal': [
        "Strengthen their executive presence",
        "Help them lead through other managers more effectively",
        "Build their strategic thinking",
        "Improve how they give feedback to their managers",
        "Prepare them for a VP-level role",
    ],
    # Q6 – specific challenges
    'q_challenges': [
        "Struggles to command the room with senior leadership",
        "Comes across as too tactical, not strategic enough",
        "Has trouble influencing without authority",
        "Gets lost in the weeds instead of setting direction",
    ],
    # Q7 – what are you hearing / observing
    'q_daytoday': [
        "Gets pulled into the weeds in leadership meetings",
        "Struggles to influence peers and senior stakeholders",
        "Talks about tasks, not outcomes or vision",
        "Avoids taking a strong stance on ambiguous decisions",
    ],
    # Q8 – what data is available
    'q_data': [
        "I can share performance reviews or feedback data",
        "I have job descriptions I can paste or upload",
        "I have a competency framework or learning brief",
        "Nothing structured — let's just talk it through",
    ],
    # Stage 2 – after file upload prompt
    'q_data_upload': [
        "I'll paste the review now",
        "I'll use the upload button",
        "Let me describe the key findings",
    ],
    # Stage 2 – after each document: more to add?
    'q_more_docs': [
        "Add another document",
        "That's everyone — let's continue",
        "Just this one person",
    ],
    # Stage 2 – JD paste prompt
    'q_data_jd': [
        "I'll paste the job description now",
        "I have multiple roles to add",
        "Let me describe the roles instead",
        "Nothing structured — let's just talk it through",
    ],
    # Stage 2 – AI document summary confirmation (after upload analysis)
    'q_confirm_data': [
        "Yes, that's accurate",
        "Mostly right — let me clarify one thing",
        "Add one more detail",
        "Not quite — here's the correction",
    ],
    # Q9 – strengths (beyond what's in the review)
    'q_strengths': [
        "Strong client and borrower relationships",
        "Deep technical knowledge of the portfolio",
        "Willing to take on stretch assignments",
        "Good at developing junior team members",
    ],
    # Q10 – company values / competencies (NEW)
    'q_values': [
        "Yes, I'll paste them",
        "We have a competency framework",
        "Not formalized — just feel of the place",
        "Skip — keep it generic",
    ],
    # Q11 – timeline
    'q_timeline': [
        "Within the next 30 days",
        "Next quarter",
        "Next 6 months",
        "No specific timeline",
    ],
    # Q12 – constraints / off-limits
    'q_constraints': [
        "No exclusions — open to anything",
        "Avoid anything overly academic",
        "We've already done communication training",
        "Avoid time-management-focused sessions",
    ],
    # Q13 – summary confirmation + generate (replaces old Q14)
    'q_ready': [
        "Go ahead, generate the recommendation",
        "Actually, change the timeline",
        "Actually, add more context on his role",
        "Actually, adjust the training goals",
    ],
    # Diagnostic questions (Path C – no data)
    'q_diag_challenge': [
        "Communication and alignment gaps",
        "Leadership and management gaps",
        "Execution and accountability issues",
        "Low morale and engagement",
    ],
    'q_diag_friction': [
        "Communication breakdowns",
        "Execution and follow-through",
        "Leadership inconsistency",
        "Low team morale",
    ],
    'q_diag_feedback': [
        "Yes, very confident",
        "Somewhat — it varies by manager",
        "Not really — they tend to avoid it",
    ],
    'q_diag_conflict': [
        "We address it directly",
        "It tends to get avoided",
        "It escalates and becomes a problem",
        "Inconsistent — depends on the manager",
    ],
    'q_diag_change': [
        "They adapt quickly",
        "It's a real struggle for most",
        "Depends on the person",
    ],
    'q_diag_ownership': [
        "Strong — people own their work",
        "Mixed — some do, some don't",
        "Most people wait for direction",
    ],
    'q_diag_collab': [
        "Very well — strong cross-functional culture",
        "Okay within teams, but silos exist",
        "Collaboration is a real problem",
    ],
    'q_diag_success': [
        "Better leadership at every level",
        "Measurably lower turnover",
        "Stronger communication and trust",
        "Improved accountability and performance",
    ],
    # Stage 4 – delivery method
    'q_scenario': [
        "1:1 Training + Coaching",
        "1:1 Training Only",
        "Coaching Only",
    ],
    # Stage 4b – session count
    'q_sessions': [
        "Start Here — 4 sessions",
        "Build Momentum — 6 sessions",
        "Full Impact — 8 sessions",
    ],
    # Stage 4 – budget depth
    'q_budget': [
        "Start small — 4 sessions to test",
        "A structured program — 6 sessions",
        "Full programme — 8 sessions",
    ],
    # Stage 6 – booking
    'q_book': [
        "Yes, let's talk",
        "Open the plan first",
        "I'll review and come back",
    ],
    # Kept for legacy / resume compatibility
    'q_success': [
        "They run leadership meetings confidently",
        "Measurable improvement in 360 feedback",
        "Fewer escalations to me",
        "Their team performs more independently",
    ],
}


def detect_question_type(ai_message):
    """
    Detect which question the AI just asked and return the matching suggestion key.
    Order: most-specific first, broadest last. Returns None for transitional messages.
    """
    msg = ai_message.lower()

    # ── Delivery / scenario ───────────────────────────────────────────────────
    if all(p in msg for p in ['scenario a', 'scenario b', 'scenario c']):
        return 'q_scenario'
    if any(p in msg for p in [
        '1:1 training + coaching', 'training + coaching', 'training only', 'coaching only',
        'delivery method', 'delivery option', 'which pathway', 'which delivery',
        'which of these feels right', 'which option feels right',
    ]):
        return 'q_scenario'

    # ── Session count ─────────────────────────────────────────────────────────
    if any(p in msg for p in [
        'how many sessions', 'number of sessions', 'session count',
        'many sessions are you', 'how many session', 'how big a program',
        'how big of a program', 'how large a program',
    ]):
        return 'q_sessions'

    # ── Budget depth ──────────────────────────────────────────────────────────
    if any(p in msg for p in ['budget', 'investment', 'training spend']) and \
       any(p in msg for p in ['start here', 'build momentum', 'full impact',
                               'start small', 'structured program', 'full programme']):
        return 'q_budget'

    # ── Booking CTA ───────────────────────────────────────────────────────────
    if any(p in msg for p in [
        'book a', 'schedule a', 'consultation call', '30-minute',
        'talk to a bundle', 'book a call', 'get you scheduled',
        'download this plan', 'download as a pdf', 'set up a quick call',
        'quick call with a bundle',
    ]):
        return 'q_book'

    # ── Q13 Summary confirmation / ready to generate ──────────────────────────
    # These patterns ONLY appear in the AI's Q13 recap message, not in the opening line.
    # Keep patterns specific to avoid false-positives against the greeting/opening.
    if any(p in msg for p in [
        "so we're looking at", "so we are looking at",
        "here's what i've got", "here's what we have",
        "to summarise", "to summarize",
        "ready to generate your", "ready to move forward",
        "shall i go ahead", "go ahead and generate",
        "before i put your recommendation",
        "before i generate your", "before i generate the",
        "we'll build around what's left", "we've got everything",
        "i have everything i need",
        "ready to generate?", "shall i put together your",
    ]):
        return 'q_ready'

    # ── Q2 Company size (smart follow-up) ─────────────────────────────────────
    if any(p in msg for p in [
        'how big is the company overall', 'is that the whole org',
        'just the operations', 'just the team', 'whole org, or',
        'whole company, or', 'just the', 'whole org',
        'how big is the company', 'company size', 'how many people overall',
        'overall headcount', 'how large is the company', 'company overall',
        'rough number', 'rough is fine',
    ]):
        return 'q_team_size'

    # ── AI document summary confirmation (after upload) ───────────────────────
    if any(p in msg for p in [
        "that right?", "is that right?", "does that sound right",
        "that accurate?", "is that accurate", "sound about right",
        "have i got that right", "is that a fair summary",
        "looks like this is", "looks like we have",
    ]):
        return 'q_confirm_data'

    # ── More documents to upload? ─────────────────────────────────────────────
    if any(p in msg for p in [
        'do you have another', 'any more documents', 'another document to add',
        'more to add', 'add another', "that's everyone", 'anyone else',
        'shall we move on', 'more files', 'more documents',
    ]):
        return 'q_more_docs'

    # ── Data upload request (path A) ──────────────────────────────────────────
    if any(p in msg for p in [
        'paste or upload', 'paste the data', 'paste your data', 'paste your performance',
        'upload your data', 'upload your performance', 'upload button',
        'paste it directly', 'share your performance', 'share the data',
        'go ahead and paste', 'can you paste', 'please paste', 'feel free to paste',
        'drop the file', 'drop a file', 'paperclip',
        'pdf, csv', 'pdf, csv, or excel', 'pdf, csv, excel',
    ]):
        return 'q_data_upload'

    # ── JD request (path B) ──────────────────────────────────────────────────
    if any(p in msg for p in [
        'paste your job', 'paste the job', 'paste one or more job',
        'paste the jd', 'share the jd', 'paste a job',
        'job descriptions for', 'roles you want to train',
    ]):
        return 'q_data_jd'

    # ── Q12 Constraints / off-limits ─────────────────────────────────────────
    if any(p in msg for p in [
        "off the table", "wouldn't land", "topics or approaches",
        "anything we should avoid", "any topics to avoid", "off limits",
        "already covered", "not a good fit", "wouldn't land for",
        "anything that", "approaches that wouldn't",
    ]):
        return 'q_constraints'

    # ── Q10 Company values / competencies ────────────────────────────────────
    if any(p in msg for p in [
        'company values', 'mission language', 'competency framework',
        'competencies', 'build this around', 'values, competencies',
        'core values', 'any values', 'any mission', 'organisational values',
        'organizational values', 'learning brief',
    ]):
        return 'q_values'

    # ── Legacy success metrics (kept for resume) ──────────────────────────────
    if any(p in msg for p in [
        'how would you know this worked', 'how will you know', 'define success',
        'what changes for you', 'what would success look like for this person',
        'what would tell you', 'measure success', 'what does good look like',
    ]):
        return 'q_success'

    # ── Q9 Strengths / beyond the review ─────────────────────────────────────
    if any(p in msg for p in [
        'what does this person do well', 'what are their strengths',
        "build on rather than replace", 'already doing well',
        'what should we build on', "what's working", 'what are they good at',
        'beyond what', "beyond the review", "beyond what's in",
        'existing strengths', 'talent they already have',
    ]):
        return 'q_strengths'

    # ── Q7 What are you hearing / observing ──────────────────────────────────
    if any(p in msg for p in [
        'what are you hearing', 'hearing from others', 'observing directly',
        'specific moments', 'shows up', 'where this shows up',
        'day to day', 'day-to-day', 'showing up in',
        'see it in meetings', 'written updates', 'where is this showing',
        'where do you see this', 'what are you noticing', 'see this play out',
    ]):
        return 'q_daytoday'

    # ── Q6 Specific challenges ────────────────────────────────────────────────
    if any(p in msg for p in [
        'challenges are they facing', 'challenges are they running into',
        'running into right now', 'what challenges', 'specific challenge',
        'challenges right now', 'what are they struggling with',
        'what problems are they', 'be as specific', 'be specific if you can',
    ]):
        return 'q_challenges'

    # ── Q4 Role and seniority ─────────────────────────────────────────────────
    if any(p in msg for p in [
        'what role are they in', 'seniority ladder', 'seniority level',
        'their role', 'what is their role', "what's their role",
        'where are they on the', 'level are they', 'their position',
        'their title', 'job title', 'role and seniority',
    ]):
        return 'q_role'

    # ── Diagnostic questions (Path C) ─────────────────────────────────────────
    if any(p in msg for p in [
        'biggest challenge', "team's biggest challenge", 'main challenge',
        'biggest challenge your team', 'team is facing right now',
        'team facing right now',
    ]):
        return 'q_diag_challenge'

    if any(p in msg for p in [
        'most friction', 'where is the friction', 'where do you see the most',
        'communication, execution', 'execution, leadership', 'leadership, or morale',
    ]):
        return 'q_diag_friction'

    if any(p in msg for p in [
        'confident giving', 'giving direct feedback',
        'managers confident', 'comfortable giving feedback',
        'give direct feedback', 'performance falls short',
    ]):
        return 'q_diag_feedback'

    if any(p in msg for p in [
        'handle conflict', 'how is conflict', 'when conflict',
        'conflict on the team', 'conflict come up', 'conflict typically',
        'conflict gets handled', 'deal with conflict',
    ]):
        return 'q_diag_conflict'

    if any(p in msg for p in [
        'priorities shift', 'when priorities', 'adapt quickly',
        'struggle with change', 'unexpected changes', 'shifting priorities',
        'adapt quickly or struggle',
    ]):
        return 'q_diag_change'

    if any(p in msg for p in [
        'take ownership', 'do people take', 'own their work',
        'wait for direction', 'take responsibility', 'people on this team generally',
        'tend to wait', 'ownership of outcomes',
    ]):
        return 'q_diag_ownership'

    if any(p in msg for p in [
        'collaborate across', 'across functions', 'across departments',
        'across teams', 'collaborate with other',
        'how well does this team collaborate', 'between departments',
    ]):
        return 'q_diag_collab'

    if any(p in msg for p in [
        'success look like', 'what does success', '6 months from now',
        'six months from now', 'look like in 6', 'look like for this team',
    ]):
        return 'q_diag_success'

    # ── Q8 Data availability ──────────────────────────────────────────────────
    if any(p in msg for p in [
        'performance data', 'performance review', 'review data', 'employee data',
        'any data', 'data available', 'data you can share',
        'do you have data', 'data to share', 'what can you share',
        'what do you have', 'i can work with', 'whatever you have',
    ]):
        return 'q_data'

    # ── Q11 Timeline ──────────────────────────────────────────────────────────
    if any(p in msg for p in [
        'when do you want this to start', 'when do you want',
        'when do you need', 'any deadlines', 'deadline',
        'timeline', 'time frame', 'timeframe', 'start date',
        'kicking off', 'when to start', 'when do you hope',
    ]):
        return 'q_timeline'

    # ── Q3 Who is training for ────────────────────────────────────────────────
    if any(p in msg for p in [
        "who's this training for", "who is this training for", "who is the training for",
        "who are we training", "training for one person", "one person or",
        "individual or a team", "this for an individual",
    ]):
        return 'q_focus'

    # ── Q5 Training goal ──────────────────────────────────────────────────────
    if any(p in msg for p in [
        'accomplish for this person', 'hoping the training will accomplish',
        'training will accomplish', 'training goal', 'hoping to achieve',
        'what are you hoping', 'what would you like to achieve', 'goal for this',
        'what are you trying to', 'objective for this', 'what outcome',
        'hoping this will do', 'want the training to',
    ]):
        return 'q_goal'

    # ── Q1 Company intro (broadest — check last) ──────────────────────────────
    if any(p in msg for p in [
        'what company', 'company is this for', 'company name', 'which company',
        'your company', 'what does your team do', 'roughly what does',
        'tell me about your company', 'what industry', 'your industry',
        'how many employees', 'name of your company', 'to start:',
    ]):
        return 'q_company'

    return None


# ── Context builders ───────────────────────────────────────────────────────────

def build_taxonomy_context():
    from .models import PrimarySkill
    lines = ["=== BUNDLE HUMAN-CENTERED SKILLS TAXONOMY ===\n"]
    for skill in PrimarySkill.objects.prefetch_related('sub_skills').all():
        lines.append(f"PRIMARY SKILL: {skill.name}")
        lines.append(f"  Definition: {skill.definition}")
        subs = skill.sub_skills.all()
        if subs:
            sub_parts = []
            for s in subs:
                if s.definition:
                    sub_parts.append(f"{s.name} ({s.definition})")
                else:
                    sub_parts.append(s.name)
            lines.append(f"  Sub-skills: {' | '.join(sub_parts)}")
        lines.append("")
    return "\n".join(lines)


def build_sessions_context():
    from .models import Session
    lines = ["=== BUNDLE SESSION CATALOG (34 sessions — only recommend from this list) ===\n"]
    for s in Session.objects.all().order_by('session_number'):
        lines.append(f"SESSION {s.session_number}: {s.title}")
        lines.append(f"  Primary Skills: {s.primary_skills_text}")
        if s.sub_skills_text:
            lines.append(f"  Sub-skills: {s.sub_skills_text}")
        lines.append(f"  Applicable Roles: {s.role_applicability}")
        lines.append(f"  Manager Only: {'YES — never recommend to ICs' if s.is_manager_only else 'No'}")
        lines.append("")
    return "\n".join(lines)


def build_pathways_context():
    from .models import Pathway
    lines = ["=== BUNDLE OFFICIAL PATHWAYS ===\n"]
    for p in Pathway.objects.all():
        lines.append(f"PATHWAY: {p.name} (Role: {p.role})")
        lines.append(f"  Description: {p.description}")
        for i, s in enumerate(p.get_session_list(), 1):
            lines.append(f"  {i}. {s}")
        lines.append("")
    return "\n".join(lines)


# ── Prompt assembly — DB-backed with cache ────────────────────────────────────

_PROMPT_CACHE_TTL = 300  # 5 minutes


def _get_agent_key(run) -> str:
    """Route to the correct agent based on run stage."""
    if run.current_stage <= 2:
        return 'context_collector'
    if run.current_stage in (3, 4):
        return 'analyzer'
    if run.current_stage == 5 and not run.final_plan_json:
        return 'plan_generator'
    return 'general'


def _load_prompt_sections(agent_key: str) -> list[str]:
    """
    Load assembled prompt sections from cache (or DB).
    Returns ordered list of section content strings.
    Shared sections (agent=None) + agent-specific sections, sorted by order.
    """
    cache_key = f'bundle_prompt_sections__{agent_key}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from .models import PromptSection
        sections = (
            PromptSection.objects
            .filter(is_active=True)
            .filter(Q(agent__isnull=True) | Q(agent__key=agent_key))
            .order_by('order', 'key')
            .values_list('content', flat=True)
        )
        result = list(sections)
    except Exception:
        result = []

    cache.set(cache_key, result, _PROMPT_CACHE_TTL)
    return result


def _get_agent_params(agent_key: str) -> dict:
    """Load model/temperature/max_tokens for an agent from DB (with cache)."""
    cache_key = f'bundle_agent_params__{agent_key}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    defaults = {'model': settings.OPENAI_MODEL, 'temperature': 0.7, 'max_tokens': 8000}
    try:
        from .models import AgentConfig
        agent = AgentConfig.objects.get(key=agent_key, is_active=True)
        result = {
            'model':       agent.model_name or settings.OPENAI_MODEL,
            'temperature': agent.temperature,
            'max_tokens':  agent.max_tokens,
        }
    except Exception:
        result = defaults

    cache.set(cache_key, result, _PROMPT_CACHE_TTL)
    return result


def invalidate_prompt_cache(agent_key: str = None):
    """
    Invalidate cached prompts. Called by admin after a PromptSection is saved.
    Pass agent_key to clear only one agent, or None to clear all.
    """
    keys_to_clear = (
        [agent_key] if agent_key
        else ['context_collector', 'analyzer', 'plan_generator', 'general']
    )
    for k in keys_to_clear:
        cache.delete(f'bundle_prompt_sections__{k}')
        cache.delete(f'bundle_agent_params__{k}')


def _build_run_state_block(run) -> str:
    """Dynamic run state injected at the top of every prompt (not stored in DB)."""
    return (
        "CURRENT RUN STATE:\n"
        f"- Company: {run.company_name or 'Not yet collected'}\n"
        f"- Industry: {run.industry or 'Not yet collected'}\n"
        f"- Team Size: {run.team_size or 'Not yet collected'}\n"
        f"- Role Title: {run.role_title or 'Not yet collected'}\n"
        f"- Seniority Level: {run.seniority_level or 'Not yet collected'}\n"
        f"- Training Goal: {run.training_goal or 'Not yet collected'}\n"
        f"- Observed Challenges: {run.observed_challenges or 'Not yet collected'}\n"
        f"- Success Metrics: {run.success_metrics or 'Not yet collected'}\n"
        f"- Training Constraints: {run.training_constraints or 'Not yet collected'}\n"
        f"- Focus Type: {run.focus_type or 'Not yet collected'}\n"
        f"- Has Performance Data: {run.has_performance_data or 'Not yet collected'}\n"
        f"- Budget Tier: {run.budget_tier or 'Not yet collected'}\n"
        f"- Timeline: {run.timeline or 'Not yet collected'}\n"
        f"- Entry Point: {run.entry_point or 'Not yet determined'}\n"
        f"- Current Stage: {run.current_stage}"
    )


def build_system_prompt(run, agent_key: str = None) -> str:
    """
    Assemble the system prompt for the given agent from DB-stored sections.
    Order: identity → run state → taxonomy/sessions/pathways → agent sections → shared sections.
    Falls back to the static emergency prompt if DB is unavailable.
    """
    if agent_key is None:
        agent_key = _get_agent_key(run)

    taxonomy  = build_taxonomy_context()
    sessions  = build_sessions_context()
    pathways  = build_pathways_context()

    db_sections = _load_prompt_sections(agent_key)

    if not db_sections:
        # DB unavailable — fall back to emergency inline prompt so the app never breaks
        logger.warning("No prompt sections found in DB for agent '%s' — using fallback.", agent_key)
        db_sections = [_FALLBACK_PROMPT]

    parts = [
        _build_run_state_block(run),
        taxonomy,
        sessions,
        pathways,
        *db_sections,
    ]
    return '\n\n'.join(p for p in parts if p and p.strip())


# ── Session refine — called by the "Refine with AI" button on the plan page ───

def refine_session_with_ai(run, emp_idx: int, sess_num: int, change_request: str) -> dict:
    """
    Given a user's change request for one session in the final plan, call the AI
    to propose a replacement or modification. Returns a fully populated session dict.
    """
    import json as _json

    plan_data = run.get_final_plan_data()
    if not plan_data:
        raise ValueError("No final plan data found.")

    employees = plan_data.get('employees', [])
    if emp_idx < 0 or emp_idx >= len(employees):
        raise ValueError(f"Employee index {emp_idx} is out of range.")

    emp = employees[emp_idx]
    sessions = emp.get('sessions', [])
    current_session = next((s for s in sessions if s.get('number') == sess_num), None)
    if not current_session:
        raise ValueError(f"Session number {sess_num} not found.")

    # Names of other sessions already in the plan (so AI doesn't suggest a duplicate)
    other_titles = [s.get('title', '') for s in sessions if s.get('number') != sess_num]

    sessions_catalog = build_sessions_context()
    taxonomy = build_taxonomy_context()

    emp_context = (
        f"Employee: {emp.get('name', 'Unknown')}\n"
        f"Role: {emp.get('role_context', '')}\n"
        f"Strengths: {', '.join(emp.get('strengths', []))}\n"
        f"Growth opportunities: {', '.join(emp.get('growth_opportunities', []))}\n"
        f"Career direction: {emp.get('career_direction', '')}"
    )

    # Include uploaded performance data so the AI can quote from it
    performance_context = ""
    if run.uploaded_data:
        performance_context = (
            f"\nPERFORMANCE DATA (source for quotes):\n"
            f"{run.uploaded_data[:4000]}\n"
        )

    system_prompt = (
        "You are the Bundle AI Training Builder. "
        "A user wants to modify one session in an existing training plan. "
        "You must propose a replacement or updated session using ONLY sessions from Bundle's catalog.\n\n"
        f"{taxonomy}\n\n"
        f"{sessions_catalog}\n\n"
        "=== CRITICAL RULES ===\n"
        "1. ONLY use sessions from the catalog above. Never invent sessions.\n"
        "2. If sess_num == 1, the replacement MUST still be a relational opener "
        "(Effective Communication, Elevate Emotional Intelligence, Empathy and Compassion at Work, "
        "Building Strong Team Dynamics, Coaching and Feedback, or Foster Collaboration).\n"
        f"3. Do NOT suggest sessions already in this plan: {', '.join(other_titles)}.\n"
        "4. Return ONLY a valid JSON object — no markdown, no explanation, no code blocks.\n\n"
        "Return exactly this JSON shape:\n"
        "{\n"
        f'  "number": {sess_num},\n'
        '  "title": "Exact session title from catalog",\n'
        '  "skill_categories": ["Category 1"],\n'
        '  "skill_focus": ["Sub-skill 1", "Sub-skill 2", "Sub-skill 3"],\n'
        '  "what_it_covers": "1 sentence, max 15 words",\n'
        '  "recommended_because": "The review states that... (direct quote from data)",\n'
        '  "why_this_session": "3-5 sentences: why this replacement fits, what gap it closes, what it unlocks"\n'
        "}"
    )

    user_prompt = (
        f"EMPLOYEE CONTEXT:\n{emp_context}\n"
        f"{performance_context}\n"
        f"CURRENT SESSION BEING MODIFIED:\n{_json.dumps(current_session, indent=2)}\n\n"
        f"CHANGE REQUEST FROM USER:\n\"{change_request}\"\n\n"
        "Based on the change request, propose the best replacement or modification. "
        "If they want to swap, find the best alternative from the catalog. "
        "If they want to refocus, update the descriptions while keeping the session if appropriate. "
        "Return ONLY the JSON object."
    )

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.4,
        max_tokens=1200,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if the model wraps the JSON
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)

    result = _json.loads(raw)
    # Always enforce the correct session number
    result['number'] = sess_num
    return result


# ── Emergency fallback (used only if DB has no sections seeded) ───────────────
_FALLBACK_PROMPT = (
    "You are the Bundle AI Training Builder — a warm, expert training advisor. "
    "Guide the user through a structured conversation about their training needs. "
    "Ask ONE question at a time. Always end every message with [SUGGESTIONS: ...] and [DATA: ...]."
)


# ── Stage + data detection ─────────────────────────────────────────────────────

def save_data_from_tag(run, user_msg, ai_reply):
    """Parse [DATA:] tag from AI reply and persist extracted fields to the run."""
    data = extract_data_tag(ai_reply)
    if not data:
        return

    if 'company_name' in data and data['company_name']:
        run.company_name = data['company_name']
        if not run.title:
            run.title = data['company_name']
    if 'industry' in data:
        run.industry = data['industry']
    if 'team_size' in data:
        run.team_size = data['team_size']
    if 'training_goal' in data:
        run.training_goal = data['training_goal']
    if 'focus_type' in data:
        run.focus_type = data['focus_type']
    if 'target_type' in data:
        run.target_type = data['target_type']
    if 'has_performance_data' in data:
        run.has_performance_data = data['has_performance_data']
    if 'entry_point' in data:
        ep = data['entry_point'].lower()
        if ep in ('performance_data', 'jd_based', 'diagnostic'):
            run.entry_point = ep
    if 'budget_tier' in data:
        raw = data['budget_tier'].lower().replace(' ', '_')
        if raw in ('start_here', 'build_momentum', 'full_impact'):
            run.budget_tier = raw
        elif 'start' in raw:
            run.budget_tier = 'start_here'
        elif 'momentum' in raw or 'build' in raw:
            run.budget_tier = 'build_momentum'
        elif 'full' in raw or 'impact' in raw:
            run.budget_tier = 'full_impact'
    if 'timeline' in data:
        run.timeline = data['timeline']
    if 'selected_scenario' in data:
        run.selected_scenario = data['selected_scenario'].upper()[:1]
    if 'num_sessions' in data:
        try:
            run.num_sessions = int(re.sub(r'\D', '', str(data['num_sessions'])))
        except (ValueError, AttributeError):
            pass
    # New learner-profile fields
    if 'role_title' in data and data['role_title']:
        run.role_title = data['role_title']
    if 'seniority_level' in data and data['seniority_level']:
        run.seniority_level = data['seniority_level']
    if 'observed_challenges' in data and data['observed_challenges']:
        run.observed_challenges = data['observed_challenges']
    if 'success_metrics' in data and data['success_metrics']:
        run.success_metrics = data['success_metrics']
    if 'training_constraints' in data and data['training_constraints']:
        run.training_constraints = data['training_constraints']


def detect_and_update_stage(run, user_msg, ai_reply):
    """Update run stage and status based on message content."""
    ai_lower = ai_reply.lower()
    user_lower = user_msg.lower()

    # Stage 4: recommendation with 3 scenarios
    if all(p in ai_lower for p in ['scenario a', 'scenario b', 'scenario c']):
        run.current_stage = 4
        run.status = 'recommendation_ready'

    # Stage 5: full plan with session tables
    plan_signal = (
        ('| 1 |' in ai_reply and 'why this session' in ai_lower) or
        ('| # |' in ai_reply and 'skill focus' in ai_lower) or
        ('coaching support' in ai_lower and '| 1 |' in ai_reply) or
        ('sequencing' in ai_lower and '| 1 |' in ai_reply) or
        ('growth opportunities' in ai_lower and '| 1 |' in ai_reply)
    )
    if plan_signal:
        run.current_stage = 5
        run.status = 'plan_generated'
        run.final_plan = ai_reply

    # Stage 6: booking prompt
    if any(p in ai_lower for p in ['fill out the booking', 'booking form below', 'get you scheduled']):
        run.current_stage = 6

    if any(p in user_lower for p in ["yes, let's book", "book a call", "let's book", "yes, book"]):
        run.current_stage = 6

    # Fallback budget tier extraction from user message
    if not run.budget_tier:
        if 'start here' in user_lower:
            run.budget_tier = 'start_here'
        elif 'build momentum' in user_lower:
            run.budget_tier = 'build_momentum'
        elif 'full impact' in user_lower:
            run.budget_tier = 'full_impact'

    # Fallback entry point from user message
    if not run.entry_point:
        if any(w in user_lower for w in ['performance data', 'performance review', 'i have data', 'yes, i have']):
            run.entry_point = 'performance_data'
        elif any(w in user_lower for w in ['job description', ' jd ', 'job desc']):
            run.entry_point = 'jd_based'
        elif any(w in user_lower for w in ['no data', 'just a goal', 'no performance']):
            run.entry_point = 'diagnostic'

    # Fallback target type from user message
    if not run.target_type:
        if any(w in user_lower for w in ['individual', 'one person', 'specific person']):
            run.target_type = 'individual'
            run.focus_type  = 'individual'
        elif any(w in user_lower for w in ['cohort', 'group', 'team', 'whole']):
            run.target_type = 'cohort'
            run.focus_type  = 'cohort'

    # Thread title
    if run.company_name and not run.title:
        run.title = run.company_name


# ── Fallback suggestion generator ─────────────────────────────────────────────

def is_transitional_message(ai_message):
    """Return True when the AI is acknowledging input and preparing the next output."""
    msg_lower = ai_message.lower()
    transitional_phrases = [
        'please hold on', 'hold on', "i'll analyze", "i'll map",
        "i'll now", "i'll create", "i'll prepare", 'let me analyze',
        'let me map', 'let me review', 'let me prepare', 'analyzing your',
        'mapping your', 'prepare the plan', 'prepare a plan', 'preparing the plan',
        'create a tailored', 'create the plan', 'give me a moment',
        'just a moment', 'one moment', 'processing', 'please wait',
    ]
    return any(phrase in msg_lower for phrase in transitional_phrases)


def get_suggestions_for_message(ai_message):
    """Suggestion chips for a given assistant message (e.g. when resuming a thread)."""
    if not ai_message or is_transitional_message(ai_message):
        return []
    msg_lower = ai_message.lower()
    if re.search(r'how many sessions|number of sessions', msg_lower):
        return []
    q_type = detect_question_type(ai_message)
    if q_type and q_type in STAGE_SUGGESTIONS:
        return STAGE_SUGGESTIONS[q_type]
    return generate_fallback_suggestions(ai_message)


def generate_fallback_suggestions(ai_message):
    """
    Generates 3-4 short (2-4 word) suggestions that actually match what the AI just said.
    For transitional/loading messages, returns instant acknowledgement replies.
    For everything else, makes a fast dedicated AI call.
    """
    # Transitional messages — no AI call needed, return instant acknowledgements
    if is_transitional_message(ai_message):
        return ["Take your time", "Sounds good", "I'm ready", "Go ahead"]

    # For all other messages: generate fresh contextual suggestions via a small AI call
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        snippet = ai_message[:600].strip()
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate ultra-short suggested replies for a training advisor chat UI. "
                        "Output ONLY a pipe-separated list — no labels, no numbering, no extra text. "
                        "Each reply must be 2-4 words maximum. "
                        "Replies must directly answer or react to what was just said. "
                        "NEVER repeat or copy examples from earlier in a conversation. "
                        "Example format: Sounds right | Not sure yet | Tell me more | Maybe later"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"The AI training advisor just said:\n\n\"{snippet}\"\n\n"
                        "Give 3 or 4 short replies a user might click. "
                        "Each reply must be 2-4 words and directly relevant to THIS specific message. "
                        "Pipe-separated only, nothing else."
                    ),
                },
            ],
            max_tokens=60,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip()
        suggestions = [s.strip().strip('"').strip("'") for s in raw.split('|')]
        suggestions = [s for s in suggestions if 2 <= len(s.split()) <= 4][:4]
        if len(suggestions) >= 3:
            return suggestions
    except Exception:
        pass

    # API call failed — return safe generic replies so something always shows
    return ["Sounds good", "Tell me more", "What's next?", "Got it"]


# ── Greeting ───────────────────────────────────────────────────────────────────

def generate_greeting(run):
    """Returns (greeting_text, suggestions_list)."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    # Greetings always come from the context_collector agent
    agent_params = _get_agent_params('context_collector')
    response = client.chat.completions.create(
        model=agent_params.get('model', settings.OPENAI_MODEL),
        messages=[
            {"role": "system", "content": build_system_prompt(run, 'context_collector')},
            {"role": "user", "content": "Hello, I want to build a training plan for my team."},
        ],
        max_tokens=500,
        temperature=agent_params.get('temperature', 0.7),
    )
    raw = response.choices[0].message.content

    ai_reply, ai_suggestions = parse_suggestions(raw)

    # The greeting ALWAYS ends with Q1 ("what company is this for?")
    # — hard-lock to q_company suggestions, never rely on detect_question_type
    # which could false-positive on phrases in the opening paragraph.
    suggestions = STAGE_SUGGESTIONS['q_company']

    history = [{"role": "assistant", "content": ai_reply}]
    run.set_chat_history(history)
    run.save()
    return ai_reply, suggestions


# ── Main chat ──────────────────────────────────────────────────────────────────

def _resolve_suggestions(run, ai_reply):
    if is_transitional_message(ai_reply):
        return generate_fallback_suggestions(ai_reply)
    # Plan generated (both reports ready) → always show booking options
    if run.status == 'plan_generated':
        return STAGE_SUGGESTIONS.get('q_book', [
            "Yes, let's talk", 'Open the plan first', "I'll review and come back",
        ])
    # recommendation_ready without a plan yet — still booking options
    # (the AI should auto-generate the plan next, so never show pathway-picker chips)
    if run.status == 'recommendation_ready':
        return STAGE_SUGGESTIONS.get('q_book', [
            "Yes, let's talk", 'Open the plan first', "I'll review and come back",
        ])
    q_type = detect_question_type(ai_reply)
    if q_type and q_type in STAGE_SUGGESTIONS:
        return STAGE_SUGGESTIONS[q_type]
    return generate_fallback_suggestions(ai_reply)


def _plan_has_sessions(run) -> bool:
    """Return True only when every employee block has at least one session row."""
    try:
        plan = run.get_final_plan_data()
        if not plan:
            return False
        employees = plan.get('employees') or []
        if not employees:
            return False
        return all(len(e.get('sessions') or []) > 0 for e in employees)
    except Exception:
        return False


def _auto_generate_plan(run, client):
    """
    Separate API call using plan_generator (16k tokens + full stage_5 prompts).
    Forces submit_final_plan via tool_choice so the plan is always generated.
    Called when ai_analysis_json is ready but sessions are missing/empty.
    """
    from .ai_tools import SUBMIT_FINAL_PLAN_TOOL, handle_tool_call

    agent_params = _get_agent_params('plan_generator')
    model       = agent_params.get('model', settings.OPENAI_MODEL)
    max_tokens  = agent_params.get('max_tokens', 16000)
    temperature = agent_params.get('temperature', 0.65)

    system = build_system_prompt(run, 'plan_generator')
    history = run.get_chat_history()
    api_messages = [{'role': 'system', 'content': system}, *history[-20:]]

    # Internal trigger — not shown in the user-facing chat
    api_messages.append({
        'role': 'user',
        'content': (
            'The AI analysis is complete. '
            'Call submit_final_plan now to generate the full, session-by-session training plan. '
            'Use the delivery method and session count already decided in the analysis. '
            'Write every employee block in full — no shortcuts, no truncation.'
        ),
    })

    last_chat_msg = ''
    for _attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                tools=[SUBMIT_FINAL_PLAN_TOOL],
                tool_choice={'type': 'function', 'function': {'name': 'submit_final_plan'}},
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            logger.error(f'Plan generator API call failed: {e}', exc_info=True)
            break

        msg = response.choices[0].message

        if msg.tool_calls:
            api_messages.append({
                'role': 'assistant',
                'content': msg.content or '',
                'tool_calls': [
                    {
                        'id': tc.id,
                        'type': 'function',
                        'function': {
                            'name': tc.function.name,
                            'arguments': tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                try:
                    result, chat_msg, _ = handle_tool_call(run, tc)
                    last_chat_msg = chat_msg
                    api_messages.append({
                        'role': 'tool',
                        'tool_call_id': tc.id,
                        'content': result,
                    })
                except Exception as e:
                    logger.error(f'Plan generator tool call error: {e}', exc_info=True)
            if _plan_has_sessions(run):
                break
            continue

        # Non-tool response — done
        break

    return last_chat_msg


def chat_with_ai(run, user_message):
    """Returns (ai_reply, suggestions_list). Uses tool calls for Stage 4/5 deliverables."""
    from .ai_tools import BUNDLE_TOOLS, handle_tool_call

    try:
        # Validate OpenAI API key
        api_key = settings.OPENAI_API_KEY
        if not api_key or api_key == 'YOUR_OPENAI_API_KEY_HERE':
            logger.error("OpenAI API key is not configured")
            raise ValueError("OpenAI API key is not configured. Check settings.OPENAI_API_KEY")

        # ── Agent routing — pick the right agent + its DB-configured params ──
        agent_key = _get_agent_key(run)
        agent_params = _get_agent_params(agent_key)
        model       = agent_params.get('model', settings.OPENAI_MODEL)
        temperature = agent_params.get('temperature', 0.7)
        max_tokens  = agent_params.get('max_tokens', 8000)

        # tool_instructions is now a shared section (order=25) — loaded automatically for all agents
        system = build_system_prompt(run, agent_key)

        client = OpenAI(api_key=api_key)

        # Get chat history
        try:
            history = run.get_chat_history()
        except Exception as e:
            logger.error(f"Error retrieving chat history for run {run.id}: {str(e)}", exc_info=True)
            history = []

        history.append({"role": "user", "content": user_message})

        api_messages = [{"role": "system", "content": system}, *history[-20:]]

        ai_reply = ''
        last_tool_chat = ''

        for attempt in range(5):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=api_messages,
                    tools=BUNDLE_TOOLS,
                    tool_choice='auto',
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except Exception as e:
                logger.error(
                    f"OpenAI API error on attempt {attempt + 1}/5 for run {run.id}: {str(e)}",
                    exc_info=True
                )
                if attempt == 4:  # Last attempt
                    raise
                continue
            
            try:
                msg = response.choices[0].message
            except (IndexError, AttributeError) as e:
                logger.error(f"Error parsing OpenAI response for run {run.id}: {str(e)}", exc_info=True)
                raise ValueError("Invalid response from OpenAI API")

            if msg.tool_calls:
                assistant_msg = {
                    'role': 'assistant',
                    'content': msg.content or '',
                    'tool_calls': [
                        {
                            'id': tc.id,
                            'type': 'function',
                            'function': {
                                'name': tc.function.name,
                                'arguments': tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
                api_messages.append(assistant_msg)

                for tc in msg.tool_calls:
                    try:
                        result, chat_msg, _ = handle_tool_call(run, tc)
                        last_tool_chat = chat_msg
                        api_messages.append({
                            'role': 'tool',
                            'tool_call_id': tc.id,
                            'content': result,
                        })
                    except Exception as e:
                        logger.error(
                            f"Error handling tool call {tc.function.name} for run {run.id}: {str(e)}",
                            exc_info=True
                        )
                        raise
                continue

            raw_reply = msg.content or ''
            try:
                save_data_from_tag(run, user_message, raw_reply)
            except Exception as e:
                logger.error(f"Error saving data from AI response for run {run.id}: {str(e)}", exc_info=True)
                # Don't fail the whole request if data saving fails
            
            ai_reply, _ = parse_suggestions(raw_reply)
            break
        else:
            ai_reply = last_tool_chat or (
                'Your report is ready — use the button below to view it.'
            )

        if last_tool_chat and not ai_reply:
            ai_reply = last_tool_chat

        # ── AUTO-TRIGGER plan generator ─────────────────────────────────────────
        # The analyzer produces submit_ai_analysis but its 12k token budget is
        # often exhausted before it can write all session rows in submit_final_plan.
        # We detect this and make a separate plan_generator call (16k tokens,
        # full stage_5 system prompt) to generate the plan properly.
        if run.ai_analysis_json and (not run.final_plan_json or not _plan_has_sessions(run)):
            try:
                plan_msg = _auto_generate_plan(run, client)
                if plan_msg:
                    last_tool_chat = plan_msg
                    if not ai_reply:
                        ai_reply = plan_msg
            except Exception as e:
                logger.error(
                    f"Auto plan generation failed for run {run.id}: {str(e)}",
                    exc_info=True,
                )

        if not ai_reply and last_tool_chat:
            ai_reply = last_tool_chat

        history.append({"role": "assistant", "content": ai_reply})
        
        try:
            run.set_chat_history(history)
        except Exception as e:
            logger.error(f"Error saving chat history for run {run.id}: {str(e)}", exc_info=True)

        if not run.ai_analysis_json and not run.final_plan_json:
            try:
                detect_and_update_stage(run, user_message, ai_reply)
            except Exception as e:
                logger.error(f"Error detecting stage for run {run.id}: {str(e)}", exc_info=True)

        suggestions = _resolve_suggestions(run, ai_reply)
        run.save()

        return ai_reply, suggestions
    
    except Exception as e:
        logger.error(f"Critical error in chat_with_ai for run {run.id}: {str(e)}", exc_info=True)
        raise
