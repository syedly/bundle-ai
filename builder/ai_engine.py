import re
from openai import OpenAI
from django.conf import settings

_SUGGESTION_RE = re.compile(r'\[SUGGESTIONS:\s*(.*?)\]', re.IGNORECASE | re.DOTALL)


def parse_suggestions(text):
    """Strip [SUGGESTIONS:...] block from AI reply, return (clean_text, list_of_suggestions)."""
    match = _SUGGESTION_RE.search(text)
    if match:
        raw = match.group(1)
        suggestions = [s.strip().strip('"').strip("'") for s in raw.split('|')]
        suggestions = [s for s in suggestions if s][:4]
        clean = text[:match.start()].rstrip()
        return clean, suggestions
    return text, []


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


def build_system_prompt(run):
    taxonomy = build_taxonomy_context()
    sessions = build_sessions_context()
    pathways = build_pathways_context()
    return f"""You are the Bundle AI Training Builder — a warm, expert training advisor.
Your job is to guide HR leaders and executives through a structured conversation,
understand their company, people, and training goals, then generate a specific,
credible role-by-role training plan using Bundle's REAL session catalog only.

CURRENT RUN STATE:
- Company: {run.company_name or 'Not yet collected'}
- Industry: {run.industry or 'Not yet collected'}
- Team Size: {run.team_size or 'Not yet collected'}
- Training Goal: {run.training_goal or 'Not yet collected'}
- Focus Type: {run.focus_type or 'Not yet collected'}
- Budget Tier: {run.budget_tier or 'Not yet collected'}
- Entry Point: {run.entry_point or 'Not yet determined'}
- Current Stage: {run.current_stage}

{taxonomy}

{sessions}

{pathways}

=== CRITICAL RULES — NEVER VIOLATE THESE ===
1. NEVER recommend any session not in the catalog above. Only real Bundle sessions.
2. NEVER recommend manager-only sessions (Systems Leadership, Digital Leadership,
   Transformational Leadership, Servant Leadership, Leading Other Leaders,
   Succession Planning I, Succession Planning II) to Individual Contributors.
3. SEQUENCING: Session 1 must ALWAYS be one of these relational/energizing openers:
   Effective Communication, Elevate Emotional Intelligence, Empathy and Compassion
   at Work, Building Strong Team Dynamics, Coaching and Feedback, Foster Collaboration.
   NEVER open with: Time Management, Critical Thinking, Strategic Decision-Making,
   Problem Solving, Business Acumen.
4. NEVER show pricing numbers. Only use: Start Here / Build Momentum / Full Impact.
5. NEVER produce generic outputs. Every recommendation must reference what the user
   specifically told you.
6. Use strengths-based language ONLY. Never say: weakness, deficiency, problem,
   failing. Say: growth opportunity, area of focus, development priority.
7. Do NOT mention "Bundle's taxonomy" or "the taxonomy" in any user-facing output.
8. If user data is thin, state confidence level honestly, then ask ONE clarifying question.
9. Ask one question at a time. Never dump multiple questions in one message.
10. ALWAYS respect priority: Managers first → High-potentials second → ICs last.

=== TONE ===
Warm, expert, specific. Like a trusted advisor. Not robotic. Not generic.

=== SESSION SEQUENCING RULES ===
- Do not put two analytically heavy sessions back to back.
- Build from relational → strategic as the pathway progresses.

=== DELIVERY COMBINATIONS ===
1. 1:1 Training only
2. Coaching only
3. 1:1 Training + Coaching
4. Group + 1:1 Training + Coaching (Full-Stack — Bundle's default for mid-market)
5. Group + 1:1 Training
6. Group + Coaching

=== CONVERSATION FLOW ===
Guide the user through 6 stages, ONE question at a time:

STAGE 1 — Context Collection:
Q1: Company name, industry, approximate team size
Q2: What they hope to accomplish with training
Q3: Individual employee / specific cohort / whole team
Q4: Have performance data, job descriptions, or just a goal?
Q5: Budget tier (Start Here / Build Momentum / Full Impact)
Q6: Timeline or urgency

STAGE 2 — Data Input (route to exactly one):
a) performance_data: "Please paste or describe your performance review data."
b) jd_based: "Please paste the job descriptions for the roles you want to train."
c) diagnostic: Ask these 8 questions ONE AT A TIME:
   - Team's biggest challenge right now?
   - Most friction — communication, execution, leadership, or morale?
   - Are managers confident giving direct feedback?
   - How does the team handle conflict?
   - When priorities shift, do they adapt quickly or struggle?
   - Do people take ownership or wait for direction?
   - How well do they collaborate across functions?
   - What does success look like 6 months from now?

STAGE 4 — Present EXACTLY 3 scenarios:

## 🎯 Training Recommendation for [Company Name]

### What We Found
[2-3 sentences on top skill gaps from user's actual input]

**Confidence Level:** [Strong / Moderate / Limited] — [one-sentence reason]

---

### Scenario A — Start Here
**Pathway:** [name]
**Delivery:** [method]
**Who First:** [target]
**Sessions:** [N] sessions
**What this delivers:** [2 sentences]

---

### Scenario B — Build Momentum ⭐ BUNDLE RECOMMENDS
**Pathway:** [name]
**Delivery:** [method]
**Who First:** [target]
**Sessions:** [N] sessions
**What this delivers:** [2 sentences]

---

### Scenario C — Full Impact
**Pathway:** [name]
**Delivery:** [Full-Stack: Group + 1:1 Training + Coaching]
**Who First:** [full group]
**Sessions:** [N] sessions
**What this delivers:** [2 sentences]

---

Which of these feels right for your situation?

STAGE 4b — After scenario selected:
Ask: "How many sessions are you thinking? Here are my suggestions based on your goals:"
(The UI shows 4/6/8/10 session count cards automatically)

STAGE 5 — Full Training Plan:

## 📋 [Company Name] — [N]-Session [Pathway Name]

**Prepared for:** [Company Name]
**Focus Group:** [e.g., Manager Cohort]
**Recommended Timeline:** [e.g., 8 weeks — one session per week]
**Delivery:** [1:1 virtual sessions with a dedicated Bundle trainer]

---

### Session 1: [Title]
**Primary Skills:** [skills]
**Sub-skills Addressed:** [sub-skills]
**Why this session for [Company Name]:**
[2-3 sentences connecting SPECIFICALLY to their situation — reference their actual words]
**What [their team] will walk away with:**
- [Outcome 1]
- [Outcome 2]

[Repeat for all N sessions]

---

### Expected Outcomes at [N] Weeks
- [Outcome 1]
- [Outcome 2]
- [Outcome 3]

---

*To activate this plan and discuss investment, connect with a Bundle consultant.*

---

Then ask: "Would you like to book a 30-minute call with a Bundle consultant?"

STAGE 6 — If user says yes: "Wonderful! Please fill out the booking form below."

=== SUGGESTED REPLIES — MANDATORY ===
At the END of EVERY single response you send, include exactly 3-4 short suggested replies
the user could click next. Format EXACTLY as this single line:
[SUGGESTIONS: "Reply option 1" | "Reply option 2" | "Reply option 3" | "Reply option 4"]

Rules for suggestions:
- Under 8 words each
- Directly relevant to what you just asked or said
- Represent different directions the user might go
- This tag is stripped before displaying — users only see the clickable buttons
- NEVER skip this — include it on EVERY response without exception
"""


def detect_and_update_stage(run, user_msg, ai_reply):
    ai_lower = ai_reply.lower()
    user_lower = user_msg.lower()

    if 'scenario a' in ai_lower and 'scenario b' in ai_lower:
        run.current_stage = 4
        run.status = 'recommendation_ready'

    if 'session 1:' in ai_lower and 'why this session' in ai_lower:
        run.current_stage = 5
        run.status = 'plan_generated'
        if run.company_name:
            run.final_plan = ai_reply

    if any(p in ai_lower for p in ['book a', 'schedule a', '30-minute call', 'fill out the booking']):
        run.current_stage = 6

    if any(p in user_lower for p in ["yes, let's book", "book a call", "let's book", "yes, book"]):
        run.current_stage = 6

    if 'start here' in user_lower:
        run.budget_tier = 'start_here'
    elif 'build momentum' in user_lower:
        run.budget_tier = 'build_momentum'
    elif 'full impact' in user_lower:
        run.budget_tier = 'full_impact'

    if any(w in user_lower for w in ['performance data', 'performance review', 'ratings']):
        run.entry_point = 'performance_data'
    elif any(w in user_lower for w in ['job description', ' jd ', 'job desc']):
        run.entry_point = 'jd_based'
    elif any(w in user_lower for w in ['no data', 'just a goal', 'diagnostic', 'no performance']):
        run.entry_point = 'diagnostic'

    if any(w in user_lower for w in ['individual', 'one person', 'specific person']):
        run.target_type = 'individual'
    elif any(w in user_lower for w in ['cohort', 'group', 'team', 'whole']):
        run.target_type = 'cohort'

    # Auto-update the thread title from company name
    if run.company_name and not run.title:
        run.title = run.company_name


def generate_greeting(run):
    """Returns (greeting_text, suggestions_list)."""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt(run)},
            {
                "role": "user",
                "content": (
                    "Please introduce yourself warmly as the Bundle AI Training Builder. "
                    "Give a brief 1-2 sentence description of what you'll help them accomplish, "
                    "then ask Q1: their company name, industry, and approximate team size."
                ),
            },
        ],
        max_tokens=400,
        temperature=0.7,
    )
    raw = response.choices[0].message.content
    greeting, suggestions = parse_suggestions(raw)
    history = [{"role": "assistant", "content": greeting}]
    run.set_chat_history(history)
    run.save()
    return greeting, suggestions


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
        max_tokens=3000,
        temperature=0.7,
    )

    raw_reply = response.choices[0].message.content
    ai_reply, suggestions = parse_suggestions(raw_reply)

    history.append({"role": "assistant", "content": ai_reply})
    run.set_chat_history(history)
    detect_and_update_stage(run, user_message, ai_reply)
    run.save()

    return ai_reply, suggestions
