from django.core.management.base import BaseCommand
from builder.models import PrimarySkill, SubSkill, Session, Pathway


PRIMARY_SKILLS = [
    ("Empathy", "Understanding and sharing the feelings of others."),
    ("Communication", "The ability to convey information effectively."),
    ("Collaboration", "Working effectively with others to achieve goals."),
    ("Teamwork", "Working collaboratively within a team to achieve common goals."),
    ("Problem Solving", "Analyzing and resolving complex issues and challenges."),
    ("Creativity", "Generating novel ideas and solutions."),
    ("Adaptability", "Adjusting and thriving in changing environments."),
    ("Leadership", "Guiding and inspiring others to achieve common goals."),
    ("Emotional Intelligence", "Recognizing, understanding, and managing one's own emotions and the emotions of others."),
    ("Resilience", "The ability to bounce back from setbacks and adapt to adversity."),
    ("Critical Thinking", "Applying logical and analytical thinking to problems."),
    ("Decision Making", "Making sound and timely decisions based on data, information, and judgment."),
    ("Time Management", "Prioritizing tasks, allocating resources, and managing one's time effectively."),
    ("Cultural Competence", "Working effectively with individuals from diverse backgrounds and cultures."),
    ("Conflict Resolution", "Addressing and resolving conflicts effectively."),
    ("Systems Leadership", "Guiding and influencing complex systems by understanding interactions between components, fostering collaboration, building partnerships, and aligning actions with the organization's vision."),
    ("Interpersonal Dexterity", "Influencing, persuading, and navigating relationships at and across levels of leadership."),
]

SUB_SKILLS = {
    "Empathy": [
        "Active Listening", "Perspective-taking", "Emotional Awareness",
        "Non-Verbal Communication", "Cultural Sensitivity",
    ],
    "Communication": [
        "Verbal Communication", "Written Communication", "Non-Verbal Communication",
        "Public Speaking", "Storytelling", "Persuasion", "Confidence", "Gravitas",
        "Questioning Techniques", "Influence",
    ],
    "Collaboration": [
        "Teamwork", "Conflict Resolution", "Task Delegation",
        "Communication Within a Team", "Building Trust", "Project Management",
    ],
    "Problem Solving": [
        "Analytical Thinking", "Decision-Making", "Creativity and Innovation",
        "Critical Thinking", "Data Analysis", "Financial Literacy", "Research Skills",
    ],
    "Creativity": [
        "Ideation", "Brainstorming", "Design Thinking", "Problem-Solving Through Creativity",
    ],
    "Adaptability": [
        "Change Management", "Flexibility", "Stress Management",
        "Resilience", "Learning Agility",
    ],
    "Leadership": [
        "Vision-Setting", "Motivation", "Delegation", "Coaching and Mentoring",
        "Conflict Resolution", "Decision-Making", "Leadership through Influence",
        "Credibility", "Trustworthiness", "Feedback", "Inspiration", "Ethical Leadership",
        "Stewardship", "Building Community", "Psychological Safety",
        "Empowering and Developing Leaders", "Ethical Influence",
    ],
    "Emotional Intelligence": [
        "Self-Awareness", "Self-Regulation", "Social Awareness", "Relationship Management",
    ],
    "Resilience": [
        "Stress Management", "Optimism", "Perseverance", "Adaptation to Change",
    ],
    "Critical Thinking": [
        "Analytical Reasoning", "Problem Analysis", "Logical Reasoning",
        "Inference", "Evaluation of Evidence",
    ],
    "Systems Leadership": [
        "Systems Thinking", "Collaborative Leadership", "Coalition Building",
        "Strategic Alignment", "Strategic Delegation", "Evaluation and Continuous Improvement",
    ],
    "Interpersonal Dexterity": [
        "Influencing and Persuading Other Leaders", "Conflict Resolution Among Leaders",
    ],
}

SESSIONS = [
    (1,  "Effective Communication",                      "Communication, Empathy",                                       "Mgr, NM, IC",  False),
    (2,  "Building Strong Team Dynamics",                "Teamwork, Collaboration",                                      "Mgr, NM, IC",  False),
    (3,  "Managing Stress in the Workplace",             "Adaptability, Resilience",                                     "Mgr, IC",      False),
    (4,  "Problem Solving",                              "Problem Solving",                                              "Mgr, NM, IC",  False),
    (5,  "Time Management",                              "Time Management, Decision Making",                             "Mgr, IC",      False),
    (6,  "Critical Thinking",                            "Critical Thinking, Problem Solving",                           "Mgr, NM, IC",  False),
    (7,  "Elevate Emotional Intelligence",               "Emotional Intelligence, Empathy",                              "Mgr, NM, IC",  False),
    (8,  "Resilience Leadership",                        "Resilience",                                                   "Mgr, NM, IC",  False),
    (9,  "Empathy and Compassion at Work",               "Empathy, Emotional Intelligence",                              "Mgr, NM, IC",  False),
    (10, "Develop a Culture of Inclusion",               "Cultural Competence, Empathy",                                 "Mgr, IC, NM",  False),
    (11, "Coaching and Feedback",                        "Leadership, Communication",                                    "Mgr, NM, IC",  False),
    (12, "Conflict Resolution and Management",           "Conflict Resolution, Emotional Intelligence",                  "Mgr, NM, IC",  False),
    (13, "Foster Collaboration",                         "Collaboration, Teamwork",                                      "Mgr, IC, NM",  False),
    (14, "Motivating People for Performance",            "Leadership",                                                   "Mgr, IC, NM",  False),
    (15, "Managing Change",                              "Adaptability",                                                 "Mgr, NM, IC",  False),
    (16, "Strategic Decision-Making",                    "Decision Making, Problem Solving",                             "Mgr, NM, IC",  False),
    (17, "Creative Thinking and Innovation",             "Creativity, Problem Solving",                                  "Mgr, NM, IC",  False),
    (18, "Productivity and Organizational Skills",       "Time Management, Collaboration",                               "Mgr, IC",      False),
    (19, "Executive Presence",                           "Leadership, Communication",                                    "Mgr, IC, NM",  False),
    (20, "Leadership Essentials",                        "Leadership",                                                   "Mgr, NM, IC",  False),
    (21, "Systems Leadership",                           "Systems Leadership",                                           "Mgr only",     True),
    (22, "Interviewing with Impact",                     "Communication, Empathy, Decision Making",                      "Any",          False),
    (23, "Leading Difficult Conversations",              "Communication, Empathy",                                       "Mgr, NM, IC",  False),
    (24, "Digital Leadership",                           "Leadership, Communication, Collaboration",                     "Mgr only",     True),
    (25, "Negotiation and Influence",                    "Communication, Conflict Resolution",                           "Mgr, IC",      False),
    (26, "Maximizing the Impact of 1:1 Conversations",  "Communication, Emotional Intelligence, Empathy",               "Mgr, NM, IC",  False),
    (27, "Business Acumen",                              "Problem Solving, Critical Thinking, Decision Making",          "Mgr, IC",      False),
    (28, "Transformational Leadership",                  "Leadership, Communication",                                    "Mgr only",     True),
    (29, "Leading Other Leaders",                        "Leadership, Interpersonal Dexterity, Systems Leadership",      "Mgr only",     True),
    (30, "Storytelling and Persuasion",                  "Communication",                                                "IC, Mgr",      False),
    (31, "Public Speaking",                              "Communication",                                                "IC, Mgr",      False),
    (32, "Servant Leadership",                           "Leadership, Emotional Intelligence",                           "Mgr only",     True),
    (33, "Succession Planning I",                        "Problem Solving, Leadership, Systems Leadership",              "Mgr only",     True),
    (34, "Succession Planning II",                       "Leadership, Collaboration, Communication",                     "Mgr only",     True),
]

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
        self.stdout.write(f"  ✓ {len(PRIMARY_SKILLS)} primary skills created")

        # Seed sub-skills
        sub_count = 0
        for skill_name, sub_names in SUB_SKILLS.items():
            parent = skill_objects.get(skill_name)
            if parent:
                for sub_name in sub_names:
                    SubSkill.objects.create(primary_skill=parent, name=sub_name)
                    sub_count += 1
        self.stdout.write(f"  ✓ {sub_count}+ sub-skills created")

        # Seed sessions
        for num, title, primary_skills, role_applicability, is_manager_only in SESSIONS:
            Session.objects.create(
                session_number=num,
                title=title,
                primary_skills_text=primary_skills,
                role_applicability=role_applicability,
                is_manager_only=is_manager_only,
            )
        self.stdout.write(f"  ✓ {len(SESSIONS)} sessions created")

        # Seed pathways
        for pathway_data in PATHWAYS:
            Pathway.objects.create(
                name=pathway_data["name"],
                role=pathway_data["role"],
                description=pathway_data["description"],
                session_titles="\n".join(pathway_data["sessions"]),
            )
        self.stdout.write(f"  ✓ {len(PATHWAYS)} pathways created")

        self.stdout.write("Database ready.")
