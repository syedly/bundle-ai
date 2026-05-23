"""
OpenAI tool definitions and handlers for Bundle deliverable reports.

Flow (see product flowchart):
  Agents 1–3: intake conversation in chat
  Tool submit_ai_analysis: Stage 4 detailed recommendation
  Tool submit_final_plan: Stage 5 performance-aligned learning plan
"""
import json

from django.utils import timezone

from .models import BuilderRun

# ── Tool schemas (OpenAI function calling) ────────────────────────────────────

SUBMIT_AI_ANALYSIS_TOOL = {
    'type': 'function',
    'function': {
        'name': 'submit_ai_analysis',
        'description': (
            'Submit the complete Stage 4 AI Analysis / Recommendation report. '
            'Call ONCE when intake data is sufficient. Do NOT paste the full report in chat — '
            'put all detail in this tool. Include specific quotes and evidence from reviews/data.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'header_title': {
                    'type': 'string',
                    'description': 'e.g. "Monticello — Individual"',
                },
                'confidence': {
                    'type': 'string',
                    'enum': ['Strong confidence', 'Moderate confidence', 'Limited confidence'],
                },
                'confidence_rationale': {
                    'type': 'string',
                    'description': '2-4 sentences explaining the confidence score with specific evidence.',
                },
                'summary_paragraph': {
                    'type': 'string',
                    'description': 'Executive summary: 3-5 sentences about the person, context, and plan rationale.',
                },
                'growth_opportunities': {
                    'type': 'array',
                    'description': '3-4 skill gaps with detailed evidence.',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'skill_area': {'type': 'string'},
                            'evidence': {
                                'type': 'string',
                                'description': 'Minimum 2 sentences; quote or paraphrase manager/review data.',
                            },
                        },
                        'required': ['skill_area', 'evidence'],
                    },
                    'minItems': 3,
                    'maxItems': 4,
                },
                'delivery_options': {
                    'type': 'array',
                    'description': 'Three delivery pathways.',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'recommended': {'type': 'boolean'},
                            'description': {
                                'type': 'string',
                                'description': '2-4 sentences specific to this learner.',
                            },
                            'sessions_label': {
                                'type': 'string',
                                'description': 'e.g. "4 sessions · includes coaching support"',
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
                        'intro': {
                            'type': 'string',
                            'description': 'Brief intro to depth tiers.',
                        },
                        'full_outcome_paragraph': {
                            'type': 'string',
                            'description': '3-5 sentences: outcomes at full 8-session depth.',
                        },
                        'tiers': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'name': {'type': 'string'},
                                    'sessions': {'type': 'integer'},
                                    'tagline': {'type': 'string'},
                                    'description': {'type': 'string'},
                                },
                                'required': ['name', 'sessions', 'tagline', 'description'],
                            },
                            'minItems': 3,
                            'maxItems': 3,
                        },
                        'start_small_paragraph': {
                            'type': 'string',
                            'description': 'Honest 2-4 sentences on what minimum tier does NOT cover.',
                        },
                    },
                    'required': [
                        'intro', 'full_outcome_paragraph', 'tiers', 'start_small_paragraph',
                    ],
                },
                'sequencing_logic': {
                    'type': 'string',
                    'description': (
                        'Detailed session-by-session sequencing rationale and primary skill audit. '
                        'Multiple paragraphs; explain why each session order.'
                    ),
                },
                'chat_message': {
                    'type': 'string',
                    'description': (
                        'Short 1-3 sentence message for the chat UI telling the user '
                        'the analysis is ready to view (do not repeat the full report).'
                    ),
                },
            },
            'required': [
                'header_title', 'confidence', 'confidence_rationale', 'summary_paragraph',
                'growth_opportunities', 'delivery_options', 'depth_options',
                'sequencing_logic', 'chat_message',
            ],
        },
    },
}

SUBMIT_FINAL_PLAN_TOOL = {
    'type': 'function',
    'function': {
        'name': 'submit_final_plan',
        'description': (
            'Submit the complete Stage 5 Performance-Aligned Learning Plan. '
            'Call ONCE after delivery method and session count are confirmed. '
            'Do NOT paste the full plan in chat — use this tool only. '
            'Write a FULL block per employee with all sessions and coaching support.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'plan_title': {
                    'type': 'string',
                    'description': 'e.g. "Performance-Aligned Learning Plan: Employee 1"',
                },
                'company_name': {'type': 'string'},
                'tagline': {
                    'type': 'string',
                    'description': 'Default: "Rooted in real feedback. Designed for real growth."',
                },
                'intro_paragraph': {
                    'type': 'string',
                    'description': '2-4 sentences on how the plan was built from their data.',
                },
                'sequencing_overview': {
                    'type': 'string',
                    'description': (
                        '1 paragraph before employee blocks explaining how sessions build on each other.'
                    ),
                },
                'employees': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'role_context': {
                                'type': 'string',
                                'description': 'Job title / team / transition context, one line.',
                            },
                            'strengths': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'minItems': 3,
                            },
                            'growth_opportunities': {
                                'type': 'array',
                                'items': {'type': 'string'},
                                'minItems': 3,
                            },
                            'career_direction': {'type': 'string'},
                            'sequencing_paragraph': {
                                'type': 'string',
                                'description': '4-6 sentences on session arc for this person.',
                            },
                            'sessions': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'number': {'type': 'integer'},
                                        'title': {'type': 'string'},
                                        'what_it_covers': {'type': 'string'},
                                        'skill_focus': {
                                            'type': 'array',
                                            'items': {'type': 'string'},
                                        },
                                        'why_this_session': {
                                            'type': 'string',
                                            'description': 'Minimum 3 sentences with specific data quotes.',
                                        },
                                    },
                                    'required': [
                                        'number', 'title', 'what_it_covers',
                                        'skill_focus', 'why_this_session',
                                    ],
                                },
                                'minItems': 1,
                            },
                            'coaching_support': {
                                'type': 'string',
                                'description': '3-5 sentences personalized coaching value.',
                            },
                        },
                        'required': [
                            'name', 'role_context', 'strengths', 'growth_opportunities',
                            'career_direction', 'sequencing_paragraph', 'sessions',
                            'coaching_support',
                        ],
                    },
                    'minItems': 1,
                },
                'chat_message': {
                    'type': 'string',
                    'description': 'Short message for chat: plan is ready to open and download.',
                },
            },
            'required': [
                'plan_title', 'company_name', 'tagline', 'intro_paragraph',
                'sequencing_overview', 'employees', 'chat_message',
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
    """
    Execute a tool call. Returns (tool_result_content, chat_message, suggestions_hint).
    suggestions_hint is None — caller still resolves suggestions from chat_message.
    """
    name = tool_call.function.name
    args = _tool_args(tool_call)

    if name == 'submit_ai_analysis':
        return _handle_submit_ai_analysis(run, args)
    if name == 'submit_final_plan':
        return _handle_submit_final_plan(run, args)
    return json.dumps({'error': f'Unknown tool: {name}'}), 'Something went wrong.', None


def _handle_submit_ai_analysis(run, args):
    payload = {
        'header_title': args.get('header_title', ''),
        'confidence': args.get('confidence', 'Moderate confidence'),
        'confidence_rationale': args.get('confidence_rationale', ''),
        'summary_paragraph': args.get('summary_paragraph', ''),
        'growth_opportunities': args.get('growth_opportunities', []),
        'delivery_options': args.get('delivery_options', []),
        'depth_options': args.get('depth_options', {}),
        'sequencing_logic': args.get('sequencing_logic', ''),
        'generated_at': timezone.now().isoformat(),
    }
    run.ai_analysis_json = json.dumps(payload)
    run.current_stage = 4
    run.status = 'recommendation_ready'
    run.save(update_fields=['ai_analysis_json', 'current_stage', 'status', 'updated_at'])

    chat_msg = (args.get('chat_message') or '').strip() or (
        'Your AI analysis and recommendation are ready. '
        'Open the report to review growth opportunities, delivery options, and depth tiers — '
        'then come back here to choose a pathway.'
    )
    return json.dumps({'success': True, 'report': 'ai_analysis'}), chat_msg, None


def _handle_submit_final_plan(run, args):
    payload = {
        'plan_title': args.get('plan_title', ''),
        'company_name': args.get('company_name', run.company_name or ''),
        'tagline': args.get('tagline', 'Rooted in real feedback. Designed for real growth.'),
        'intro_paragraph': args.get('intro_paragraph', ''),
        'sequencing_overview': args.get('sequencing_overview', ''),
        'employees': args.get('employees', []),
        'num_sessions': max(
            (len(e.get('sessions') or []) for e in args.get('employees') or []),
            default=0,
        ),
        'generated_at': timezone.now().isoformat(),
    }
    if run.num_sessions:
        payload['num_sessions'] = run.num_sessions

    run.final_plan_json = json.dumps(payload)
    run.final_plan = _final_plan_to_markdown(payload)
    run.current_stage = 5
    run.status = 'plan_generated'
    run.save(update_fields=[
        'final_plan_json', 'final_plan', 'current_stage', 'status', 'updated_at',
    ])

    chat_msg = (args.get('chat_message') or '').strip() or (
        'Your performance-aligned learning plan is ready. '
        'Open the full report to review every session and rationale, or download the PDF.'
    )
    return json.dumps({'success': True, 'report': 'final_plan'}), chat_msg, None


def _final_plan_to_markdown(payload):
    """Markdown backup for PDF export and legacy parsers."""
    lines = [
        f"## {payload.get('company_name', '')} — Performance-Aligned Learning Plans",
        '',
        payload.get('tagline', ''),
        '',
        payload.get('intro_paragraph', ''),
        '',
        payload.get('sequencing_overview', ''),
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
        lines.append(f"**Career direction**")
        lines.append(emp.get('career_direction', ''))
        lines.append('')
        lines.append(emp.get('sequencing_paragraph', ''))
        lines.append('')
        lines.append('| # | Session | What it covers | Skill focus | Why this session |')
        lines.append('|---|---------|---------------|------------|-----------------|')
        for sess in emp.get('sessions') or []:
            skills = '<br>'.join(sess.get('skill_focus') or [])
            lines.append(
                f"| {sess.get('number')} | {sess.get('title')} | "
                f"{sess.get('what_it_covers')} | {skills} | {sess.get('why_this_session')} |"
            )
        lines.append('')
        lines.append('### Coaching support')
        lines.append('')
        lines.append(emp.get('coaching_support', ''))
        lines.append('')
    return '\n'.join(lines)


def run_report_flags(run):
    """Flags for API / chat UI."""
    return {
        'has_analysis_report': bool(run.ai_analysis_json),
        'has_final_plan_report': bool(run.final_plan_json or run.final_plan),
    }
