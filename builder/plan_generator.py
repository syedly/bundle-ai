"""
Parse AI-generated markdown training plans into structured data for PDF export.
"""
import re


def parse_plan(plan_text):
    """
    Parse the AI-generated plan markdown into structured data.
    Returns:
      {
        'company': str,
        'intro':   str,
        'employees': [
          {
            'name':      str,
            'role_title':str,
            'profile':   {'role': str, 'strengths': str, 'growth_opportunities': str, 'career_direction': str},
            'option_a':  {'title': str, 'overview': str, 'sessions': [...], 'coaching': str},
            'option_b':  {'title': str, 'overview': str, 'sessions': [...], 'coaching': str},
          }
        ],
        'footer': str,
      }
    """
    if not plan_text:
        return {'company': '', 'intro': '', 'employees': [], 'footer': ''}

    result = {
        'company':   '',
        'intro':     '',
        'employees': [],
        'footer':    'Ready to move forward? Reach out to your Bundle partner to confirm which option fits best and get these learners started.',
    }

    # Extract footer
    footer_match = re.search(r'\*Ready to move forward\?[^*]*\*', plan_text, re.DOTALL)
    if footer_match:
        result['footer'] = footer_match.group(0).strip('*').strip()

    # Extract company from H2 heading
    company_match = re.search(r'^##\s+.*?([A-Za-z][A-Za-z0-9 &,.\']+?)\s+[—\-–]', plan_text, re.MULTILINE)
    if company_match:
        result['company'] = company_match.group(1).strip()

    # Extract intro (before first ### heading)
    intro_match = re.match(r'^(.*?)(?=^###\s)', plan_text, re.DOTALL | re.MULTILINE)
    if intro_match:
        intro = intro_match.group(1)
        intro = re.sub(r'^##[^\n]*\n', '', intro, flags=re.MULTILINE).strip()
        result['intro'] = intro

    # Split into employee sections by ### heading
    sections = re.split(r'(?=^###\s)', plan_text, flags=re.MULTILINE)
    for section in sections:
        if not section.strip().startswith('###'):
            continue
        emp = _parse_employee_section(section)
        if emp:
            result['employees'].append(emp)

    return result


def _parse_employee_section(section_text):
    emp = {}

    # Name and role from ### heading
    heading_match = re.match(r'###\s+(.+?)\s+[—\-–]\s+(.+)', section_text)
    if not heading_match:
        return None
    emp['name']       = heading_match.group(1).strip()
    emp['role_title'] = heading_match.group(2).strip()

    emp['profile'] = _parse_profile_table(section_text)

    # Option A
    oa_match = re.search(r'####\s+Option A.*?(?=####\s+Option B|$)', section_text, re.DOTALL)
    emp['option_a'] = _parse_option_section(oa_match.group(0)) if oa_match else None

    # Option B
    ob_match = re.search(r'####\s+Option B.*?(?=^---|\Z)', section_text, re.DOTALL | re.MULTILINE)
    emp['option_b'] = _parse_option_section(ob_match.group(0)) if ob_match else None

    return emp


def _parse_profile_table(text):
    profile = {
        'role':                '',
        'strengths':           '',
        'growth_opportunities': '',
        'career_direction':    '',
    }
    # Match | **Key** | Value | rows
    rows = re.findall(r'\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|', text)
    for key, value in rows:
        key_lower = key.lower()
        if key_lower == 'role':
            profile['role'] = value.strip()
        elif 'strength' in key_lower:
            profile['strengths'] = value.strip()
        elif 'growth' in key_lower:
            profile['growth_opportunities'] = value.strip()
        elif 'career' in key_lower:
            profile['career_direction'] = value.strip()
    return profile


def _parse_option_section(section_text):
    option = {'title': '', 'overview': '', 'sessions': [], 'coaching': ''}

    # Title
    title_match = re.match(r'####\s+(.+)', section_text)
    if title_match:
        option['title'] = title_match.group(1).strip()

    # Overview paragraph (between title line and first |)
    overview_match = re.search(r'####[^\n]*\n+([^|#\n][^\n]+(?:\n[^|#\n][^\n]+)*)', section_text)
    if overview_match:
        option['overview'] = overview_match.group(1).strip()

    # Sessions from table rows (skip header and separator)
    table_rows = re.findall(
        r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$',
        section_text,
        re.MULTILINE,
    )
    for num, session, skills_raw, why in table_rows:
        # Split skills by <br> or newline
        skills_list = [s.strip() for s in re.split(r'<br>|<BR>|\n', skills_raw) if s.strip()]
        option['sessions'].append({
            'number':  int(num),
            'session': session.strip(),
            'skills':  skills_list,
            'why':     why.strip(),
        })

    # Coaching support
    coaching_match = re.search(r'\*\*Coaching Support:\*\*\s*(.+?)(?:\n|$)', section_text)
    if coaching_match:
        option['coaching'] = coaching_match.group(1).strip()

    return option
