"""
OpenAI tool definitions and handlers for Bundle deliverable reports.

Flow:
  Context collected → submit_ai_analysis (one call, one block per person)
                    → submit_final_plan  (one call immediately after, one employee block per person)
"""
import json

from django.utils import timezone

from .models import BuilderRun

# ── Tool schemas ───────────────────────────────────────────────────────────────

# Per-person sub-schema reused inside the people array
_PERSON_ANALYSIS_SCHEMA = {
    'type': 'object',
    'properties': {
        'name': {
            'type': 'string',
            'description': 'Person name or "Employee 1" if anonymous.',
        },
        'role_title': {
            'type': 'string',
            'description': 'Their current role / title in one line.',
        },
        'confidence': {
            'type': 'string',
            'enum': ['Strong confidence', 'Moderate confidence', 'Limited confidence'],
        },
        'confidence_rationale': {
            'type': 'string',
            'description': (
                '3-4 sentences. Explain what data was provided (type, specificity, '
                'directness of evidence), what patterns are clearly vs. inferred, '
                'and what additional data would sharpen the recommendation if available. '
                'Be specific — name the document type and the nature of the evidence.'
            ),
        },
        'summary_paragraph': {
            'type': 'string',
            'description': (
                'MINIMUM 4-5 sentences. Open with who this person is and their current '
                'situation. Identify the 2-3 interconnected gaps the data reveals — '
                'quote specific language from the review or conversation. Explain what '
                'the plan is designed to change for this person specifically. '
                'End with what success looks like in their role after the program. '
                'Never write generic filler — name the person and their real context.'
            ),
        },
        'growth_opportunities': {
            'type': 'array',
            'description': '3-4 skill gaps. Each backed by direct quotes and full context.',
            'items': {
                'type': 'object',
                'properties': {
                    'skill_area': {
                        'type': 'string',
                        'description': 'Gap name, e.g. "Time Management".',
                    },
                    'evidence': {
                        'type': 'string',
                        'description': (
                            'MINIMUM 3-4 sentences. (1) Open with a direct quote or '
                            'close paraphrase from the actual review/data that shows '
                            'this gap — always start with the source evidence, not a '
                            'description of it. (2) Explain what this pattern means for '
                            'this person in their specific role. (3) State the business '
                            'or performance consequence if left unaddressed. '
                            'Never write generic evidence — always anchor to actual words '
                            'from the data the user provided.'
                        ),
                    },
                },
                'required': ['skill_area', 'evidence'],
            },
            'minItems': 3,
            'maxItems': 4,
        },
        'recommended_delivery': {
            'type': 'string',
            'enum': ['1:1 Training + Coaching', '1:1 Training Only', 'Coaching Only'],
            'description': 'Delivery method the AI chose for this person based on their gaps.',
        },
        'recommended_sessions': {
            'type': 'integer',
            'enum': [4, 6, 8],
            'description': (
                'Session count chosen by the AI: 4 (Start Here), '
                '6 (Build Momentum), or 8 (Full Impact).'
            ),
        },
        'delivery_options': {
            'type': 'array',
            'description': 'All 3 delivery options. Mark one as recommended.',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'recommended': {'type': 'boolean'},
                    'description': {
                        'type': 'string',
                        'description': (
                            '3-4 sentences specific to THIS person and their gaps. '
                            'Explain why this delivery method fits their situation, '
                            'what it enables that the others would not, and what the '
                            'tangible difference would be in their day-to-day role. '
                            'Never write generic delivery method descriptions.'
                        ),
                    },
                    'sessions_label': {
                        'type': 'string',
                        'description': 'e.g. "6 sessions · includes coaching support"',
                    },
                },
                'required': ['name', 'recommended', 'description', 'sessions_label'],
            },
            'minItems': 3,
            'maxItems': 3,
        },
        'depth_options': {
            'type': 'object',
            'properties': {
                'full_outcome_paragraph': {
                    'type': 'string',
                    'description': (
                        '4-5 sentences. Describe what this person looks like after a full '
                        '8-session program — name specific behavioural changes, measurable '
                        'outcomes, and how their role or relationships change. '
                        'Reference their actual gaps from the data. Be concrete: what '
                        'meetings do they run differently? How do peers and stakeholders '
                        'experience them differently? What decisions do they make with '
                        'more confidence? Never write generic "improved leadership" filler.'
                    ),
                },
                'tiers': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'sessions': {'type': 'integer'},
                            'tagline': {'type': 'string'},
                            'description': {
                                'type': 'string',
                                'description': (
                                    '3-4 sentences. Name the specific sessions this tier '
                                    'covers, what gaps they address, and what the person '
                                    'gains from completing this tier. If this is not the '
                                    'full program, name what is left out and the consequence '
                                    'of stopping here. Specific to this person — not generic.'
                                ),
                            },
                        },
                        'required': ['name', 'sessions', 'tagline', 'description'],
                    },
                    'minItems': 3,
                    'maxItems': 3,
                },
                'start_small_paragraph': {
                    'type': 'string',
                    'description': (
                        '3-4 sentences. Name the specific gaps and sessions that the '
                        '4-session Start Here tier does NOT cover. Explain the consequence '
                        'for this person of leaving those gaps unaddressed. Be direct — '
                        'what remains at risk in their role if they stop at 4 sessions?'
                    ),
                },
            },
            'required': ['full_outcome_paragraph', 'tiers', 'start_small_paragraph'],
        },
        'sequencing_logic': {
            'type': 'string',
            'description': (
                'MINIMUM 4-6 full paragraphs. This is the "Why we built it this way" '
                'narrative. Paragraph 1: the root cause pattern — what the data shows '
                'as the deepest underlying gap and why it has to be addressed first. '
                'Paragraph 2: why the opening session was chosen — what it unlocks. '
                'Paragraph 3: how sessions 2-4 build on each other — the skill arc. '
                'Paragraph 4: what the back half of the program targets and why only '
                'after the foundation is laid. Paragraph 5: how the full sequence '
                'connects to this person\'s role, their next career stage, and the '
                'business impact their manager/HR described. '
                'NEVER write generic "we start with communication because it\'s foundational" — '
                'name this person, their specific review language, and their exact situation.'
            ),
        },
    },
    'required': [
        'name', 'role_title', 'confidence', 'confidence_rationale',
        'summary_paragraph', 'growth_opportunities',
        'recommended_delivery', 'recommended_sessions',
        'delivery_options', 'depth_options', 'sequencing_logic',
    ],
}

SUBMIT_AI_ANALYSIS_TOOL = {
    'type': 'function',
    'function': {
        'name': 'submit_ai_analysis',
        'description': (
            'Submit the Stage 4 AI Analysis. '
            'If multiple documents were uploaded, include ONE block per person in the people array. '
            'Do NOT paste any of this in chat — put everything in this tool.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'header_title': {
                    'type': 'string',
                    'description': 'Company name, e.g. "Monticello".',
                },
                'people': {
                    'type': 'array',
                    'description': (
                        'One analysis block per person. '
                        '2 documents uploaded → 2 items. '
                        '1 document → 1 item. NEVER combine multiple people into one block.'
                    ),
                    'items': _PERSON_ANALYSIS_SCHEMA,
                    'minItems': 1,
                },
                'chat_message': {
                    'type': 'string',
                    'description': (
                        '1-2 sentences for the chat. '
                        'e.g. "Your recommendation is ready — skill gaps, rationale, '
                        'and the pathway I\'m building your plan around."'
                    ),
                },
            },
            'required': ['header_title', 'people', 'chat_message'],
        },
    },
}

SUBMIT_FINAL_PLAN_TOOL = {
    'type': 'function',
    'function': {
        'name': 'submit_final_plan',
        'description': (
            'Submit the Stage 5 Performance-Aligned Learning Plan. '
            'Call immediately after submit_ai_analysis — no user questions in between. '
            'One employee block per person — NEVER combine or skip anyone. '
            'CRITICAL: sessions array must be fully populated. Never leave it empty.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'plan_title': {
                    'type': 'string',
                    'description': 'e.g. "Performance-Aligned Learning Plans — Monticello"',
                },
                'company_name': {'type': 'string'},
                'delivery_method': {
                    'type': 'string',
                    'description': (
                        'Delivery method the AI chose, e.g. "1:1 Training + Coaching". '
                        'Must match what was recommended in submit_ai_analysis.'
                    ),
                },
                'num_sessions': {
                    'type': 'integer',
                    'description': (
                        'Session count chosen: 4, 6, or 8. '
                        'Must match recommended_sessions from submit_ai_analysis. '
                        'Must equal the number of session rows written per employee.'
                    ),
                },
                'tagline': {
                    'type': 'string',
                    'description': 'Always: "Rooted in real feedback. Designed for real growth."',
                },
                'intro_paragraph': {
                    'type': 'string',
                    'description': (
                        '3-4 sentences. State what data was provided (type and scope), '
                        'what the analysis revealed as the primary development themes, '
                        'and what this plan is specifically designed to achieve for this '
                        'company and these individuals. Name the company and the people. '
                        'This is the opening paragraph of a client deliverable — write '
                        'it with the authority of an expert who read the actual data.'
                    ),
                },
                'employees': {
                    'type': 'array',
                    'description': (
                        'One COMPLETE block per person. '
                        'If 2 people → 2 blocks. Each block is fully self-contained.'
                    ),
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'role_context': {
                                'type': 'string',
                                'description': 'Role / team / transition context, one line.',
                            },
                            'strengths': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': '3-5 specific strengths drawn from the data.',
                            },
                            'growth_opportunities': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'description': '3-4 development areas from the data.',
                            },
                            'career_direction': {
                                'type': 'string',
                                'description': 'One sentence on where this person is headed.',
                            },
                            'sessions': {
                                'type': 'array',
                                'description': (
                                    'ALL session rows for this person. '
                                    'Must contain exactly num_sessions items. '
                                    'Generate sessions FIRST before any other long text fields.'
                                ),
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'number': {'type': 'integer'},
                                        'title': {
                                            'type': 'string',
                                            'description': 'Exact Bundle session title.',
                                        },
                                        'skill_categories': {
                                            'type': 'array',
                                            'items': {'type': 'string'},
                                            'maxItems': 2,
                                            'description': (
                                                '1-2 main skill category names for the badge. '
                                                'e.g. ["Communication", "Stakeholder Engagement"].'
                                            ),
                                        },
                                        'skill_focus': {
                                            'type': 'array',
                                            'items': {'type': 'string'},
                                            'description': '2-4 specific sub-skill names.',
                                        },
                                        'what_it_covers': {
                                            'type': 'string',
                                            'description': (
                                                '1 short sentence (max 15 words) — plain English '
                                                'description of what the person will learn.'
                                            ),
                                        },
                                        'recommended_because': {
                                            'type': 'string',
                                            'description': (
                                                '1 sentence direct quote or close paraphrase '
                                                'from the review/data showing why this session. '
                                                'Start with: "The review states that..." or '
                                                '"The self-assessment notes..."'
                                            ),
                                        },
                                        'why_this_session': {
                                            'type': 'string',
                                            'description': (
                                                'MINIMUM 3 sentences (aim for 4-5). Explain: '
                                                '(a) WHY this session lands at this point in the '
                                                'sequence — what earlier sessions enabled it; '
                                                '(b) what specific gap from the data it addresses '
                                                '— reference the actual review language; '
                                                '(c) what capability or session it unlocks next. '
                                                'Never write generic rationale — name the person '
                                                'and their specific context.'
                                            ),
                                        },
                                    },
                                    'required': [
                                        'number', 'title', 'skill_categories', 'skill_focus',
                                        'what_it_covers', 'recommended_because',
                                        'why_this_session',
                                    ],
                                },
                                'minItems': 1,
                            },
                            'what_this_delivers': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'minItems': 4,
                                'maxItems': 5,
                                'description': (
                                    '4-5 specific, measurable outcome statements for this person. '
                                    'Start each with an action verb and reference their actual gaps. '
                                    'e.g. "Stakeholder responses consistently within 24-48 hours, '
                                    'reducing reputational risk flagged in the review."'
                                ),
                            },
                            'group_rationale': {
                                'type': 'string',
                                'description': (
                                    'MINIMUM 3-4 sentences for the "Why this group first" card. '
                                    '(1) Name the 2-3 interconnected gaps the data reveals and '
                                    'how they connect to each other — why they must be addressed '
                                    'together, not in isolation. (2) Explain why NOW is the right '
                                    'moment — reference their role, any transition underway, or '
                                    'the performance context the review describes. (3) State what '
                                    'becomes possible for this person once these gaps are closed. '
                                    'Quote or paraphrase the actual review language. Never generic.'
                                ),
                            },
                            'plan_overview': {
                                'type': 'string',
                                'description': (
                                    'MINIMUM 4-5 sentences describing the full arc of the plan. '
                                    '(1) What problem the opening sessions solve and why that '
                                    'comes first. (2) What the middle sessions build and why '
                                    'that sequence matters. (3) What the final sessions deliver '
                                    'and how they connect to the person\'s role goals. '
                                    'Write this as a narrative paragraph — no bullets. '
                                    'Name the specific sessions and link them to the data.'
                                ),
                            },
                            'peer_workshop_note': {
                                'type': 'string',
                                'description': (
                                    '2-3 sentences explaining why peer workshops are NOT the '
                                    'right format for this specific person at this stage. '
                                    'Reference the individual nature of their specific gaps, '
                                    'why 1:1 delivery addresses what group learning cannot, '
                                    'and when peer workshops might make sense in the future.'
                                ),
                            },
                            'sequencing_paragraph': {
                                'type': 'string',
                                'description': (
                                    'MINIMUM 4-6 sentences. Explain the full arc of this '
                                    'person\'s plan: (1) Why the opening session was chosen — '
                                    'what gap it directly addresses and what it makes possible; '
                                    '(2) How the middle sessions build the skill bridge from '
                                    'where they are to where they need to be; '
                                    '(3) What the final sessions deliver and how they connect '
                                    'to the person\'s role evolution and stated goals. '
                                    'Reference the actual review language. Name the person. '
                                    'No generic "this builds leadership skills" filler.'
                                ),
                            },
                            'coaching_support': {
                                'type': 'string',
                                'description': (
                                    'MINIMUM 4-5 sentences. Explain what the coaching layer '
                                    'specifically adds for THIS person that training alone '
                                    'cannot achieve. (1) Name the behavioural gaps that need '
                                    'real-time reinforcement — reference the review language. '
                                    '(2) Describe what the coach and learner will work on '
                                    'together between sessions. (3) Explain how coaching '
                                    'accelerates the programme for someone in this specific '
                                    'role and at this specific career stage. '
                                    'Never write generic coaching benefits — anchor to this '
                                    'person\'s situation and their data.'
                                ),
                            },
                        },
                        'required': [
                            'name', 'role_context', 'strengths', 'growth_opportunities',
                            'career_direction', 'sessions', 'what_this_delivers',
                            'sequencing_paragraph', 'coaching_support',
                        ],
                    },
                    'minItems': 1,
                },
                'chat_message': {
                    'type': 'string',
                    'description': (
                        '1-2 sentences. '
                        'e.g. "Your plan is ready. Want me to set up a quick call with '
                        'a Bundle consultant to walk through it?"'
                    ),
                },
            },
            'required': [
                'plan_title', 'company_name', 'delivery_method', 'num_sessions',
                'tagline', 'intro_paragraph', 'employees', 'chat_message',
            ],
        },
    },
}

BUNDLE_TOOLS = [SUBMIT_AI_ANALYSIS_TOOL, SUBMIT_FINAL_PLAN_TOOL]


def _tool_args(tool_call):
    try:
        return json.loads(tool_call.function.arguments or '{}')
    except json.JSONDecodeError:
        return {}


def handle_tool_call(run, tool_call):
    name = tool_call.function.name
    args = _tool_args(tool_call)

    if name == 'submit_ai_analysis':
        return _handle_submit_ai_analysis(run, args)
    if name == 'submit_final_plan':
        return _handle_submit_final_plan(run, args)
    return json.dumps({'error': f'Unknown tool: {name}'}), 'Something went wrong.', None


def _handle_submit_ai_analysis(run, args):
    people = args.get('people', [])

    # Backwards compatibility: if the AI still sends old flat format,
    # wrap it in a people array.
    if not people and args.get('growth_opportunities'):
        people = [{
            'name': args.get('header_title', 'Employee'),
            'role_title': '',
            'confidence': args.get('confidence', 'Moderate confidence'),
            'confidence_rationale': args.get('confidence_rationale', ''),
            'summary_paragraph': args.get('summary_paragraph', ''),
            'growth_opportunities': args.get('growth_opportunities', []),
            'recommended_delivery': '1:1 Training + Coaching',
            'recommended_sessions': 6,
            'delivery_options': args.get('delivery_options', []),
            'depth_options': args.get('depth_options', {}),
            'sequencing_logic': args.get('sequencing_logic', ''),
        }]

    payload = {
        'header_title': args.get('header_title', ''),
        'people': people,
        'generated_at': timezone.now().isoformat(),
    }
    run.ai_analysis_json = json.dumps(payload)
    run.current_stage = 4
    run.status = 'recommendation_ready'
    run.save(update_fields=['ai_analysis_json', 'current_stage', 'status', 'updated_at'])

    chat_msg = (args.get('chat_message') or '').strip() or (
        'Your AI analysis and recommendation are ready. '
        'Open the report to review growth opportunities, delivery options, and depth tiers.'
    )
    return json.dumps({'success': True, 'report': 'ai_analysis'}), chat_msg, None


def _handle_submit_final_plan(run, args):
    employees = args.get('employees', [])
    ai_num_sessions = args.get('num_sessions') or max(
        (len(e.get('sessions') or []) for e in employees),
        default=0,
    )
    payload = {
        'plan_title': args.get('plan_title', ''),
        'company_name': args.get('company_name', run.company_name or ''),
        'delivery_method': args.get('delivery_method', '1:1 Training + Coaching'),
        'tagline': args.get('tagline', 'Rooted in real feedback. Designed for real growth.'),
        'intro_paragraph': args.get('intro_paragraph', ''),
        'employees': employees,
        'num_sessions': ai_num_sessions,
        'generated_at': timezone.now().isoformat(),
    }
    if ai_num_sessions:
        run.num_sessions = ai_num_sessions

    run.final_plan_json = json.dumps(payload)
    run.final_plan = _final_plan_to_markdown(payload)
    run.current_stage = 5
    run.status = 'plan_generated'
    run.save(update_fields=[
        'final_plan_json', 'final_plan', 'num_sessions',
        'current_stage', 'status', 'updated_at',
    ])

    chat_msg = (args.get('chat_message') or '').strip() or (
        'Your performance-aligned learning plan is ready. '
        'Open the full report to review every session and rationale, or download the PDF.'
    )
    return json.dumps({'success': True, 'report': 'final_plan'}), chat_msg, None


def _final_plan_to_markdown(payload):
    """Markdown backup for PDF export."""
    delivery = payload.get('delivery_method', '')
    sessions = payload.get('num_sessions', '')
    meta = f"{delivery} · {sessions} sessions" if delivery and sessions else delivery or ''
    lines = [
        f"## {payload.get('company_name', '')} — Performance-Aligned Learning Plans",
        '',
        payload.get('tagline', ''),
        meta,
        '',
        payload.get('intro_paragraph', ''),
        '',
    ]
    for emp in payload.get('employees') or []:
        lines.append(f"### {emp.get('name', 'Learner')}")
        lines.append(emp.get('role_context', ''))
        lines.append('')
        lines.append('**Strengths**')
        for s in emp.get('strengths') or []:
            lines.append(f'- {s}')
        lines.append('')
        lines.append('**Growth opportunities**')
        for g in emp.get('growth_opportunities') or []:
            lines.append(f'- {g}')
        lines.append('')
        lines.append('**Career direction**')
        lines.append(emp.get('career_direction', ''))
        lines.append('')
        lines.append(emp.get('sequencing_paragraph', ''))
        lines.append('')
        lines.append('| # | Session | What it covers | Skill focus | Why this session |')
        lines.append('|---|---------|---------------|------------|-----------------|')
        for sess in emp.get('sessions') or []:
            skills = ' / '.join(sess.get('skill_focus') or [])
            lines.append(
                f"| {sess.get('number')} | {sess.get('title')} | "
                f"{sess.get('what_it_covers')} | {skills} | {sess.get('why_this_session')} |"
            )
        lines.append('')
        lines.append('### Coaching support')
        lines.append('')
        lines.append(emp.get('coaching_support', ''))
        lines.append('')
        lines.append('---')
        lines.append('')
    return '\n'.join(lines)


def run_report_flags(run):
    """Flags for API / chat UI."""
    return {
        'has_analysis_report': bool(run.ai_analysis_json),
        'has_final_plan_report': bool(run.final_plan_json or run.final_plan),
    }
