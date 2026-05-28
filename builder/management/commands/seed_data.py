from django.core.management.base import BaseCommand
from builder.models import PrimarySkill, SubSkill, Session, Pathway


# ── Primary Skills (Human-Centered Skills Taxonomy) ───────────────────────────
PRIMARY_SKILLS = [
    ("Empathy",                "Understanding and sharing the feelings of others."),
    ("Communication",          "The ability to convey information clearly, authentically, and effectively across contexts."),
    ("Collaboration",          "Working effectively with others to achieve shared goals."),
    ("Teamwork",               "Working cooperatively within a team to achieve common objectives through mutual support."),
    ("Problem Solving",        "Analyzing and resolving complex issues and challenges using structured and creative thinking."),
    ("Creativity",             "Generating novel ideas and solutions through imagination and divergent thinking."),
    ("Adaptability",           "Adjusting behaviors, mindsets, and approaches to thrive in changing environments."),
    ("Leadership",             "Guiding, inspiring, and developing others to achieve individual and collective goals."),
    ("Emotional Intelligence", "Recognizing, understanding, and managing one's own emotions and the emotions of others."),
    ("Resilience",             "The capacity to recover from setbacks, adapt to adversity, and maintain momentum under pressure."),
    ("Critical Thinking",      "Applying logical, analytical, and evaluative thinking to assess information and solve problems."),
    ("Decision Making",        "Making sound, timely, and well-reasoned choices based on data, context, and values."),
    ("Time Management",        "Prioritizing tasks, managing competing demands, and organizing effort to deliver consistent results."),
    ("Cultural Competence",    "Working effectively and respectfully with individuals from diverse backgrounds, cultures, and perspectives."),
    ("Conflict Resolution",    "Addressing and resolving interpersonal and group conflicts in a constructive, relationship-preserving way."),
    ("Systems Leadership",     "Guiding complex systems by understanding interdependencies, building coalitions, and aligning action to strategy."),
    ("Interpersonal Dexterity","Influencing, persuading, and navigating relationships at and across levels of leadership."),
]

# ── Sub-Skills (each tuple: name, definition) ─────────────────────────────────
SUB_SKILLS = {
    "Empathy": [
        ("Active Listening",       "Fully focusing on the speaker, understanding their message, and responding thoughtfully to foster deeper communication."),
        ("Perspective-taking",     "Viewing situations from the perspective of others to understand their feelings and viewpoints."),
        ("Emotional Awareness",    "Recognizing and understanding one's own and others' emotions in real time."),
        ("Non-Verbal Communication","Communicating and interpreting emotions and intentions through body language, gestures, and facial expressions."),
        ("Cultural Sensitivity",   "Being aware of and respectful toward the cultural differences and norms of others."),
    ],
    "Communication": [
        ("Verbal Communication",    "Expressing ideas and information clearly and effectively through spoken words."),
        ("Written Communication",   "Conveying information and ideas through written words with clarity, tone, and purpose."),
        ("Non-Verbal Communication","Communicating through body language, gestures, and facial expressions without using words."),
        ("Public Speaking",         "Delivering effective and engaging speeches or presentations to an audience."),
        ("Storytelling",            "Creating and delivering compelling narratives to convey messages and engage listeners."),
        ("Persuasion",              "Convincing and influencing others by presenting arguments and ideas in a compelling way."),
        ("Confidence",              "Demonstrating self-assuredness and certainty when communicating, conveying authority and instilling trust."),
        ("Gravitas",                "Projecting authority and seriousness through body language, tone, and communication style to command respect."),
        ("Questioning Techniques",  "Crafting purposeful questions that elicit meaningful information, clarify misunderstandings, and promote deeper dialogue."),
        ("Influence",               "Guiding and motivating others by building relationships, gaining trust, and presenting persuasive arguments."),
    ],
    "Collaboration": [
        ("Teamwork",                  "Collaborating and cooperating with team members to achieve common goals."),
        ("Conflict Resolution",       "Addressing and resolving disputes or conflicts within teams or organizations."),
        ("Task Delegation",           "Assigning tasks and responsibilities to team members based on their skills and capabilities."),
        ("Communication Within a Team","Effectively communicating and sharing information within a team to ensure alignment."),
        ("Building Trust",            "Establishing trust and rapport with team members to foster a positive working environment."),
        ("Project Management",        "Planning, executing, and overseeing projects to achieve specific objectives within scope and timeline."),
    ],
    "Teamwork": [
        ("Collaboration",              "Working jointly with others to achieve shared goals through mutual support and contribution."),
        ("Cooperation",                "Working harmoniously with team members by sharing responsibilities and maintaining a team-first mindset."),
        ("Shared Accountability",      "Taking collective ownership of team outcomes rather than attributing success or failure to individuals alone."),
        ("Team Cohesion",              "Building unity and trust within a team through consistent communication, respect, and shared norms."),
        ("Cross-Functional Collaboration","Working effectively with colleagues from different departments or disciplines toward a common goal."),
    ],
    "Problem Solving": [
        ("Analytical Thinking",       "Evaluating complex situations and problems by breaking them down into manageable components."),
        ("Decision-Making",           "Making choices and decisions based on careful consideration of available information and options."),
        ("Creativity and Innovation", "Generating new and original ideas to address challenges and improve processes."),
        ("Research Skills",           "Gathering, evaluating, and synthesizing data and information to support problem-solving."),
        ("Critical Thinking",         "Applying logical and objective analysis to evaluate assumptions and solve problems."),
        ("Data Analysis",             "Examining data to extract meaningful insights and inform sound decision-making."),
        ("Financial Literacy",        "Understanding key financial concepts and interpreting financial data to guide strategic business decisions."),
        ("Creative Problem-Solving",  "Using imaginative and non-linear thinking approaches to find unique solutions to challenges."),
        ("Problem Analysis",          "Identifying root causes and underlying dimensions of complex problems before acting."),
    ],
    "Creativity": [
        ("Ideation",                        "Developing and generating new and innovative ideas through divergent thinking."),
        ("Brainstorming",                   "Encouraging creative thinking and idea generation through structured group or individual exploration."),
        ("Design Thinking",                 "Applying a human-centered approach to solve problems and create innovative, empathetic solutions."),
        ("Problem-Solving Through Creativity","Using creative thinking to address challenges and find unconventional, effective solutions."),
    ],
    "Adaptability": [
        ("Change Management",  "Planning and executing strategies to navigate organizational transitions with minimal disruption."),
        ("Flexibility",        "Adjusting approaches, behaviors, and thinking to suit changing conditions and emerging requirements."),
        ("Stress Management",  "Identifying and managing stressors to maintain wellbeing and performance under pressure."),
        ("Resilience",         "Recovering quickly from setbacks while maintaining a positive, forward-focused outlook."),
        ("Learning Agility",   "Rapidly learning new skills and knowledge from experience, applying insights to improve future outcomes."),
    ],
    "Leadership": [
        ("Vision-Setting",                    "Establishing a clear, compelling direction for a team or organization that inspires action."),
        ("Motivation",                        "Inspiring and energizing others to achieve goals and reach their full potential."),
        ("Delegation",                        "Assigning tasks and authority to others to develop capability and improve team outcomes."),
        ("Coaching and Mentoring",            "Supporting the growth and development of others through structured guidance and developmental conversations."),
        ("Feedback Techniques",               "Providing specific, timely, and actionable feedback that fosters growth and strengthens performance."),
        ("Conflict Resolution",               "Navigating and resolving interpersonal and group conflicts constructively and relationally."),
        ("Decision-Making",                   "Making sound, timely decisions that weigh multiple factors and consider stakeholder impact."),
        ("Leadership through Influence",      "Guiding others without direct authority through credibility, trust, and relationship-building."),
        ("Credibility",                       "Building trust and respect through consistent, ethical, and competent leadership behavior."),
        ("Trustworthiness",                   "Demonstrating honesty, reliability, and integrity in all leadership actions and commitments."),
        ("Feedback",                          "Giving and receiving developmental feedback effectively to drive personal and team growth."),
        ("Inspiration",                       "Energizing and motivating others toward a shared vision through authentic leadership presence."),
        ("Ethical Leadership",                "Leading with a strong moral compass, fairness, and integrity even in complex or high-pressure situations."),
        ("Stewardship",                       "Taking responsibility for resources, people, and the organizational mission with care and accountability."),
        ("Building Community",                "Fostering belonging, shared purpose, and meaningful connection within and across teams."),
        ("Psychological Safety",              "Creating an environment where people feel safe to speak up, take risks, and share ideas without fear."),
        ("Empowering and Developing Leaders", "Identifying and growing leadership capacity in others by creating stretch opportunities and coaching."),
        ("Ethical Influence",                 "Guiding the decisions and actions of others through principled, transparent persuasion."),
    ],
    "Emotional Intelligence": [
        ("Self-Awareness",       "Recognizing and understanding one's own emotions, triggers, strengths, and limitations."),
        ("Self-Regulation",      "Managing and controlling one's emotions and impulses effectively, especially under pressure."),
        ("Social Awareness",     "Reading the emotional environment and accurately understanding others' feelings and perspectives."),
        ("Relationship Management","Building, maintaining, and leveraging positive, productive relationships with others."),
    ],
    "Resilience": [
        ("Stress Management",   "Identifying and managing stressors to sustain wellbeing and performance under pressure."),
        ("Optimism",            "Maintaining a positive, forward-looking outlook even in challenging or uncertain situations."),
        ("Perseverance",        "Continuing to pursue goals and commitments despite obstacles, setbacks, or adversity."),
        ("Adaptation to Change","Adjusting effectively to new situations, challenges, and environments without losing momentum."),
    ],
    "Critical Thinking": [
        ("Analytical Reasoning",    "Systematically examining evidence and arguments to reach well-supported logical conclusions."),
        ("Problem Analysis",        "Identifying root causes and underlying dimensions of complex problems before taking action."),
        ("Logical Reasoning",       "Drawing valid conclusions from premises using structured, coherent thinking."),
        ("Inference",               "Drawing sound conclusions from available evidence, patterns, and contextual signals."),
        ("Evaluation of Evidence",  "Assessing the validity, reliability, and relevance of information before acting on it."),
    ],
    "Decision Making": [
        ("Risk Assessment",              "Identifying, analyzing, and evaluating potential risks and their likelihood and impact."),
        ("Data-Driven Decision-Making",  "Using quantitative and qualitative data to inform, validate, and strengthen decisions."),
        ("Ethical Decision-Making",      "Considering moral principles, stakeholder impact, and organizational values when making decisions."),
        ("Prioritization",               "Determining the relative importance and urgency of competing tasks, goals, or initiatives."),
        ("Analytical Thinking",          "Evaluating complex situations by breaking them into manageable components to surface the best path forward."),
    ],
    "Time Management": [
        ("Prioritization",           "Determining the relative importance and urgency of tasks to focus effort where it matters most."),
        ("Procrastination Management","Recognizing and overcoming tendencies to delay or avoid important tasks and commitments."),
        ("Task Organization",        "Structuring and sequencing tasks logically to maximize efficiency and consistency of delivery."),
        ("Goal Setting",             "Establishing clear, specific, measurable objectives that guide focused effort and track progress."),
        ("Productivity Techniques",  "Applying proven methods and tools to increase output quality and reduce wasted effort."),
    ],
    "Cultural Competence": [
        ("Cultural Sensitivity",        "Recognizing and respecting cultural differences in values, beliefs, communication styles, and practices."),
        ("Inclusion",                   "Creating environments where diverse individuals feel valued, respected, and able to contribute fully."),
        ("Diversity Awareness",         "Understanding the range of human differences and their meaningful impact on workplace dynamics."),
        ("Cross-Cultural Communication","Communicating effectively and respectfully with people from different cultural backgrounds."),
        ("Perspective-Taking",          "Viewing situations through others' cultural viewpoints to build deeper empathy and understanding."),
    ],
    "Conflict Resolution": [
        ("Mediation",                  "Facilitating negotiation and agreement between conflicting parties in a neutral, structured way."),
        ("Negotiation",                "Reaching mutually beneficial agreements through constructive dialogue, compromise, and respect."),
        ("De-escalation",              "Reducing emotional intensity and tension in conflict situations before they compound."),
        ("Active Listening",           "Fully attending to all parties' perspectives during conflict to ensure each person feels heard."),
        ("Collaborative Problem-Solving","Working jointly with all parties to find solutions that satisfy needs and preserve relationships."),
    ],
    "Systems Leadership": [
        ("Systems Thinking",                  "Understanding how components of a complex system interact and create emergent outcomes."),
        ("Collaborative Leadership",          "Building cross-functional relationships and leading effectively through partnership and shared ownership."),
        ("Coalition Building",                "Creating alliances and networks across the organization to advance shared strategic goals."),
        ("Strategic Alignment",               "Ensuring team and organizational efforts align with broader strategy, priorities, and values."),
        ("Strategic Delegation",              "Assigning responsibilities to build organizational capability and advance mission-critical goals."),
        ("Evaluation and Continuous Improvement","Assessing outcomes systematically and refining approaches to optimize organizational performance."),
    ],
    "Interpersonal Dexterity": [
        ("Influencing and Persuading Other Leaders","Engaging and winning support from peer and senior leaders through credibility and well-reasoned arguments."),
        ("Conflict Resolution Among Leaders",       "Navigating disagreements between leaders constructively and without damaging relationships."),
    ],
}

# ── Sessions (number, title, primary_skills, sub_skills, role, manager_only) ──
SESSIONS = [
    (1,  "Effective Communication",
         "Communication, Empathy",
         "Active Listening, Verbal Communication, Non-Verbal Communication",
         "Mgr, NM, IC",  False),

    (2,  "Building Strong Team Dynamics",
         "Teamwork, Collaboration",
         "Building Trust, Conflict Resolution, Communication Within a Team, Team Cohesion",
         "Mgr, NM, IC",  False),

    (3,  "Managing Stress in the Workplace",
         "Adaptability, Resilience",
         "Stress Management, Resilience, Perseverance, Adaptation to Change",
         "Mgr, IC",      False),

    (4,  "Problem Solving",
         "Problem Solving",
         "Problem Analysis, Analytical Thinking, Decision-Making, Creative Problem-Solving",
         "Mgr, NM, IC",  False),

    (5,  "Time Management",
         "Time Management, Decision Making",
         "Prioritization, Procrastination Management, Task Organization, Goal Setting",
         "Mgr, IC",      False),

    (6,  "Critical Thinking",
         "Critical Thinking, Problem Solving",
         "Analytical Reasoning, Logical Reasoning, Problem Analysis, Evaluation of Evidence",
         "Mgr, NM, IC",  False),

    (7,  "Elevate Emotional Intelligence",
         "Emotional Intelligence, Empathy",
         "Self-Awareness, Social Awareness, Relationship Management, Self-Regulation",
         "Mgr, NM, IC",  False),

    (8,  "Resilience Leadership",
         "Resilience",
         "Stress Management, Perseverance, Optimism, Adaptation to Change",
         "Mgr, NM, IC",  False),

    (9,  "Empathy and Compassion at Work",
         "Empathy, Emotional Intelligence",
         "Perspective-taking, Emotional Awareness, Cultural Sensitivity, Active Listening",
         "Mgr, NM, IC",  False),

    (10, "Develop a Culture of Inclusion",
         "Cultural Competence, Empathy",
         "Cultural Sensitivity, Perspective-taking, Inclusion, Diversity Awareness",
         "Mgr, IC, NM",  False),

    (11, "Coaching and Feedback",
         "Leadership, Communication",
         "Coaching and Mentoring, Feedback Techniques, Active Listening, Feedback",
         "Mgr, NM, IC",  False),

    (12, "Conflict Resolution and Management",
         "Conflict Resolution, Emotional Intelligence",
         "Mediation, Negotiation, Collaborative Problem-Solving, De-escalation",
         "Mgr, NM, IC",  False),

    (13, "Foster Collaboration",
         "Collaboration, Teamwork",
         "Communication Within a Team, Building Trust, Task Delegation, Shared Accountability",
         "Mgr, IC, NM",  False),

    (14, "Motivating People for Performance",
         "Leadership",
         "Motivation, Vision-Setting, Inspiration, Ethical Leadership",
         "Mgr, IC, NM",  False),

    (15, "Managing Change",
         "Adaptability",
         "Change Management, Flexibility, Resilience, Learning Agility",
         "Mgr, NM, IC",  False),

    (16, "Strategic Decision-Making",
         "Decision Making, Problem Solving",
         "Risk Assessment, Data-Driven Decision-Making, Ethical Decision-Making, Analytical Thinking",
         "Mgr, NM, IC",  False),

    (17, "Creative Thinking and Innovation",
         "Creativity, Problem Solving",
         "Ideation, Brainstorming, Design Thinking, Creativity and Innovation",
         "Mgr, NM, IC",  False),

    (18, "Productivity and Organizational Skills",
         "Time Management, Collaboration",
         "Task Delegation, Project Management, Productivity Techniques, Goal Setting",
         "Mgr, IC",      False),

    (19, "Executive Presence",
         "Leadership, Communication",
         "Credibility, Gravitas, Influence, Trustworthiness",
         "Mgr, IC, NM",  False),

    (20, "Leadership Essentials",
         "Leadership",
         "Vision-Setting, Delegation, Decision-Making, Ethical Leadership, Leadership through Influence",
         "Mgr, NM, IC",  False),

    (21, "Systems Leadership",
         "Systems Leadership",
         "Systems Thinking, Collaborative Leadership, Strategic Alignment, Coalition Building",
         "Mgr only",     True),

    (22, "Interviewing with Impact",
         "Communication, Empathy, Decision Making",
         "Confidence, Active Listening, Questioning Techniques, Non-Verbal Communication",
         "Any",          False),

    (23, "Leading Difficult Conversations",
         "Communication, Empathy",
         "Empathy, Conflict Resolution, Emotional Intelligence, Relationship Management",
         "Mgr, NM, IC",  False),

    (24, "Digital Leadership",
         "Leadership, Communication, Collaboration",
         "Vision-Setting, Communication Within a Team, Building Trust, Delegation",
         "Mgr only",     True),

    (25, "Negotiation and Influence",
         "Communication, Conflict Resolution",
         "Influence, Negotiation, Persuasion, Credibility, Active Listening",
         "Mgr, IC",      False),

    (26, "Maximizing the Impact of 1:1 Conversations",
         "Communication, Emotional Intelligence, Empathy",
         "Questioning Techniques, Relationship Management, Feedback, Perspective-taking",
         "Mgr, NM, IC",  False),

    (27, "Business Acumen",
         "Problem Solving, Critical Thinking, Decision Making",
         "Financial Literacy, Data Analysis, Research Skills, Analytical Thinking",
         "Mgr, IC",      False),

    (28, "Transformational Leadership",
         "Leadership, Communication",
         "Inspiration, Vision-Setting, Empowering and Developing Leaders, Building Community",
         "Mgr only",     True),

    (29, "Leading Other Leaders",
         "Leadership, Interpersonal Dexterity, Systems Leadership",
         "Influencing and Persuading Other Leaders, Conflict Resolution Among Leaders, Strategic Delegation",
         "Mgr only",     True),

    (30, "Storytelling and Persuasion",
         "Communication",
         "Storytelling, Persuasion, Confidence, Gravitas",
         "IC, Mgr",      False),

    (31, "Public Speaking",
         "Communication",
         "Public Speaking, Confidence, Non-Verbal Communication, Gravitas",
         "IC, Mgr",      False),

    (32, "Servant Leadership",
         "Leadership, Emotional Intelligence",
         "Psychological Safety, Empowering and Developing Leaders, Building Community, Stewardship",
         "Mgr only",     True),

    (33, "Succession Planning I",
         "Problem Solving, Leadership, Systems Leadership",
         "Strategic Delegation, Evaluation and Continuous Improvement, Systems Thinking",
         "Mgr only",     True),

    (34, "Succession Planning II",
         "Leadership, Collaboration, Communication",
         "Empowering and Developing Leaders, Building Community, Coalition Building",
         "Mgr only",     True),
]

# ── Pathways ───────────────────────────────────────────────────────────────────
PATHWAYS = [
    {
        "name": "Manager Foundations",
        "role": "Manager",
        "description": "Lay the groundwork for effective management with a focus on building essential skills to lead with clarity, empathy, and impact.",
        "sessions": [
            "Effective Communication",
            "Building Strong Team Dynamics",
            "Elevate Emotional Intelligence",
            "Problem Solving",
            "Critical Thinking",
            "Executive Presence",
        ],
    },
    {
        "name": "Strategic Leadership",
        "role": "Manager",
        "description": "Navigate complex challenges with clarity, empathy, and innovation. Cultivate essential leadership skills to inspire and motivate your team.",
        "sessions": [
            "Leadership Essentials",
            "Empathy and Compassion at Work",
            "Resilience Leadership",
            "Conflict Resolution and Management",
            "Strategic Decision-Making",
            "Creative Thinking and Innovation",
        ],
    },
    {
        "name": "Leading Teams to Success",
        "role": "Manager",
        "description": "Empower your team to thrive by creating an inclusive, motivated, and high-performing environment.",
        "sessions": [
            "Develop a Culture of Inclusion",
            "Motivating People for Performance",
            "Coaching and Feedback",
            "Managing Change",
            "Leading Difficult Conversations",
            "Maximizing the Impact of 1:1 Conversations",
        ],
    },
    {
        "name": "Driving Execution",
        "role": "Manager",
        "description": "Enhance your ability to execute with precision, focus, and impact. Build resilience, negotiate with confidence, and create a culture of productivity.",
        "sessions": [
            "Business Acumen",
            "Time Management",
            "Productivity and Organizational Skills",
            "Managing Stress in the Workplace",
            "Negotiation and Influence",
            "Foster Collaboration",
        ],
    },
    {
        "name": "Future-Forward Leadership",
        "role": "Manager",
        "description": "Prepare to lead in a rapidly changing world by mastering the skills that define forward-thinking leadership.",
        "sessions": [
            "Digital Leadership",
            "Systems Leadership",
            "Transformational Leadership",
            "Servant Leadership",
            "Leading Other Leaders",
        ],
    },
    {
        "name": "New Manager Foundations",
        "role": "New Manager",
        "description": "Transition successfully from individual contributor to people manager with the essential foundations of leadership.",
        "sessions": [
            "Effective Communication",
            "Building Strong Team Dynamics",
            "Elevate Emotional Intelligence",
            "Problem Solving",
            "Critical Thinking",
            "Executive Presence",
        ],
    },
    {
        "name": "Essential Workplace Skills",
        "role": "Individual Contributor",
        "description": "Build the core human-centered skills that make you a more effective, collaborative, and impactful contributor.",
        "sessions": [
            "Effective Communication",
            "Building Strong Team Dynamics",
            "Elevate Emotional Intelligence",
            "Resilience Leadership",
            "Empathy and Compassion at Work",
            "Foster Collaboration",
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed Bundle taxonomy, sessions, and pathways into the database'

    def handle(self, *args, **options):
        self.stdout.write("Seeding Bundle taxonomy...")

        # Clear existing data
        Pathway.objects.all().delete()
        Session.objects.all().delete()
        SubSkill.objects.all().delete()
        PrimarySkill.objects.all().delete()

        # Seed primary skills
        skill_objects = {}
        for name, definition in PRIMARY_SKILLS:
            skill = PrimarySkill.objects.create(name=name, definition=definition)
            skill_objects[name] = skill
        self.stdout.write(f"  OK: {len(PRIMARY_SKILLS)} primary skills created")

        # Seed sub-skills (each item is a (name, definition) tuple)
        sub_count = 0
        for skill_name, sub_list in SUB_SKILLS.items():
            parent = skill_objects.get(skill_name)
            if parent:
                for item in sub_list:
                    if isinstance(item, tuple):
                        sub_name, sub_def = item
                    else:
                        sub_name, sub_def = item, ""
                    SubSkill.objects.create(
                        primary_skill=parent,
                        name=sub_name,
                        definition=sub_def,
                    )
                    sub_count += 1
        self.stdout.write(f"  OK: {sub_count} sub-skills created")

        # Seed sessions (num, title, primary_skills, sub_skills, role, manager_only)
        for num, title, primary_skills, sub_skills, role_applicability, is_manager_only in SESSIONS:
            Session.objects.create(
                session_number=num,
                title=title,
                primary_skills_text=primary_skills,
                sub_skills_text=sub_skills,
                role_applicability=role_applicability,
                is_manager_only=is_manager_only,
            )
        self.stdout.write(f"  OK: {len(SESSIONS)} sessions created")

        # Seed pathways
        for pathway_data in PATHWAYS:
            Pathway.objects.create(
                name=pathway_data["name"],
                role=pathway_data["role"],
                description=pathway_data["description"],
                session_titles="\n".join(pathway_data["sessions"]),
            )
        self.stdout.write(f"  OK: {len(PATHWAYS)} pathways created")

        self.stdout.write("Database ready.")
