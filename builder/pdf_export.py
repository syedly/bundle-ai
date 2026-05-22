"""
Generate a Bundle-branded PDF from a BuilderRun's final_plan.
Uses reportlab with Bundle brand colors from brand guidelines.
"""
import re
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)

from .plan_generator import parse_plan

# ── Bundle brand colors ───────────────────────────────────────────────────────
DARK_TEAL  = colors.HexColor('#00403F')   # Primary Teal
MED_TEAL   = colors.HexColor('#3B9A8D')   # Accent Teal
MINT       = colors.HexColor('#BAF0D8')   # Soft accent
CORAL      = colors.HexColor('#FF9B7A')   # Accent
OFF_WHITE  = colors.HexColor('#FAFAFA')   # Page bg
LIGHT_GRAY = colors.HexColor('#EDEDED')   # Card bg
BODY_TEXT  = colors.HexColor('#1A1A1A')   # Body copy
WHITE      = colors.white

# Content width: A4 (210mm) - 20mm left - 20mm right = 170mm
CW = 170 * mm


def _styles():
    s = {}
    s['title'] = ParagraphStyle(
        'BTitle', fontName='Helvetica-Bold', fontSize=18,
        textColor=WHITE, leading=22, spaceAfter=1*mm,
    )
    s['subtitle'] = ParagraphStyle(
        'BSubtitle', fontName='Helvetica', fontSize=10,
        textColor=MINT, leading=14,
    )
    s['intro'] = ParagraphStyle(
        'BIntro', fontName='Helvetica', fontSize=10,
        textColor=BODY_TEXT, leading=15, spaceAfter=4*mm,
    )
    s['emp_name'] = ParagraphStyle(
        'BEmpName', fontName='Helvetica-Bold', fontSize=13,
        textColor=WHITE, leading=17,
    )
    s['emp_role'] = ParagraphStyle(
        'BEmpRole', fontName='Helvetica', fontSize=10,
        textColor=MINT, leading=14,
    )
    s['option_title'] = ParagraphStyle(
        'BOptTitle', fontName='Helvetica-Bold', fontSize=11,
        textColor=DARK_TEAL, leading=14,
    )
    s['overview'] = ParagraphStyle(
        'BOverview', fontName='Helvetica-Oblique', fontSize=10,
        textColor=BODY_TEXT, leading=14, spaceAfter=3*mm,
    )
    s['coaching'] = ParagraphStyle(
        'BCoaching', fontName='Helvetica', fontSize=9,
        textColor=DARK_TEAL, leading=13, spaceAfter=3*mm,
        leftIndent=4*mm,
    )
    s['footer'] = ParagraphStyle(
        'BFooter', fontName='Helvetica-Oblique', fontSize=9,
        textColor=colors.HexColor('#666666'), alignment=TA_CENTER, leading=13,
    )
    s['cell'] = ParagraphStyle(
        'BCell', fontName='Helvetica', fontSize=8.5,
        textColor=BODY_TEXT, leading=12,
    )
    s['cell_bold'] = ParagraphStyle(
        'BCellBold', fontName='Helvetica-Bold', fontSize=8.5,
        textColor=DARK_TEAL, leading=12,
    )
    s['hdr_cell'] = ParagraphStyle(
        'BHdrCell', fontName='Helvetica-Bold', fontSize=8.5,
        textColor=WHITE, leading=12,
    )
    s['profile_key'] = ParagraphStyle(
        'BProfileKey', fontName='Helvetica-Bold', fontSize=9,
        textColor=DARK_TEAL, leading=13,
    )
    s['profile_val'] = ParagraphStyle(
        'BProfileVal', fontName='Helvetica', fontSize=9,
        textColor=BODY_TEXT, leading=13,
    )
    return s


def _clean(text):
    """Strip markdown for PDF rendering; convert **bold** to <b>.</b>"""
    if not text:
        return ''
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    # Remove emoji — reportlab can't render them
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _add_page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(colors.HexColor('#888888'))
    canvas.drawRightString(
        doc.pagesize[0] - 20*mm, 11*mm,
        f'Page {doc.page}  |  Bundle AI Training Builder  |  Confidential',
    )
    canvas.restoreState()


def _doc_header(company, styles):
    """Dark teal header banner."""
    data = [[
        Paragraph(f'Bundle  |  Performance-Aligned Learning Plans', styles['subtitle']),
        Paragraph('', styles['subtitle']),
    ], [
        Paragraph(company, styles['title']),
        Paragraph('', styles['title']),
    ]]
    t = Table(data, colWidths=[CW * 0.75, CW * 0.25])
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), DARK_TEAL),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',(0, 0), (-1, -1), 10),
        ('TOPPADDING',  (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return [t, Spacer(1, 5*mm)]


def _employee_header(emp, styles):
    name = _clean(emp.get('name', 'Employee'))
    role = _clean(emp.get('role_title', ''))
    data = [[Paragraph(name, styles['emp_name']), Paragraph(role, styles['emp_role'])]]
    t = Table(data, colWidths=[CW * 0.55, CW * 0.45])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), MED_TEAL),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING',   (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 7),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return [t, Spacer(1, 3*mm)]


def _profile_table(profile, styles):
    rows = [
        [Paragraph('Role',                  styles['profile_key']),
         Paragraph(_clean(profile.get('role', '—')),                   styles['profile_val'])],
        [Paragraph('Strengths',             styles['profile_key']),
         Paragraph(_clean(profile.get('strengths', '—')),               styles['profile_val'])],
        [Paragraph('Growth Opportunities',  styles['profile_key']),
         Paragraph(_clean(profile.get('growth_opportunities', '—')),    styles['profile_val'])],
        [Paragraph('Career Direction',      styles['profile_key']),
         Paragraph(_clean(profile.get('career_direction', '—')),         styles['profile_val'])],
    ]
    t = Table(rows, colWidths=[CW * 0.30, CW * 0.70])
    t.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (0, -1), LIGHT_GRAY),
        ('BACKGROUND',   (1, 0), (1, -1), WHITE),
        ('BOX',          (0, 0), (-1, -1), 0.5, MED_TEAL),
        ('INNERGRID',    (0, 0), (-1, -1), 0.3, colors.HexColor('#DDDDDD')),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
        ('LEFTPADDING',  (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
    ]))
    return [t, Spacer(1, 4*mm)]


def _session_table(sessions, styles):
    header = [
        Paragraph('#',                styles['hdr_cell']),
        Paragraph('Session',          styles['hdr_cell']),
        Paragraph('Skill Focus',      styles['hdr_cell']),
        Paragraph('Why This Session', styles['hdr_cell']),
    ]
    rows = [header]
    for i, s in enumerate(sessions):
        skills_html = '<br/>'.join(_clean(sk) for sk in s.get('skills', []) if sk)
        rows.append([
            Paragraph(str(s.get('number', i + 1)), styles['cell']),
            Paragraph(_clean(s.get('session', '')), styles['cell_bold']),
            Paragraph(skills_html, styles['cell']),
            Paragraph(_clean(s.get('why', '')),     styles['cell']),
        ])

    col_w = [CW * 0.06, CW * 0.20, CW * 0.24, CW * 0.50]
    t = Table(rows, colWidths=col_w)

    cmds = [
        ('BACKGROUND',   (0, 0), (-1, 0), DARK_TEAL),
        ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
        ('FONTSIZE',     (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
        ('LEFTPADDING',  (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BOX',          (0, 0), (-1, -1), 0.5, MED_TEAL),
        ('INNERGRID',    (0, 0), (-1, -1), 0.3, colors.HexColor('#DDDDDD')),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',        (0, 0), (0, -1), 'CENTER'),
    ]
    for i in range(1, len(rows)):
        bg = LIGHT_GRAY if i % 2 == 0 else WHITE
        cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

    t.setStyle(TableStyle(cmds))
    return t


def _option_block(option, styles):
    if not option:
        return []
    elems = []

    # Option title banner (mint background)
    title_data = [[Paragraph(_clean(option.get('title', 'Option')), styles['option_title'])]]
    tt = Table(title_data, colWidths=[CW])
    tt.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), MINT),
        ('LEFTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',   (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
    ]))
    elems.append(tt)
    elems.append(Spacer(1, 2*mm))

    # Overview
    overview = option.get('overview', '')
    if overview:
        elems.append(Paragraph(_clean(overview), styles['overview']))

    # Session table
    sessions = option.get('sessions', [])
    if sessions:
        elems.append(_session_table(sessions, styles))

    # Coaching support
    coaching = option.get('coaching', '')
    if coaching:
        elems.append(Spacer(1, 2*mm))
        elems.append(Paragraph(
            f'<b>Coaching Support:</b> {_clean(coaching)}',
            styles['coaching'],
        ))

    elems.append(Spacer(1, 5*mm))
    return elems


def generate_plan_pdf(run):
    """Generate and return PDF bytes for a BuilderRun."""
    plan_data = parse_plan(run.final_plan or '')
    company   = run.company_name or plan_data.get('company') or 'Your Company'

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=22*mm,   bottomMargin=18*mm,
        title=f'{company} — Bundle Training Plans',
        author='Bundle AI Training Builder',
    )

    styles = _styles()
    story  = []

    # Header
    story += _doc_header(company, styles)

    # Intro
    intro = plan_data.get('intro', '')
    if intro:
        clean_intro = _clean(intro)
        if clean_intro:
            story.append(Paragraph(clean_intro, styles['intro']))
            story.append(Spacer(1, 4*mm))

    # Employee sections
    employees = plan_data.get('employees', [])
    if not employees:
        # Fallback: render the raw plan as text
        story.append(Paragraph('Training Plan', styles['option_title']))
        story.append(Spacer(1, 3*mm))
        for line in (run.final_plan or '').split('\n'):
            clean = _clean(line.strip())
            if clean:
                story.append(Paragraph(clean, styles['intro']))
    else:
        for i, emp in enumerate(employees):
            if i > 0:
                story.append(PageBreak())
            story += _employee_header(emp, styles)
            profile = emp.get('profile', {})
            if any(profile.values()):
                story += _profile_table(profile, styles)
            if emp.get('option_a'):
                story += _option_block(emp['option_a'], styles)
            if emp.get('option_b'):
                story += _option_block(emp['option_b'], styles)

    # Footer
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width=CW, thickness=0.8, color=MED_TEAL))
    story.append(Spacer(1, 3*mm))
    footer_text = plan_data.get('footer', 'Ready to move forward? Reach out to your Bundle partner.')
    story.append(Paragraph(_clean(footer_text), styles['footer']))

    doc.build(story, onFirstPage=_add_page_footer, onLaterPages=_add_page_footer)
    buffer.seek(0)
    return buffer.read()
