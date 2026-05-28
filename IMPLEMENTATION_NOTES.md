# Bundle AI Training Builder — Implementation Notes
> Complete system reference: architecture, taxonomy, employee analysis, and AI decision logic.
> Built from: Tech Stack PDF, Recommender Brief, Performance Reviews, Pathway Plans, Competency Framework, Human-Centered Skills Taxonomy.

---

## 1. System Architecture Overview

### 4 AI Agents (in sequence)

| Agent Key | Stages | Role |
|---|---|---|
| `context_collector` | 1–2 | Asks 14 questions to capture company, learner, and data context |
| `analyzer` | 3–4 | Reads all uploaded data; produces 3 delivery scenarios with confidence scoring |
| `plan_generator` | 5 | Generates full session-by-session training plan with sequencing rationale |
| `general` | 6 + fallback | Handles booking flow and follow-up questions |

### Agent Routing Logic
- Stage 1–2 → `context_collector`
- Stage 3–4 → `analyzer`
- Stage 5 (no plan yet) → `plan_generator`
- Stage 6 + all other → `general`

### Data Entry Paths (Stage 2)
- **Path A — Performance Data**: Upload/paste performance reviews, 360s, manager feedback
- **Path B — Job Description**: Paste JDs to infer skill gaps by role
- **Path C — Diagnostic**: AI asks 8 structured diagnostic questions when no data exists

### Deliverables
- **Stage 4 (Analyzer output)**: 3 delivery scenarios per person — confidence level, growth opportunities with evidence, recommended sessions, delivery options (1:1 Training + Coaching / Training Only / Coaching Only)
- **Stage 5 (Plan Generator output)**: Full session-by-session plan with skill focus, sequencing rationale, and coaching touchpoints per person
- **Stage 6**: Booking confirmation + PDF export

---

## 2. Skills Taxonomy

### Primary Skills (17 total — Human-Centered Skills Taxonomy)

| # | Primary Skill | Core Definition |
|---|---|---|
| 1 | Empathy | Understanding and sharing the feelings of others |
| 2 | Communication | Conveying information clearly, authentically, and effectively across contexts |
| 3 | Collaboration | Working effectively with others to achieve shared goals |
| 4 | Teamwork | Working cooperatively within a team through mutual support |
| 5 | Problem Solving | Analyzing and resolving complex issues using structured and creative thinking |
| 6 | Creativity | Generating novel ideas and solutions through imagination and divergent thinking |
| 7 | Adaptability | Adjusting behaviors, mindsets, and approaches to thrive in changing environments |
| 8 | Leadership | Guiding, inspiring, and developing others toward individual and collective goals |
| 9 | Emotional Intelligence | Recognizing, understanding, and managing one's own and others' emotions |
| 10 | Resilience | Recovering from setbacks and maintaining momentum under pressure |
| 11 | Critical Thinking | Applying logical and evaluative thinking to assess information and solve problems |
| 12 | Decision Making | Making sound, timely, well-reasoned choices based on data, context, and values |
| 13 | Time Management | Prioritizing tasks and organizing effort to deliver consistent results |
| 14 | Cultural Competence | Working effectively with individuals from diverse backgrounds and perspectives |
| 15 | Conflict Resolution | Addressing conflicts constructively in a relationship-preserving way |
| 16 | Systems Leadership | Guiding complex systems by understanding interdependencies and aligning action to strategy |
| 17 | Interpersonal Dexterity | Influencing and navigating relationships at and across levels of leadership |

### Sub-Skills by Primary Skill

**Empathy**: Active Listening | Perspective-taking | Emotional Awareness | Non-Verbal Communication | Cultural Sensitivity

**Communication**: Verbal Communication | Written Communication | Non-Verbal Communication | Public Speaking | Storytelling | Persuasion | Confidence | Gravitas | Questioning Techniques | Influence

**Collaboration**: Teamwork | Conflict Resolution | Task Delegation | Communication Within a Team | Building Trust | Project Management

**Teamwork**: Collaboration | Cooperation | Shared Accountability | Team Cohesion | Cross-Functional Collaboration

**Problem Solving**: Analytical Thinking | Decision-Making | Creativity and Innovation | Research Skills | Critical Thinking | Data Analysis | Financial Literacy | Creative Problem-Solving | Problem Analysis

**Creativity**: Ideation | Brainstorming | Design Thinking | Problem-Solving Through Creativity

**Adaptability**: Change Management | Flexibility | Stress Management | Resilience | Learning Agility

**Leadership**: Vision-Setting | Motivation | Delegation | Coaching and Mentoring | Feedback Techniques | Conflict Resolution | Decision-Making | Leadership through Influence | Credibility | Trustworthiness | Feedback | Inspiration | Ethical Leadership | Stewardship | Building Community | Psychological Safety | Empowering and Developing Leaders | Ethical Influence

**Emotional Intelligence**: Self-Awareness | Self-Regulation | Social Awareness | Relationship Management

**Resilience**: Stress Management | Optimism | Perseverance | Adaptation to Change

**Critical Thinking**: Analytical Reasoning | Problem Analysis | Logical Reasoning | Inference | Evaluation of Evidence

**Decision Making**: Risk Assessment | Data-Driven Decision-Making | Ethical Decision-Making | Prioritization | Analytical Thinking

**Time Management**: Prioritization | Procrastination Management | Task Organization | Goal Setting | Productivity Techniques

**Cultural Competence**: Cultural Sensitivity | Inclusion | Diversity Awareness | Cross-Cultural Communication | Perspective-Taking

**Conflict Resolution**: Mediation | Negotiation | De-escalation | Active Listening | Collaborative Problem-Solving

**Systems Leadership**: Systems Thinking | Collaborative Leadership | Coalition Building | Strategic Alignment | Strategic Delegation | Evaluation and Continuous Improvement

**Interpersonal Dexterity**: Influencing and Persuading Other Leaders | Conflict Resolution Among Leaders

---

## 3. Session Catalog with Full Skill Mapping (34 Sessions)

| # | Session Title | Primary Skills | Sub-skills | Roles |
|---|---|---|---|---|
| 1 | Effective Communication | Communication, Empathy | Active Listening, Verbal Communication, Non-Verbal Communication | Mgr, NM, IC |
| 2 | Building Strong Team Dynamics | Teamwork, Collaboration | Building Trust, Conflict Resolution, Communication Within a Team, Team Cohesion | Mgr, NM, IC |
| 3 | Managing Stress in the Workplace | Adaptability, Resilience | Stress Management, Resilience, Perseverance, Adaptation to Change | Mgr, IC |
| 4 | Problem Solving | Problem Solving | Problem Analysis, Analytical Thinking, Decision-Making, Creative Problem-Solving | Mgr, NM, IC |
| 5 | Time Management | Time Management, Decision Making | Prioritization, Procrastination Management, Task Organization, Goal Setting | Mgr, IC |
| 6 | Critical Thinking | Critical Thinking, Problem Solving | Analytical Reasoning, Logical Reasoning, Problem Analysis, Evaluation of Evidence | Mgr, NM, IC |
| 7 | Elevate Emotional Intelligence | Emotional Intelligence, Empathy | Self-Awareness, Social Awareness, Relationship Management, Self-Regulation | Mgr, NM, IC |
| 8 | Resilience Leadership | Resilience | Stress Management, Perseverance, Optimism, Adaptation to Change | Mgr, NM, IC |
| 9 | Empathy and Compassion at Work | Empathy, Emotional Intelligence | Perspective-taking, Emotional Awareness, Cultural Sensitivity, Active Listening | Mgr, NM, IC |
| 10 | Develop a Culture of Inclusion | Cultural Competence, Empathy | Cultural Sensitivity, Perspective-taking, Inclusion, Diversity Awareness | Mgr, IC, NM |
| 11 | Coaching and Feedback | Leadership, Communication | Coaching and Mentoring, Feedback Techniques, Active Listening, Feedback | Mgr, NM, IC |
| 12 | Conflict Resolution and Management | Conflict Resolution, Emotional Intelligence | Mediation, Negotiation, Collaborative Problem-Solving, De-escalation | Mgr, NM, IC |
| 13 | Foster Collaboration | Collaboration, Teamwork | Communication Within a Team, Building Trust, Task Delegation, Shared Accountability | Mgr, IC, NM |
| 14 | Motivating People for Performance | Leadership | Motivation, Vision-Setting, Inspiration, Ethical Leadership | Mgr, IC, NM |
| 15 | Managing Change | Adaptability | Change Management, Flexibility, Resilience, Learning Agility | Mgr, NM, IC |
| 16 | Strategic Decision-Making | Decision Making, Problem Solving | Risk Assessment, Data-Driven Decision-Making, Ethical Decision-Making, Analytical Thinking | Mgr, NM, IC |
| 17 | Creative Thinking and Innovation | Creativity, Problem Solving | Ideation, Brainstorming, Design Thinking, Creativity and Innovation | Mgr, NM, IC |
| 18 | Productivity and Organizational Skills | Time Management, Collaboration | Task Delegation, Project Management, Productivity Techniques, Goal Setting | Mgr, IC |
| 19 | Executive Presence | Leadership, Communication | Credibility, Gravitas, Influence, Trustworthiness | Mgr, IC, NM |
| 20 | Leadership Essentials | Leadership | Vision-Setting, Delegation, Decision-Making, Ethical Leadership, Leadership through Influence | Mgr, NM, IC |
| 21 | Systems Leadership | Systems Leadership | Systems Thinking, Collaborative Leadership, Strategic Alignment, Coalition Building | **Mgr only** |
| 22 | Interviewing with Impact | Communication, Empathy, Decision Making | Confidence, Active Listening, Questioning Techniques, Non-Verbal Communication | Any |
| 23 | Leading Difficult Conversations | Communication, Empathy | Empathy, Conflict Resolution, Emotional Intelligence, Relationship Management | Mgr, NM, IC |
| 24 | Digital Leadership | Leadership, Communication, Collaboration | Vision-Setting, Communication Within a Team, Building Trust, Delegation | **Mgr only** |
| 25 | Negotiation and Influence | Communication, Conflict Resolution | Influence, Negotiation, Persuasion, Credibility, Active Listening | Mgr, IC |
| 26 | Maximizing the Impact of 1:1 Conversations | Communication, Emotional Intelligence, Empathy | Questioning Techniques, Relationship Management, Feedback, Perspective-taking | Mgr, NM, IC |
| 27 | Business Acumen | Problem Solving, Critical Thinking, Decision Making | Financial Literacy, Data Analysis, Research Skills, Analytical Thinking | Mgr, IC |
| 28 | Transformational Leadership | Leadership, Communication | Inspiration, Vision-Setting, Empowering and Developing Leaders, Building Community | **Mgr only** |
| 29 | Leading Other Leaders | Leadership, Interpersonal Dexterity, Systems Leadership | Influencing and Persuading Other Leaders, Conflict Resolution Among Leaders, Strategic Delegation | **Mgr only** |
| 30 | Storytelling and Persuasion | Communication | Storytelling, Persuasion, Confidence, Gravitas | IC, Mgr |
| 31 | Public Speaking | Communication | Public Speaking, Confidence, Non-Verbal Communication, Gravitas | IC, Mgr |
| 32 | Servant Leadership | Leadership, Emotional Intelligence | Psychological Safety, Empowering and Developing Leaders, Building Community, Stewardship | **Mgr only** |
| 33 | Succession Planning I | Problem Solving, Leadership, Systems Leadership | Strategic Delegation, Evaluation and Continuous Improvement, Systems Thinking | **Mgr only** |
| 34 | Succession Planning II | Leadership, Collaboration, Communication | Empowering and Developing Leaders, Building Community, Coalition Building | **Mgr only** |

---

## 4. Official Pathways

### Manager Pathways

| Pathway | Sessions |
|---|---|
| **Manager Foundations** | Effective Communication → Building Strong Team Dynamics → Elevate Emotional Intelligence → Problem Solving → Critical Thinking → Executive Presence |
| **Strategic Leadership** | Leadership Essentials → Empathy and Compassion at Work → Resilience Leadership → Conflict Resolution and Management → Strategic Decision-Making → Creative Thinking and Innovation |
| **Leading Teams to Success** | Develop a Culture of Inclusion → Motivating People for Performance → Coaching and Feedback → Managing Change → Leading Difficult Conversations → Maximizing the Impact of 1:1 Conversations |
| **Driving Execution** | Business Acumen → Time Management → Productivity and Organizational Skills → Managing Stress in the Workplace → Negotiation and Influence → Foster Collaboration |
| **Future-Forward Leadership** | Digital Leadership → Systems Leadership → Transformational Leadership → Servant Leadership → Leading Other Leaders |

### Other Role Pathways

| Pathway | Role | Sessions |
|---|---|---|
| **New Manager Foundations** | New Manager | Effective Communication → Building Strong Team Dynamics → Elevate EI → Problem Solving → Critical Thinking → Executive Presence |
| **Essential Workplace Skills** | Individual Contributor | Effective Communication → Building Strong Team Dynamics → Elevate EI → Resilience Leadership → Empathy and Compassion at Work → Foster Collaboration |

---

## 5. Employee Analysis — MonticelloAM (2025 Review Cycle)

### Employee 1 — Asset Manager, Healthcare Originations

**Role Type**: Manager (works across asset management and originations)

**Strengths identified**:
- Relationship management with external partners
- Technology initiative leadership
- External partner coordination

**Growth opportunities (from review)**:
- Deliverable consistency (work submitted without thorough final review; analyses requiring multiple follow-ups)
- Giving direct feedback to team members (avoids difficult conversations with reports)
- Confidence as independent deal decision-maker (relies too heavily on validation)

**Career trajectory**: Deal leadership end-to-end; growing senior role with external-facing responsibility

**Root cause**: Self-awareness gap — the behavioral patterns (indirect feedback, incomplete work, accountability hesitancy) all trace to Emotional Intelligence deficits, not skill knowledge gaps alone.

**Recommended Technique Sequence**:

| Option | Sessions | Sequence Logic |
|---|---|---|
| 4-session | Elevate EI → Coaching and Feedback → Time Management → Strategic Decision-Making | Foundation first: EI unlocks all behavioral change. Feedback skills next (direct talent development). Execution systems (deliverable consistency). Deal confidence last. |
| 6-session | Elevate EI → Coaching and Feedback → Leading Difficult Conversations → Time Management → Strategic Decision-Making → Conflict Resolution and Management | Sessions 2+3 work as a pair: feedback skill needs the ability to stay in hard conversations. Conflict Resolution added for Greystone relationship management. |
| 8-session | Same 6 + Motivating People for Performance → Executive Presence | Prepares for expanded scope: motivating team as deal leader. Presence for external deal settings. |

**Why these techniques for this person**:
- Start with **Elevate Emotional Intelligence** because both self-assessment and manager review point to self-awareness as the root: indirect feedback, work not fully reviewed, accountability habits developing.
- **Coaching and Feedback** immediately after — translates EI self-awareness into practical feedback skills with team members.
- **Leading Difficult Conversations** (in 6+) — coaching skill without conversation stamina is incomplete; they need the courage to stay in hard exchanges.
- **Time Management** — "analyses submitted without final review" and "requested work requiring multiple follow-ups" point to execution systems, not motivation issues.
- **Strategic Decision-Making** — learner's own stated goal: front-end deal ownership and independent credit judgment. This is the session for that.

---

### Employee 2 — Asset Manager, Transitioning to Underwriting

**Role Type**: IC + emerging manager (managing large portfolio, stepping into origination)

**Strengths identified**:
- Portfolio ownership and depth
- Cross-team contribution and proactive participation
- Initiative on new programs

**Growth opportunities (from review)**:
- Stakeholder communication and timeliness (delayed responses, unclear expectation-setting)
- Personal accountability (outcomes not owned when tasks are shared)
- Prioritization under competing demands (large portfolio + underwriting transition)

**Career trajectory**: Full transition to underwriting; owning deals from term sheet through close; direct borrower engagement

**Root cause**: Operational system gap — the issues (delayed communication, unclear expectations, prioritization failures) point to execution systems and communication protocols, not motivation. Self-awareness supports but isn't the root.

**Recommended Technique Sequence**:

| Option | Sessions | Sequence Logic |
|---|---|---|
| 4-session | Effective Communication → Time Management → Productivity and Organizational Skills → Elevate EI | Start where the manager review points: communication and timeliness. Then execution systems. EI last — addresses self-awareness dimension of accountability. |
| 6-session | Same 4 + Coaching and Feedback → Problem Solving | Coaching added: this person already oversees junior AMs — structure that work. Problem Solving: underwriting transition is live, analytical foundation needed now. |
| 8-session | Same 6 + Maximizing 1:1 Conversations → Negotiation and Influence | 1:1s for borrower/stakeholder engagement. Negotiation for independent deal leadership — the end-goal of this transition. |

**Why these techniques for this person**:
- Start with **Effective Communication** — manager review is explicit: delayed stakeholder responses and unclear expectation-setting are the lead growth areas. This session addresses both directly.
- **Time Management** before EI — the prioritization failures are operational; managing a large portfolio while transitioning is a systems problem first, a mindset problem second.
- **Productivity and Organizational Skills** — self-assessment names delegation as a specific target; review adds that ownership must remain with this person even when tasks are shared.
- **Elevate EI** at position 4 — the self-awareness dimension of accountability is real, but it follows (not precedes) the operational fixes.
- **Negotiation and Influence** at position 8 — the career end-goal is independent deal leadership. Negotiation and credibility in multi-stakeholder settings is the final skill unlock.

---

## 6. Employee Analysis — Zelis LEAD Program (Director Level, 30 Participants)

**Population**: 30 director-level leaders in a high-growth, fast-scaling company

**Context**: Post-coaching cohort — coaching was highest-rated element; now building the skills learning component to match that standard.

**Organizational signal**: Directors need to operate across boundaries (not just within function) as Zelis scales. Change leadership is less a nice-to-have, more a core requirement.

**Recommended Technique Sequence**:

| Option | Sessions | Sequence Logic |
|---|---|---|
| 6-session | Leadership Essentials → Motivating People for Performance → Strategic Decision-Making → Systems Leadership → Leading Difficult Conversations → Coaching and Feedback | Shared framework first. Vision + motivation skills. Decision-making under pressure. Lift view to organizational level. Hard conversation skills. Coaching their own teams. |
| 8-session | Same 6 + Managing Change → Executive Presence | Managing Change: core requirement at director level in Zelis's current trajectory. Executive Presence: capstone — everything the cohort worked on, expressed in how they show up. |

**Sequence rationale for director level**:
- Leadership Essentials opens with a shared framework — critical for a 30-person cohort to have aligned language before individual work diverges.
- Sessions 2–3 build core business leadership: vision-setting and motivating, then decision-making under pressure.
- Session 4 lifts the view beyond function — Systems Leadership is where directors at Zelis need to operate.
- Sessions 5–6 address the interpersonal skills Zelis called out directly in discovery: difficult conversations and coaching.
- Executive Presence as capstone in 8-session is ideal — it synthesizes everything into presence and influence.

---

## 7. Employee Analysis — Maui Humane Society (3-Pathway Cross-Organization Program)

**Context**: Building common language and consistent norms across the organization. Three distinct audiences; intentional session overlap to create shared vocabulary.

**Shared sessions across all three groups**: Elevate Emotional Intelligence, Effective Communication, Leading Difficult Conversations (intentional — these form the connective tissue).

**Managers and ICs additionally share**: Conflict Resolution and Management.

### Pathway 1 — Senior Leaders (C-Suite and Directors) — 8 Sessions
Elevate EI → Leadership Essentials → Effective Communication → Managing Change → Leading Difficult Conversations → Servant Leadership → Strategic Decision-Making → Transformational Leadership

**Technique logic**: Start with EI and leadership identity. Communication next (sharpening what they already do). Change navigation (organizational context). Hard conversations (most avoided by senior leaders). Servant Leadership (philosophy for this org's culture). Strategic decision-making under uncertainty. Close with Transformational Leadership — legacy and long-term impact.

### Pathway 2 — Managers and Supervisors — 8 Sessions
Elevate EI → Effective Communication → Leadership Essentials → Building Strong Team Dynamics → Coaching and Feedback → Conflict Resolution and Management → Managing Change → Maximizing 1:1 Conversations

**Technique logic**: Foundation in EI and communication before introducing leadership identity. Team dynamics and trust-building are core to this audience's daily work. Coaching/feedback and conflict resolution are the practical management skills that follow. Managing Change equips them to support their teams through transitions. 1:1 Conversations closes as a repeatable, concrete format they'll use every week.

### Pathway 3 — Individual Contributors and Project Managers — 8 Sessions
Elevate EI → Effective Communication → Problem Solving → Conflict Resolution and Management → Leading Difficult Conversations → Time Management → Foster Collaboration → Productivity and Organizational Skills

**Technique logic**: EI and communication open (same foundation as other groups — building common language). Problem Solving is the IC's core tool. Conflict resolution and difficult conversations are paired — ICs navigate peer-level friction most often. Time Management and Productivity are sequenced after the relational skills, reinforcing their relevance to how the IC actually works. Collaboration closes with shared accountability.

---

## 8. AI Decision-Making Logic — How the AI Selects Techniques

### Step 1: Assess Data Quality → Set Confidence Level
- **Strong confidence**: Full performance review + manager feedback + self-assessment → rich, specific data
- **Moderate confidence**: Partial data (one review, one source) or JD-based inference
- **Limited confidence**: Diagnostic questions only (Path C) — patterns exist but no direct feedback data

### Step 2: Identify Root Cause Category
The AI classifies the core problem before selecting sessions:

| Root Cause | Signal Pattern | Primary Starting Session |
|---|---|---|
| Self-awareness / EI gap | Indirect feedback, accountability habits developing, interpersonal friction | Elevate Emotional Intelligence (Session 7) |
| Communication / Expectation gap | Delayed responses, unclear expectations, stakeholder misalignment | Effective Communication (Session 1) |
| Execution / Systems gap | Missed deadlines, work requiring re-do, prioritization failures | Time Management (Session 5) |
| Feedback / Talent development gap | Avoids hard feedback, doesn't develop direct reports | Coaching and Feedback (Session 11) |
| Decision-making / Confidence gap | Over-relies on validation, avoids independent judgment | Strategic Decision-Making (Session 16) |
| Change / Adaptability gap | Resistance to change, team instability during transitions | Managing Change (Session 15) |
| Executive presence / influence gap | Not commanding the room, too tactical in senior settings | Executive Presence (Session 19) |
| Conflict avoidance gap | Escalating unresolved tension, avoidance of hard conversations | Leading Difficult Conversations (Session 23) |
| Collaboration / delegation gap | Siloed work, doesn't delegate, ownership confusion | Productivity and Organizational Skills (Session 18) |
| Strategic / systems gap | Too function-focused, not operating at organizational level | Systems Leadership (Session 21) |

### Step 3: Apply Sequencing Principles
1. **Foundation first**: EI or Communication almost always open — they unlock everything else
2. **Behavioral pairs**: Coaching + Difficult Conversations work together; don't recommend one without the other when both gaps are present
3. **Operational before aspirational**: Fix execution systems (time management, delegation) before adding advanced leadership skills
4. **Career-stage match**: Match session sophistication to the learner's actual next role, not current one
5. **Role filter**: Manager-only sessions (21, 24, 28, 29, 32, 33, 34) must never be recommended to ICs
6. **Capstone logic**: Executive Presence or Transformational Leadership best placed at end — they synthesize prior learning

### Step 4: Select Session Count
| Count | Label | When to Recommend |
|---|---|---|
| 4 sessions | Start Here | Single focused gap; budget or timeline constraints; first engagement to test fit |
| 6 sessions | Build Momentum | 2–3 connected gaps; standard structured program; most common recommendation |
| 8 sessions | Full Impact | Multiple gaps spanning self-awareness → execution → leadership; career transition; cohort program |

### Step 5: Select Delivery Method
| Method | When to Recommend |
|---|---|
| 1:1 Training + Coaching | Strong confidence; specific, nuanced gaps; person needs real-time practice between sessions |
| 1:1 Training Only | Moderate confidence; skill-building without behavioral coaching component; budget sensitivity |
| Coaching Only | Very specific situation awareness needed; no structured skill gap identified; individual support only |

---

## 9. Competency Framework Mapping (Competency Master — Organizational Context)

The organization-level competency framework uses **Growth Attributes** as the organizing structure. The AI can use this to map client competency language to Bundle sessions.

### Growth Attribute → Bundle Session Mapping

| Growth Attribute | Core Competencies | Best-Fit Bundle Sessions |
|---|---|---|
| **Act Like an Owner** | Culture Ambassador, Business Impact, Accountability & Execution, Results Driven, Initiative & Resourcefulness | Time Management (5), Strategic Decision-Making (16), Leadership Essentials (20), Business Acumen (27) |
| **Adapt to Thrive** | Change Readiness, Growth Mindset, Managing Ambiguity, Learning Agility, Resilience | Managing Change (15), Resilience Leadership (8), Managing Stress (3), Critical Thinking (6) |
| **Challenge the Status Quo** | Continuous Improvement, Curiosity & Problem Solving, Courage & Conviction, Data-Informed Decision Making, Exploration & Experimentation | Problem Solving (4), Creative Thinking and Innovation (17), Strategic Decision-Making (16), Critical Thinking (6) |
| **Collaborate to Win** | Team Orientation, Conflict Management, Influence & Communication, Alignment & Cohesion, Engagement & Belonging | Building Strong Team Dynamics (2), Foster Collaboration (13), Conflict Resolution and Management (12), Negotiation and Influence (25), Effective Communication (1) |
| **Serve with Purpose** | Relationship Management, Compassion & Empathy, Customer Centric, Active Listening, Clear & Critical Thinking | Empathy and Compassion at Work (9), Maximizing 1:1 Conversations (26), Develop a Culture of Inclusion (10), Effective Communication (1) |

---

## 10. Session Sequencing Rules (Enforced in AI Prompts)

### Universal Rules
1. Never recommend manager-only sessions to ICs or NMs
2. Always sequence foundational sessions (EI, Communication) before advanced leadership sessions
3. Never recommend more sessions than the learner's timeline supports
4. Always match session depth level to the learner's placement assessment result
5. Coaching and Feedback and Leading Difficult Conversations should be recommended together when feedback gaps are present
6. Executive Presence and Transformational Leadership are capstone sessions — place them last

### Path A (Performance Data) Rules
- Extract specific behavioral quotes from the review to anchor session selection
- Evidence from manager review takes precedence over self-assessment when they conflict
- Map each identified gap to the root cause category before selecting sessions
- At least one session should directly address the learner's stated career goal

### Path B (JD-Based) Rules
- Identify the gap between current role skills and target role skills
- Select sessions that bridge that skill gap most directly
- Sequence from "current reality" skills to "target role" skills

### Path C (Diagnostic) Rules
- Use the 8 diagnostic answers to infer the most likely root cause pattern
- Bias toward higher confidence recommendations when multiple diagnostic signals align
- Recommend Path A or B data collection if critical gaps remain ambiguous after diagnostics

---

## 11. Placement Assessment Logic

All learners are placed at one of four levels before Session 1:

| Level | Characteristics | AI Implication |
|---|---|---|
| **Foundational** | New to this skill area; needs core concepts and vocabulary | Sessions start with awareness and recognition; lighter application |
| **Intermediate** | Has some experience; can apply in structured settings | Sessions include scenario practice and feedback loops |
| **Advanced** | Consistent application; ready for nuanced contexts | Sessions focus on complex cases, edge cases, stakeholder dynamics |
| **Expert** | Deep mastery; context is developing others or systems-level change | Sessions oriented toward teaching, influencing at scale, strategic application |

Placement is 1:1 and session-specific — a learner can be Advanced in Communication and Foundational in EI simultaneously.

---

## 12. Data Issues Fixed

### What Was Wrong
- `sub_skills_text` field existed in Session model but was never populated — AI had no sub-skill visibility when building training plans
- Several Primary Skills (Teamwork, Time Management, Decision Making, Cultural Competence, Conflict Resolution) had no sub-skills defined in `seed_data.py`
- Sub-skill definitions were missing from all SubSkill records — taxonomy context in system prompt showed names only
- `build_sessions_context()` in `ai_engine.py` did not include sub-skills in the assembled prompt

### What Was Fixed
1. **`seed_data.py`**: All 17 Primary Skills now have sub-skills defined with full definitions from Human-Centered Skills Taxonomy
2. **`seed_data.py`**: All 34 sessions now include `sub_skills_text` (4–5 sub-skills each)
3. **`seed_data.py`**: SubSkill seeding now writes `definition` to each record
4. **`ai_engine.py`**: `build_sessions_context()` now includes sub-skills line per session
5. **`ai_engine.py`**: `build_taxonomy_context()` now includes sub-skill definitions inline

### How to Re-seed
```bash
python manage.py seed_data
```
This clears all existing skills, sub-skills, sessions, and pathways and re-seeds from the corrected data.

---

## 13. Tech Stack Reference (April 2026)

- **Backend**: Django 4.2+ (MVT)
- **AI**: OpenAI API — `gpt-4o` with tool use (submit_ai_analysis, submit_final_plan)
- **Database**: SQLite (local) → scalable to PostgreSQL
- **Frontend**: HTML + CSS + Vanilla JS (no framework)
- **Document parsing**: pypdf, python-docx, openpyxl
- **PDF export**: ReportLab
- **Email**: Django mail + Gmail SMTP
- **Caching**: Django in-memory cache (5-min TTL for prompt sections)
- **Deployment**: WSGI/ASGI compatible; static files via collectstatic
