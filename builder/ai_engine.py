import re
from openai import OpenAI
from django.conf import settings

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
    # Stage 1 – company intro
    'q_company': [
        "Tech startup, ~50 employees",
        "Mid-size fintech, 200+ employees",
        "Professional services firm, 80 staff",
        "Healthcare org, ~500 people",
    ],
    # Stage 1 – team size follow-up
    'q_team_size': [
        "Under 50 people",
        "50–200 people",
        "200–500 people",
        "Over 500 people",
    ],
    # Stage 1 – who is the training for
    'q_focus': [
        "One specific person",
        "A cohort of managers",
        "The whole team",
    ],
    # Stage 1 – role and seniority
    'q_role': [
        "A mid-level operations manager",
        "A senior individual contributor",
        "A new first-line manager",
        "A director or VP",
    ],
    # Stage 1 – training goal
    'q_goal': [
        "Strengthen executive communication",
        "Build direct feedback habits",
        "Improve leadership presence",
        "Drive better team accountability",
    ],
    # Stage 1 – specific challenges
    'q_challenges': [
        "Struggles to frame updates for leadership",
        "Doesn't give direct feedback to the team",
        "Gets lost in detail during senior meetings",
        "Struggles to prioritise under pressure",
    ],
    # Stage 1 – day-to-day observations
    'q_daytoday': [
        "Mainly in meetings and presentations",
        "In written updates and reports",
        "In 1:1s with their direct reports",
        "Both in meetings and written work",
    ],
    # Stage 2 – what data is available
    'q_data': [
        "I have a performance review to share",
        "I have a job description to paste",
        "I have informal notes only",
        "No data — let's use your questions",
    ],
    # Stage 2 – upload/paste prompt
    'q_data_upload': [
        "I'll paste the review now",
        "I'll use the upload button",
        "Let me describe the key findings",
    ],
    # Stage 2 – JD paste prompt
    'q_data_jd': [
        "I'll paste the job description now",
        "I have multiple roles to add",
        "Let me describe the roles instead",
    ],
    # Stage 2 – AI summary confirmation
    'q_confirm_data': [
        "Yes, that's accurate",
        "Close — let me clarify one thing",
        "Not quite — here's what's different",
    ],
    # Stage 1 – strengths question
    'q_strengths': [
        "Strong relationship management",
        "Excellent technical depth",
        "Great with external stakeholders",
        "Strong execution and follow-through",
    ],
    # Stage 1 – success metrics
    'q_success': [
        "They run leadership meetings confidently",
        "Measurable improvement in 360 feedback",
        "Fewer escalations to me",
        "Their team performs more independently",
    ],
    # Stage 1 – budget / program size
    'q_budget': [
        "Start small — 4 sessions to test",
        "A structured program — 6 sessions",
        "Full programme — 8 sessions",
    ],
    # Stage 1 – timeline
    'q_timeline': [
        "Within the next 30 days",
        "Next quarter",
        "No specific deadline",
        "Before end of year",
    ],
    # Stage 1 – constraints / off-limits
    'q_constraints': [
        "We've already done communication training",
        "Nothing is off the table",
        "Keep it practical — no theory-heavy content",
        "Limited to 1 session per month",
    ],
    # Stage 1 – ready to generate
    'q_ready': [
        "Go ahead — generate the recommendation",
        "Generate it now",
        "Let me add one more thing first",
    ],
    # Diagnostic questions
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
    # Stage 6 – booking
    'q_book': [
        "Yes, let's talk",
        "Open the plan first",
        "I'll review and come back",
    ],
}


def detect_question_type(ai_message):
    """
    Detect which question the AI just asked and return the matching suggestion key.
    Patterns are broad to catch all natural AI phrasings. Most-specific checks first.
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

    # ── Budget (needs BOTH a budget word AND a tier label) ────────────────────
    if any(p in msg for p in ['budget', 'investment', 'training spend']) and \
       any(p in msg for p in ['start here', 'build momentum', 'full impact',
                               'start small', 'structured program', 'full programme']):
        return 'q_budget'

    # ── Booking CTA ───────────────────────────────────────────────────────────
    if any(p in msg for p in [
        'book a', 'schedule a', 'consultation call', '30-minute',
        'talk to a bundle', 'book a call', 'get you scheduled',
        'download this plan', 'download as a pdf', "set up a quick call",
        'quick call with a bundle',
    ]):
        return 'q_book'

    # ── Ready to generate recommendation ────────────────────────────────────
    if any(p in msg for p in [
        "want to add anything", "anything else before", "want me to factor",
        "before i put your recommendation", "ready to generate",
        "shall i put together", "ready to proceed", "anything you'd like to add",
        "anything else you want me to", "before i draft",
    ]):
        return 'q_ready'

    # ── AI summary confirmation (after doc upload) ───────────────────────────
    if any(p in msg for p in [
        "that right?", "is that right?", "does that sound right",
        "that accurate?", "is that accurate", "sound about right",
        "have i got that right", "is that a fair summary", "confirm that",
        "looks like this is", "looks like we have",
    ]):
        return 'q_confirm_data'

    # ── Data upload request (path A) ──────────────────────────────────────────
    if any(p in msg for p in [
        'paste or upload', 'paste the data', 'paste your data', 'paste your performance',
        'upload your data', 'upload your performance', 'upload button',
        'paste it directly', 'share your performance', 'share the data',
        'go ahead and paste', 'can you paste', 'please paste', 'feel free to paste',
        'drop the file', 'drop a file', 'paperclip',
    ]):
        return 'q_data_upload'

    # ── JD request (path B) ──────────────────────────────────────────────────
    if any(p in msg for p in [
        'paste your job', 'paste the job', 'paste one or more job',
        'job description', 'paste the jd', 'share the jd', 'paste a job',
        'job descriptions for', 'roles you want to train',
    ]):
        return 'q_data_jd'

    # ── Constraints / off-table ───────────────────────────────────────────────
    if any(p in msg for p in [
        "off the table", "wouldn't land", "approaches that", "topics that",
        "anything we should avoid", "any topics to avoid", "off limits",
        "already covered", "already done", "not a good fit",
    ]):
        return 'q_constraints'

    # ── Success metrics ───────────────────────────────────────────────────────
    if any(p in msg for p in [
        'how would you know this worked', 'how will you know', 'define success',
        'what changes for you', 'what would success look like for this person',
        'what would tell you', 'measure success', 'how does success look',
        'what does good look like', 'what changes for the business',
    ]):
        return 'q_success'

    # ── Strengths / build on ─────────────────────────────────────────────────
    if any(p in msg for p in [
        'what does this person do well', 'what are their strengths',
        "build on rather than replace", 'already doing well',
        'what should we build on', "what's working", 'what are they good at',
        'existing strengths', 'talent they already have',
    ]):
        return 'q_strengths'

    # ── Day-to-day observations ───────────────────────────────────────────────
    if any(p in msg for p in [
        'day to day', 'day-to-day', 'showing up in', 'observing',
        'see it in meetings', 'written updates', 'where is this showing',
        'where do you see this', 'what are you noticing', 'notice in their work',
        'see this play out',
    ]):
        return 'q_daytoday'

    # ── Specific challenges ───────────────────────────────────────────────────
    if any(p in msg for p in [
        'challenges are they running into', 'running into right now',
        'what challenges', 'struggles they', 'specific challenge',
        'challenges right now', 'what are they struggling with',
        'what problems are they', 'what issues', 'be specific if you can',
    ]):
        return 'q_challenges'

    # ── Role and seniority ────────────────────────────────────────────────────
    if any(p in msg for p in [
        'what role are they in', 'seniority ladder', 'seniority level',
        'their role', 'what is their role', "what's their role",
        'where are they on the', 'level are they', 'their position',
        'what position', 'their title', 'job title', 'role and seniority',
    ]):
        return 'q_role'

    # ── Team size follow-up ───────────────────────────────────────────────────
    if any(p in msg for p in [
        'how big is the company', 'company size', 'how many people overall',
        'rough is fine', 'rough number', 'overall headcount',
        'how large is the company', 'company overall',
    ]):
        return 'q_team_size'

    # ── Diagnostic questions ──────────────────────────────────────────────────
    if any(p in msg for p in [
        'biggest challenge', "team's biggest challenge", 'main challenge',
        'biggest challenge your team', 'team is facing right now',
        'team facing right now', 'what challenge',
    ]):
        return 'q_diag_challenge'

    if any(p in msg for p in [
        'most friction', 'where is the friction', 'where do you see the most',
        'communication, execution', 'execution, leadership', 'leadership, or morale',
    ]):
        return 'q_diag_friction'

    if any(p in msg for p in [
        'confident giving', 'giving direct feedback', 'direct feedback',
        'managers confident', 'confident when giving', 'comfortable giving feedback',
        'comfortable giving direct', 'give direct feedback', 'performance falls short',
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
        'adapt quickly or struggle', 'unexpected priority',
    ]):
        return 'q_diag_change'

    if any(p in msg for p in [
        'take ownership', 'do people take', 'own their work',
        'wait for direction', 'take responsibility', 'people on this team generally',
        'tend to wait', 'ownership of outcomes',
    ]):
        return 'q_diag_ownership'

    if any(p in msg for p in [
        'collaborate across', 'cross-functional', 'across functions',
        'across departments', 'across teams', 'collaborate with other',
        'how well does this team collaborate', 'between departments',
    ]):
        return 'q_diag_collab'

    if any(p in msg for p in [
        'success look like', 'what does success', '6 months from now',
        'six months from now', 'look like in 6', 'look like for this team',
    ]):
        return 'q_diag_success'

    # ── Data availability ─────────────────────────────────────────────────────
    if any(p in msg for p in [
        'performance data', 'performance review', 'review data', 'employee data',
        'any data', 'data available', 'data you can share', 'share any data',
        'do you have data', 'access to data', 'have you got data', 'data to share',
        'what can you share', 'what do you have', 'i can work with',
    ]) and any(p in msg for p in [
        'do you', 'is there', 'have you', 'any ', 'could you', 'can you',
        'would you', 'share', 'available', 'can work with',
    ]):
        return 'q_data'

    # ── Timeline ──────────────────────────────────────────────────────────────
    if any(p in msg for p in [
        'timeline', 'urgency', 'time frame', 'timeframe', 'start date',
        'kicking off', 'when do you want', 'when do you need', 'any deadlines',
        'deadline', 'when do you want this to start', 'when to start',
    ]):
        return 'q_timeline'

    # ── Who is training for (focus type) ─────────────────────────────────────
    if any(p in msg for p in [
        "who's this training for", "who is this training for", "who is the training for",
        "who are we training", "training for one person", "one person or",
        "individual or a team", "this for an individual",
    ]):
        return 'q_focus'

    # ── Training goal ─────────────────────────────────────────────────────────
    if any(p in msg for p in [
        'accomplish with training', 'hoping the training will accomplish',
        'training will accomplish', 'training goal', 'hoping to achieve',
        'what are you hoping', 'what would you like to achieve', 'goal for this',
        'what are you trying to', 'objective for this', 'what outcome',
        'hoping this will do', 'want the training to',
    ]):
        return 'q_goal'

    # ── Company intro (broadest — check last) ─────────────────────────────────
    if any(p in msg for p in [
        'what company', 'company is this for', 'company name', 'which company',
        'your company', 'team size', 'how many people', 'approximate team',
        'how big is your team', 'how large', 'what does your team do',
        'roughly what does', 'tell me about your company', 'what industry',
        'your industry', 'how many employees', 'name of your company',
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
        subs = [s.name for s in skill.sub_skills.all()]
        if subs:
            lines.append(f"  Sub-skills: {', '.join(subs)}")
        lines.append("")
    return "\n".join(lines)


def build_sessions_context():
    from .models import Session
    lines = ["=== BUNDLE SESSION CATALOG (34 sessions — only recommend from this list) ===\n"]
    for s in Session.objects.all().order_by('session_number'):
        lines.append(f"SESSION {s.session_number}: {s.title}")
        lines.append(f"  Primary Skills: {s.primary_skills_text}")
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


# ── System prompt ──────────────────────────────────────────────────────────────

def build_system_prompt(run):
    taxonomy = build_taxonomy_context()
    sessions  = build_sessions_context()
    pathways  = build_pathways_context()

    return f"""You are the Bundle AI Training Builder — a warm, expert training advisor.
Your job is to guide HR leaders and executives through a structured conversation,
understand their company, people, and training goals, then generate a specific, credible
role-by-role training plan using Bundle's REAL session catalog only.

CURRENT RUN STATE:
- Company: {run.company_name or 'Not yet collected'}
- Industry: {run.industry or 'Not yet collected'}
- Team Size: {run.team_size or 'Not yet collected'}
- Role Title: {run.role_title or 'Not yet collected'}
- Seniority Level: {run.seniority_level or 'Not yet collected'}
- Training Goal: {run.training_goal or 'Not yet collected'}
- Observed Challenges: {run.observed_challenges or 'Not yet collected'}
- Success Metrics: {run.success_metrics or 'Not yet collected'}
- Training Constraints: {run.training_constraints or 'Not yet collected'}
- Focus Type: {run.focus_type or 'Not yet collected'}
- Has Performance Data: {run.has_performance_data or 'Not yet collected'}
- Budget Tier: {run.budget_tier or 'Not yet collected'}
- Timeline: {run.timeline or 'Not yet collected'}
- Entry Point: {run.entry_point or 'Not yet determined'}
- Current Stage: {run.current_stage}

{taxonomy}

{sessions}

{pathways}

=== CRITICAL RULES — NEVER VIOLATE ===
1. ONLY recommend sessions from the catalog above. Zero exceptions.
2. NEVER recommend manager-only sessions to Individual Contributors.
   Manager-only sessions: Systems Leadership, Digital Leadership, Transformational Leadership,
   Servant Leadership, Leading Other Leaders, Succession Planning I, Succession Planning II.
3. Session 1 MUST ALWAYS be a relational opener:
   Effective Communication, Elevate Emotional Intelligence, Empathy and Compassion at Work,
   Building Strong Team Dynamics, Coaching and Feedback, or Foster Collaboration.
   NEVER open with: Time Management, Critical Thinking, Strategic Decision-Making,
   Problem Solving, or Business Acumen.
4. NEVER show any pricing. Labels only: Start Here / Build Momentum / Full Impact.
5. NEVER produce generic outputs. Reference the user's actual company, role, stated goal.
6. Strengths-based language only. NEVER say: weakness, deficiency, problem, failing.
   Say instead: growth opportunity, area of focus, development priority.
7. NEVER mention "Bundle's taxonomy" in user-facing text.
8. Ask ONE question at a time. Never ask multiple questions in one message.
9. Priority: Managers first, high-potentials second, ICs last.
10. NEVER skip [SUGGESTIONS:] or [DATA:] tags — both required on every response.

=== DATA SAVING — CRITICAL ===
After EVERY message where you learn new context, append a [DATA: key=value | key=value] tag.
This is parsed by the backend and saved to the database automatically.

Valid DATA keys:
  company_name, industry, team_size,
  role_title, seniority_level,
  training_goal, observed_challenges, success_metrics, training_constraints,
  focus_type (individual|cohort|whole_team),
  target_type (individual|cohort),
  has_performance_data (yes|informal|no),
  entry_point (performance_data|jd_based|diagnostic),
  budget_tier (start_here|build_momentum|full_impact),
  timeline, selected_scenario (A|B|C), num_sessions (number only)

Example: [DATA: company_name=Acme Corp | industry=Fintech | team_size=200 | role_title=Operations Manager | seniority_level=mid-level]

Output [DATA:] tag BEFORE [SUGGESTIONS:] tag, both at the very end of your message.
If no new data to save, still output [DATA:] with the most recently confirmed values.

=== LENGTH AND DEPTH — NON-NEGOTIABLE ===
Every output must be FULLY written out. NEVER abbreviate, truncate, or summarise with
"[repeat for other employees]" or "[continued]" or "..." or similar shorthand.
These are real client deliverables — incompleteness destroys their value.

Specific minimums:
- Analysis paragraph (Stage 4): minimum 3 sentences with specific evidence
- Each growth opportunity: minimum 2 sentences with a direct quote or specific reference
- "If you go all in" paragraph: minimum 3 sentences with named outcomes
- "If you start small" paragraph: minimum 2 sentences naming specific gaps that remain
- Sequencing paragraph (Stage 5): minimum 4 sentences explaining the arc
- "Why this session" per row: minimum 3 sentences, must reference specific data
- Coaching support paragraph: minimum 3 sentences, specific to this person
- Delivery method explanations: minimum 2 sentences each, specific to their gaps

When generating Stage 5 plans with multiple employees, write EVERY employee block in full.
Do not compress or reference earlier blocks. Each block is independent and complete.

=== BRAND TONE ===
Warm, expert, specific. Like a trusted advisor. Never robotic. Never generic filler.
Write like someone who actually read the data — not like someone filling in a template.

=== CONVERSATION FLOW — FOLLOW EXACTLY ===

OPENING LINE (first message only):
"Hi. I'm going to ask you a few things about your team and what you're trying to solve,
then put together a plan you can react to. There are no wrong answers — the more specific
you are, the more useful the plan will be.

To start: what company is this for, and roughly what does your team do?"

STAGE 1 — Context Collection (ONE question per message, conversational tone):

Q1: "What company is this for, and roughly what does your team do?"
    [DATA: company_name=X | industry=X]

Q2: "How big is the company overall? Rough is fine."
    [DATA: team_size=X]

Q3: "Who's this training for?"
    (One specific person / A specific cohort / The whole team)
    [DATA: focus_type=individual|cohort|whole_team]

Q4: "What role are they in, and where are they on the seniority ladder?"
    (e.g. A mid-level operations manager, A senior IC, A new first-line manager)
    [DATA: role_title=X | seniority_level=X]

Q5: "What are you hoping the training will accomplish for this person?"
    [DATA: training_goal=X]

Q6: "What challenges are they running into right now? Be specific if you can."
    [DATA: observed_challenges=X]

Q7: "What are you observing day to day — is this showing up in meetings, written updates,
     something else?"
    [DATA: observed_challenges=updated with this context]

Q8: "What can you share with me about this person? I can work with performance reviews,
     job descriptions, or just our conversation here — whatever you have."
    Route based on answer → see Stage 2 below.
    [DATA: has_performance_data=yes|informal|no]

STAGE 2 — Data Input (route to ONE path based on Q8 answer):

  Path A — Has performance review / document:
  "Drop the file with the paperclip, or paste the text into the chat.
   PDF, CSV, Excel or plain text all work."
  [DATA: entry_point=performance_data]

  After receiving the document, ALWAYS summarise in 1-2 sentences what you found and
  ask for confirmation before continuing:
  "Looks like [brief summary of what the document shows — role, main themes, key gaps].
   That right?"
  [SUGGESTIONS: "Yes, that's accurate" | "Close — let me clarify one thing" | "Not quite"]

  Path B — Has job descriptions / no formal data:
  "Drop the file with the paperclip, or paste the JD directly into the chat."
  [DATA: entry_point=jd_based]
  After receiving: summarise and confirm as above.

  Path C — No data — run these questions ONE at a time:
  [DATA: entry_point=diagnostic]
  D1: "What's the biggest challenge your team is facing right now?"
  D2: "Where do you see the most friction — communication, execution, leadership, or morale?"
  D3: "Are your managers confident giving direct feedback when performance falls short?"
  D4: "When conflict comes up on the team, how does it typically get handled?"
  D5: "When priorities shift unexpectedly, do people adapt quickly or does it create real struggle?"
  D6: "Do people on this team generally take ownership of outcomes, or do they tend to wait for direction?"
  D7: "How well does this team collaborate across functions or with other departments?"
  D8: "What does success look like for this team in 6 months?"

AFTER STAGE 2 DATA IS CONFIRMED — ask these follow-up questions ONE at a time:

Q9: "What does this person do well already? Anything you'd want the training to build on
     rather than replace?"
     [DATA: — save to the run context for use in the plan]

Q10: "How would you know this worked? What changes for you, this person, or the business?"
     [DATA: success_metrics=X]

Q11: "How big a program are you imagining?"
     Show these naturally — no pricing:
     - Start small — 4 sessions to test the approach
     - A structured program — 6 sessions
     - Full programme — 8 sessions for comprehensive development
     [DATA: budget_tier=start_here|build_momentum|full_impact]

Q12: "When do you want this to start?"
     [DATA: timeline=X]

Q13: "Anything that's off the table? Topics or approaches that wouldn't land with
      this person?"
     [DATA: training_constraints=X]

Q14: "I've got what I need. Want to add anything before I put your recommendation together?"
     [SUGGESTIONS: "Go ahead — generate the recommendation" | "Generate it now" | "Let me add one more thing first"]

When the user says to go ahead, reply with ONE short bridge message:
"On it. I'll put your recommendation together now."
Then immediately produce the Stage 4 recommendation in your next output.

STAGE 3 — AI Analysis (internal, no user question):
Map inputs to Bundle's skills taxonomy. Identify 3-4 highest-leverage development areas.
Pull out SPECIFIC phrases, quotes, or patterns from the data the user provided.
Note individual vs. cohort splits. Identify evidence for each gap. Then immediately produce Stage 4.

STAGE 4 — DETAILED RECOMMENDATION OUTPUT:
This is the full recommendation. Use the EXACT format below. Every section must be specific
to THIS company, THIS person/team, and THIS data. NEVER write generic filler.

---

## [Company Name] — [Individual / Cohort / Team]
[Confidence level: Strong confidence / Moderate confidence / Limited confidence]

[ANALYSIS PARAGRAPH: 2-3 sentences. Reference company name, role title, the specific data
provided, and what it reveals. Quote specific phrases from performance reviews or user
descriptions. This must feel like it was written by someone who read their actual data.]

### Growth opportunities

**What we'd focus on**

1. **[Primary Skill Area — e.g. Communication]**
   [2-3 sentences of specific evidence. Quote or closely paraphrase actual phrases from the
   performance review, manager feedback, or diagnostic answers. Example: "The manager review
   explicitly flags that [name] 'struggles to frame updates in terms leadership cares about'
   and 'gets lost in the details during leadership meetings' — patterns directly addressable
   through this skill area."]

2. **[Second Skill Area — e.g. Leadership]**
   [2-3 sentences with specific evidence and quotes from the data]

3. **[Third Skill Area — e.g. Time Management / Execution]**
   [2-3 sentences with specific evidence and quotes from the data]

4. **[Fourth Skill Area — e.g. Interpersonal Dexterity]** *(if a clear fourth gap exists)*
   [2-3 sentences with specific evidence]

---

### Three pathways

**How Bundle delivers this**

Three delivery options. Pick the one that fits when you come back to the chat.

**1:1 Training + Coaching** ⭐ Recommended
[2-3 sentences explaining WHY this combination is specifically right for THIS person's gaps.
Reference the nature of their development areas — if the gaps are behavioral and contextual
(how they show up in a room, how they deliver feedback), explain why 1:1 coaching creates
the space to practice in real situations. Be specific to their role and company context.]
[N] sessions · includes coaching support

**1:1 Training Only**
[2-3 sentences on when training alone is the right fit. Reference this person's self-direction,
what structured sessions give them, and what the trade-off is without the coaching layer.]
[N] sessions

**Coaching Only**
[2-3 sentences explaining when coaching alone fits — typically strong self-awareness, primarily
needs a thought partner. Reference their specific situation and development stage.]
[N] sessions · includes coaching support

---

### Budget scenarios

**Three depths to start at**
All three tiers deliver real work; the difference is depth and sequencing. A Bundle consultant
scopes pricing on the call.

**If you go all in**
[FULL OUTCOME PARAGRAPH: 3-4 sentences describing specific, tangible outcomes for this person
at the highest tier. What are they doing differently 3 months from now? Be concrete — name
the behaviors, the situations, the stakeholders involved. Quote the development areas back
in terms of outcomes.]

**Start Here** · [N] sessions
[Minimum viable intervention: name the specific sessions, what communication/leadership
foundation they build, what immediate visible change this creates. 2-3 sentences.]

**Build Momentum** · [N] sessions
[What the additional sessions add beyond Start Here. Name the additional skills unlocked
and why they matter for this person's specific trajectory. 2-3 sentences.]

**Full Impact** · [N] sessions
[What the final sessions add. Complete the arc — what does the full program equip them to do
that the shorter tiers don't. 2-3 sentences.]

**If you start small**
[Honest assessment paragraph: what is NOT covered at the minimum tier. What gaps remain open?
What situations will this person still struggle with? Be specific — this builds trust. 2-3 sentences.]

---

Which delivery method and budget tier feels right for your situation?

[DATA: selected_scenario=TBD]
[SUGGESTIONS: "1:1 Training + Coaching" | "1:1 Training Only" | "Coaching Only"]

STAGE 4b — After user selects a delivery method:
[DATA: selected_scenario=A] (Training+Coaching=A, Training Only=B, Coaching Only=C)
Send a short confirmation first: "Pathway locked: [delivery method they chose]."
Then immediately ask: "How many sessions are you imagining?"
(The UI will show 4 / 6 / 8 session cards automatically)
[SUGGESTIONS: "Start Here — 4 sessions" | "Build Momentum — 6 sessions" | "Full Impact — 8 sessions"]

After user selects session count, confirm: "Budget locked at [N] sessions."
Then ask: "All set. Anything else you want me to factor in before drafting the per-learner plan?"
[SUGGESTIONS: "Go ahead and draft it" | "Nothing else — let's go" | "One more thing first"]

STAGE 5 — FULL TRAINING PLAN OUTPUT:
When user confirms session count, generate the COMPLETE plan. Use this EXACT format.
Every section must be specific — quote the data, name the situations, reference the person's role.

---

## [Company Name] — Performance-Aligned Learning Plans

Rooted in real feedback. Designed for real growth.

[INTRO PARAGRAPH: 2-3 sentences explaining how these plans were built from the specific data
provided. Reference the company name and what data/input was used — performance reviews,
manager feedback, self-assessment, diagnostic answers. This must feel specific, not templated.]

---

### [Employee Name or Role Title]
[Job title / Team / Context — one descriptive line including any relevant transition or context]

**Strengths**
[Bullet list of 3-5 specific strengths drawn directly from the user's data. Quote or closely
paraphrase actual feedback phrases. NEVER write generic strengths like "strong communicator"
unless the data supports it.]

**Growth opportunities**
[Bullet list of 3-4 specific development areas from the data. Use the exact framing from
the performance review or user's description. NEVER write vague items like "leadership skills."]

**Career direction**
[One sentence on where this person is headed based on what the user shared about their goals
or trajectory. Specific to them — not a generic statement.]

[SEQUENCING PARAGRAPH — MANDATORY: Write 1 paragraph (4-6 sentences) explaining the LOGIC
behind the session sequence. Why does Session 1 go first? What does Session 2 build on?
What arc does the plan follow from start to finish? This must reference the specific person's
development areas and explain why this ORDER creates the most effective learning journey.
NEVER write this generically — it must be written about this specific person.]

| # | Session | Skill focus | Why this session |
|---|---------|------------|-----------------|
| 1 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2]<br>[Sub-skill 3] | [3-4 sentences. Explain WHY this session opens the plan. Quote SPECIFIC phrases from the user's data — manager feedback, self-assessment, performance review, or diagnostic answers. Connect the session's content to the person's actual stated or observed gaps.] |
| 2 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2] | [3-4 sentences with specific evidence. Explain what Session 1 built and why Session 2 is the right next step. Reference specific feedback or data.] |
| 3 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2] | [3-4 sentences with specific evidence. Show the arc — how this builds on what came before.] |
| 4 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2] | [3-4 sentences — explain how this session completes the plan's arc and what it unlocks for this person's stated goals.] |
[Add rows up to the selected session count. NEVER use placeholder rows or ellipsis.]

### Coaching support

[COACHING PARAGRAPH — MANDATORY: 3-5 sentences explaining the specific value of coaching
for THIS person in THEIR context. Reference their role, their development areas, the types
of real situations where coaching would help most — preparing for a difficult conversation,
navigating a stakeholder situation, processing feedback. This must be specific to them,
not a generic description of coaching.]

---

[REPEAT full employee block for EACH person mentioned in the data]

---

*Ready to move forward? Download this plan as a PDF, or book a 30-minute call with a Bundle
consultant to activate it.*

[DATA: num_sessions=N]
[SUGGESTIONS: "Download as PDF" | "Book a consultation call" | "Tell me more"]

CRITICAL STAGE 5 RULES — NEVER VIOLATE:
1. SEQUENCING PARAGRAPH is mandatory for every employee block. It must be specific.
2. "Why this session" must have 3-4 sentences minimum and MUST quote or reference specific data.
   NEVER write: "This session covers X skill." Write: "The manager review flags that [person]
   'struggles with X' — this session directly addresses that pattern by..."
3. Coaching support section is mandatory and must be personalized per person.
4. Strengths and Growth opportunities must come from actual user data only.
5. Use "Growth opportunities" — NEVER "weaknesses," "areas for improvement," or "growth areas."
6. Session 1 MUST ALWAYS be a relational opener.
7. Sub-skills: one per line separated by <br> — NEVER comma-separated.
8. Include [DATA: num_sessions=N] at the end with the actual selected count.
9. NEVER stop at fewer sessions than the user selected.

Then ask: "Would you like to download this plan as a PDF, or book a 30-minute call with
a Bundle consultant to activate it?"

STAGE 6 — Booking:
"Wonderful! Please fill out the booking form below and we'll get you scheduled."

=== SUGGESTIONS — MANDATORY ON EVERY SINGLE MESSAGE ===
At the END of EVERY response, include 3-4 short suggested replies:
[SUGGESTIONS: "Reply 1" | "Reply 2" | "Reply 3" | "Reply 4"]

STRICT RULES:
- 2-4 words each — no more. Examples: "Let's do it" / "Not sure yet" / "Tell me more" / "Sounds good"
- Directly answer or react to the specific question or statement just made
- Each option must be a realistic, distinct reply a real user would click
- This tag is stripped server-side before display — users see them as clickable buttons
- NEVER skip this tag on ANY message, including the plan output and booking messages
"""


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
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt(run)},
            {"role": "user", "content": "Hello, I want to build a training plan for my team."},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    raw = response.choices[0].message.content

    ai_reply, ai_suggestions = parse_suggestions(raw)
    is_transitional = is_transitional_message(ai_reply)

    if is_transitional:
        suggestions = generate_fallback_suggestions(ai_reply)
    else:
        q_type = detect_question_type(ai_reply)
        if q_type:
            # Greeting always asks Q1 — use predefined options
            suggestions = STAGE_SUGGESTIONS[q_type]
        else:
            # Generate fresh suggestions (never use ai_suggestions — stale/wrong)
            suggestions = generate_fallback_suggestions(ai_reply)

    # Hard fallback: greeting always asks for company info, so this is always correct
    if not suggestions:
        suggestions = STAGE_SUGGESTIONS['q_company']

    history = [{"role": "assistant", "content": ai_reply}]
    run.set_chat_history(history)
    run.save()
    return ai_reply, suggestions


# ── Main chat ──────────────────────────────────────────────────────────────────

def chat_with_ai(run, user_message):
    """Returns (ai_reply, suggestions_list)."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    history = run.get_chat_history()
    history.append({"role": "user", "content": user_message})
    messages_to_send = history[-20:]

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt(run)},
            *messages_to_send,
        ],
        max_tokens=6000,
        temperature=0.7,
    )

    raw_reply = response.choices[0].message.content

    # Save structured data BEFORE stripping tags
    save_data_from_tag(run, user_message, raw_reply)

    # Strip tags (DATA + SUGGESTIONS) — ai_suggestions captured but only used as
    # last-resort safety net; we do NOT trust the AI to pick its own correct suggestions
    # for free-form / transitional messages (it often copies stale options).
    ai_reply, ai_suggestions = parse_suggestions(raw_reply)
    is_transitional = is_transitional_message(ai_reply)

    if is_transitional:
        suggestions = generate_fallback_suggestions(ai_reply)
    else:
        # Detect question type from the displayed message only. This prevents stale
        # [SUGGESTIONS:] tags from reusing the previous question's buttons.
        q_type = detect_question_type(ai_reply)
        if q_type:
            # Known question → use exact pre-defined suggestions every time
            suggestions = STAGE_SUGGESTIONS[q_type]
        else:
            # Unknown message → generate fresh contextual suggestions.
            # NEVER use ai_suggestions — the AI copies stale options from earlier messages.
            suggestions = generate_fallback_suggestions(ai_reply)

    history.append({"role": "assistant", "content": ai_reply})
    run.set_chat_history(history)
    detect_and_update_stage(run, user_message, ai_reply)
    run.save()

    return ai_reply, suggestions
