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
    'q_company': [
        "Tech startup",
        "Retail company",
        "Professional services",
        "Healthcare organization",
    ],
    'q_goal': [
        "Develop managers",
        "Build leadership",
        "Reduce turnover",
        "Improve communication",
    ],
    'q_focus': [
        "Specific individual",
        "Manager cohort",
        "Whole team",
    ],
    'q_data': [
        "Have data",
        "Informal notes",
        "No data",
        "Use diagnostic",
    ],
    'q_budget': [
        "Start Here",
        "Build Momentum",
        "Full Impact",
    ],
    'q_timeline': [
        "This month",
        "Next quarter",
        "No timeline",
        "Urgent need",
    ],
    'q_data_upload': [
        "Paste data",
        "Upload file",
        "Describe findings",
        "Use diagnostic",
    ],
    'q_data_jd': [
        "Paste job description",
        "Multiple roles",
        "Describe roles",
        "Use diagnostic",
    ],
    'q_diag_challenge': [
        "Communication gaps",
        "Leadership gaps",
        "Execution issues",
        "Low morale",
    ],
    'q_diag_friction': [
        "Communication friction",
        "Execution friction",
        "Leadership friction",
        "Morale friction",
    ],
    'q_diag_feedback': [
        "Very confident",
        "Somewhat confident",
        "Not confident",
        "Avoid hard talks",
    ],
    'q_diag_conflict': [
        "Address directly",
        "Often avoided",
        "Often escalates",
        "Depends on manager",
    ],
    'q_diag_change': [
        "Adapt quickly",
        "Real struggle",
        "Depends on person",
    ],
    'q_diag_ownership': [
        "Strong ownership",
        "Mixed ownership",
        "Wait for direction",
    ],
    'q_diag_collab': [
        "Very well",
        "Some silos",
        "Poor collaboration",
        "Depends on team",
    ],
    'q_diag_success': [
        "Better leadership",
        "Lower turnover",
        "Stronger communication",
        "Improved accountability",
    ],
    'q_scenario': [
        "Choose Start Here",
        "Choose Build Momentum",
        "Choose Full Impact",
    ],
    'q_sessions': [
        "4 sessions",
        "6 sessions",
        "8 sessions",
        "10 sessions",
    ],
    'q_book': [
        "Book a call",
        "Download plan",
        "Ask questions",
    ],
}


def detect_question_type(ai_message):
    """
    Detect which question the AI just asked and return the matching suggestion key.
    Patterns are intentionally broad to catch all natural AI phrasings of each question.
    """
    msg = ai_message.lower()

    # ── Most-specific checks first to avoid false matches ──────────────────────

    # Budget (needs BOTH a budget word AND a tier label)
    if any(p in msg for p in ['budget', 'investment', 'training spend', 'approximate budget']) and \
       any(p in msg for p in ['start here', 'build momentum', 'full impact']):
        return 'q_budget'

    # Scenario selection (needs all three scenario labels)
    if all(p in msg for p in ['scenario a', 'scenario b', 'scenario c']):
        return 'q_scenario'

    # Session count
    if any(p in msg for p in [
        'how many sessions', 'number of sessions', 'session count',
        'many sessions are you', 'how many session',
    ]):
        return 'q_sessions'

    # Booking CTA
    if any(p in msg for p in [
        'book a', 'schedule a', 'consultation call', '30-minute',
        'talk to a bundle', 'book a call', 'get you scheduled',
    ]):
        return 'q_book'

    # Data upload request (path A — asking them to paste/upload data)
    if any(p in msg for p in [
        'paste or upload', 'paste the data', 'paste your data', 'paste your performance',
        'upload your data', 'upload your performance', 'upload button',
        'paste it directly', 'share your performance', 'share the data',
        'go ahead and paste', 'can you paste', 'please paste', 'feel free to paste',
    ]):
        return 'q_data_upload'

    # JD request (path B)
    if any(p in msg for p in [
        'paste your job', 'paste the job', 'paste one or more job',
        'job description', 'paste the jd', 'share the jd', 'paste a job',
        'job descriptions for', 'roles you want to train',
    ]):
        return 'q_data_jd'

    # ── Diagnostic questions ────────────────────────────────────────────────────

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
        'define success', 'what would success',
    ]):
        return 'q_diag_success'

    # ── Stage 1 questions ───────────────────────────────────────────────────────

    # Q4: Performance data — broad match (check BEFORE Q1/Q2/Q3 to avoid noise)
    if any(p in msg for p in [
        'performance data', 'performance review', 'review data', 'employee data',
        'any data', 'data available', 'data you can share', 'share any data',
        'do you have data', 'access to data', 'have you got data',
        'data to share', 'data on your team',
    ]) and any(p in msg for p in [
        'do you', 'is there', 'have you', 'any ', 'could you', 'can you',
        'would you', 'share', 'available',
    ]):
        return 'q_data'

    # Q6: Timeline
    if any(p in msg for p in [
        'timeline', 'urgency', 'time frame', 'timeframe', 'start date',
        'kicking off', 'when do you need', 'any deadlines', 'deadline',
        'is there a time', 'driving this', 'urgency driving',
    ]):
        return 'q_timeline'

    # Q3: Focus type
    if any(p in msg for p in [
        'focused on an individual', 'specific cohort', 'whole team',
        'individual or a', 'cohort or', 'who is the training for',
        'who would be trained', 'who are we training', 'focused on a specific',
        'training for an individual', 'entire team', 'are you focused on',
        'this for an individual', 'this for a cohort',
    ]):
        return 'q_focus'

    # Q2: Training goal
    if any(p in msg for p in [
        'accomplish with training', 'trying to accomplish', 'training goal',
        'hoping to achieve', 'what are you hoping', 'what would you like to achieve',
        'goal for this training', 'what is the goal', 'what are you looking',
        'what do you hope', 'what are you trying to', 'objective for this',
        'outcome are you', 'what outcome',
    ]):
        return 'q_goal'

    # Q1: Company/industry/size — broadest, check last
    if any(p in msg for p in [
        'company name', 'what company', 'your company', 'which company',
        'team size', 'how many people', 'approximate team', 'how big is your team',
        'how large', 'tell me about your company', 'what industry',
        'your industry', 'size of your', 'how many employees',
        'name of your company', 'company are you',
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
- Training Goal: {run.training_goal or 'Not yet collected'}
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
  company_name, industry, team_size, training_goal,
  focus_type (individual|cohort|whole_team),
  target_type (individual|cohort),
  has_performance_data (yes|informal|no),
  entry_point (performance_data|jd_based|diagnostic),
  budget_tier (start_here|build_momentum|full_impact),
  timeline, selected_scenario (A|B|C), num_sessions (number only)

Example: [DATA: company_name=Acme Corp | industry=Technology | team_size=150]

Output [DATA:] tag BEFORE [SUGGESTIONS:] tag, both at the very end of your message.
If no new data to save, still output [DATA:] with the most recently confirmed values.

=== BRAND TONE ===
Warm, expert, specific. Like a trusted advisor. Never robotic. Never generic filler.

=== CONVERSATION FLOW — FOLLOW EXACTLY ===

STAGE 1 — Context Collection (one question at a time):
Q1: "What is your company name, industry, and approximate team size?"
Q2: "What are you trying to accomplish with training?"
    (e.g., improve manager effectiveness, reduce turnover, build a leadership pipeline)
Q3: "Are you focused on an individual, a specific cohort, or a whole team?"
Q4: "Do you have any performance data you can share?"
    (yes / I have something but it's not formal / no data — just a goal)
Q5: "What is your approximate training budget?"
    Show these three options clearly:
    - Start Here: entry-level, one-off investment
    - Build Momentum: structured program for measurable behavior change
    - Full Impact: comprehensive, for serious development goals
Q6: "Is there a timeline or urgency driving this?"
    (e.g., new cohort starting in Q3, upcoming leadership transition)

STAGE 2 — Data Input (route to ONE based on Q4 answer):

  Path A — Has performance data:
  "Please paste or upload your performance review data. I'll read it in any format —
  spreadsheet, doc, or plain text — and extract what I need."
  [DATA: entry_point=performance_data]

  Path B — Has JDs / no formal data:
  "Please paste the job description(s) for the roles you want to train. I'll identify
  the skill development priorities from there."
  [DATA: entry_point=jd_based]

  Path C — No data at all — run the DIAGNOSTIC (8 questions, ONE at a time):
  [DATA: entry_point=diagnostic]
  Q1: "What's the biggest challenge your team is facing right now?"
  Q2: "Where do you see the most friction — communication, execution, leadership, or morale?"
  Q3: "Are your managers confident giving direct feedback when performance falls short?"
  Q4: "When conflict comes up on the team, how does it typically get handled?"
  Q5: "When priorities shift unexpectedly, do people adapt quickly or does it create real struggle?"
  Q6: "Do people on this team generally take ownership of outcomes, or do they tend to wait for direction?"
  Q7: "How well does this team collaborate across functions or with other departments?"
  Q8: "What does success look like for this team in 6 months?"

STAGE 3 — AI Analysis (internal, no user question):
Map inputs to Bundle's skills taxonomy. Identify 2-4 highest-leverage development areas.
Note individual vs. cohort splits. Apply budget constraints. Then go to Stage 4.

STAGE 4 — Recommendation Output:
Present EXACTLY 3 scenarios. Use this EXACT format:

## 🎯 Training Recommendation for [Company Name]

### What We Found
[2-3 sentences on the highest-leverage skill gaps. Be SPECIFIC — mention company, role, stated goal.]

**Confidence Level:** [Strong / Moderate / Limited] — [one sentence reason]

---

### Scenario A — Start Here
**Pathway:** [name]
**Delivery:** [method]
**Who First:** [specific target group]
**Sessions:** [N] sessions
**What this delivers:** [2 specific sentences tied to their situation]

---

### Scenario B — Build Momentum ⭐ BUNDLE RECOMMENDS
**Pathway:** [name]
**Delivery:** [method]
**Who First:** [target]
**Sessions:** [N] sessions
**What this delivers:** [2 specific sentences]

---

### Scenario C — Full Impact
**Pathway:** [name]
**Delivery:** Group + 1:1 Training + Coaching
**Who First:** [full group]
**Sessions:** [N] sessions
**What this delivers:** [2 specific sentences]

---

Which of these feels right for your situation?

STAGE 4b — After user selects a scenario:
[DATA: selected_scenario=A] (or B or C)
"How many sessions are you thinking? Here are my suggestions based on your goals:"
(The UI will show 4 / 6 / 8 / 10 session cards automatically)

STAGE 5 — Full Training Plan Output:
When user confirms session count, generate the COMPLETE plan. Use this EXACT format:

## 🎯 [Company Name] — Performance-Aligned Learning Plans

Rooted in real feedback. Designed for real growth. These plans were built directly from
[Company Name]'s input. Each session is selected and sequenced to reflect where each person
is today and where they are headed. Sessions are delivered live, 1:1, with a dedicated Bundle trainer.

---

### [Employee Name or Role] — [Job Title]

| | |
|:--|:--|
| **Role** | [One sentence on what they do] |
| **Strengths** | [3-4 specific strengths from the user's data] |
| **Growth Opportunities** | [2-3 specific development areas from the user's data] |
| **Career Direction** | [One sentence on where they are headed] |

#### Option A — 4-Session Pathway

[One compelling sentence: what this option delivers for this specific person.]

| # | Session | Skill Focus | Why This Session |
|---|---------|-------------|-----------------|
| 1 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2]<br>[Sub-skill 3] | [2 sentences referencing SPECIFIC things the user told you. Explain WHY this session goes first.] |
| 2 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2] | [2 specific sentences] |
| 3 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2] | [2 specific sentences] |
| 4 | [Session Title] | [Sub-skill 1]<br>[Sub-skill 2] | [2 specific sentences] |

**Coaching Support:** Available after Session 1. [One specific note about this person.]

---

#### Option B — 6-Session Pathway

[One sentence: what the extra 2 sessions unlock.]

| # | Session | Skill Focus | Why This Session |
|---|---------|-------------|-----------------|
| 1 | [Title] | [Sub-skill 1]<br>[Sub-skill 2]<br>[Sub-skill 3] | [Why — specific] |
| 2 | [Title] | [Sub-skill 1]<br>[Sub-skill 2] | [Why] |
| 3 | [Title] | [Sub-skill 1]<br>[Sub-skill 2] | [Why] |
| 4 | [Title] | [Sub-skill 1]<br>[Sub-skill 2] | [Why] |
| 5 | [Title] | [Sub-skill 1]<br>[Sub-skill 2] | [Why] |
| 6 | [Title] | [Sub-skill 1]<br>[Sub-skill 2] | [Why] |

**Coaching Support:** Available after Session 1. [Specific note.]

---

[REPEAT employee block for EACH person mentioned]

---

*Ready to move forward? Reach out to your Bundle partner to confirm which option fits best and get these learners started.*

CRITICAL STAGE 5 FORMAT RULES:
- ALWAYS produce BOTH Option A (4 sessions) AND Option B (6 sessions) per person
- Skill Focus: sub-skills ONE PER LINE separated by <br> — NEVER comma-separated
- "Why This Session": reference specific things the user told you. NEVER generic.
- Profile table uses "Growth Opportunities" — NOT "Weaknesses" or "Growth Areas"
- Session 1 MUST be a relational opener in BOTH options
- Include [DATA: num_sessions=N] with the actual number from their selection

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
        ('| # |' in ai_reply and 'option a' in ai_lower) or
        (all(p in ai_lower for p in ['option a', 'option b', '| # |']))
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

def generate_fallback_suggestions(ai_message):
    """
    Generates 3-4 short (2-4 word) suggestions that actually match what the AI just said.
    For transitional/loading messages, returns instant acknowledgement replies.
    For everything else, makes a fast dedicated AI call.
    """
    msg_lower = ai_message.lower()

    # Transitional messages — no AI call needed, return instant acknowledgements
    _transitional = [
        'please hold on', 'hold on', "i'll analyze", "i'll map",
        "i'll now", 'let me analyze', 'let me map', 'let me review',
        'analyzing your', 'mapping your', 'give me a moment',
        'just a moment', 'one moment', 'processing', 'please wait',
    ]
    if any(phrase in msg_lower for phrase in _transitional):
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

    q_type = detect_question_type(raw)
    ai_reply, ai_suggestions = parse_suggestions(raw)

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
        max_tokens=3500,
        temperature=0.7,
    )

    raw_reply = response.choices[0].message.content

    # Save structured data BEFORE stripping tags
    save_data_from_tag(run, user_message, raw_reply)

    # Detect question type for fixed suggestions
    q_type = detect_question_type(raw_reply)

    # Strip tags (DATA + SUGGESTIONS) — ai_suggestions captured but only used as
    # last-resort safety net; we do NOT trust the AI to pick its own correct suggestions
    # for free-form / transitional messages (it often copies stale options).
    ai_reply, ai_suggestions = parse_suggestions(raw_reply)

    if q_type:
        # Known question → use exact pre-defined suggestions every time
        suggestions = STAGE_SUGGESTIONS[q_type]
    else:
        # Unknown / transitional message → always generate fresh contextual suggestions.
        # NEVER use ai_suggestions — the AI copies stale options from earlier messages.
        suggestions = generate_fallback_suggestions(ai_reply)

    history.append({"role": "assistant", "content": ai_reply})
    run.set_chat_history(history)
    detect_and_update_stage(run, user_message, ai_reply)
    run.save()

    return ai_reply, suggestions
