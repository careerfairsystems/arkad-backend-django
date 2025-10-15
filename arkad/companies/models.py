from django.contrib.postgres.fields import ArrayField
from django.db import models

DEGREE_CHOICES = [("Bachelor", "Bachelor"), ("Master", "Master"), ("PhD", "PhD")]

COMPETENCE_CHOICES = [
    ("Architecture", "Architecture"),
    ("Artificial Intelligence", "Artificial Intelligence"),
    ("Usability", "Usability"),
    ("Applications", "Applications"),
    ("Automation", "Automation"),
    ("Computation", "Computation"),
    ("Fire Safety", "Fire Safety"),
    ("Computer Security", "Computer Security"),
    ("Design", "Design"),
    ("E-Health", "E-Health"),
    ("Electronics", "Electronics"),
    ("Energy Systems", "Energy Systems"),
    ("Law", "Law"),
    ("Finance", "Finance"),
    ("Geography", "Geography"),
    ("Sustainability", "Sustainability"),
    ("Industrial Processes", "Industrial Processes"),
    ("Interactivity", "Interactivity"),
    ("Chemistry", "Chemistry"),
    ("Communications", "Communications"),
    ("Construction", "Construction"),
    ("Food Technology", "Food Technology"),
    ("Pharmaceutical Technology", "Pharmaceutical Technology"),
    ("Mathematical Modelling", "Mathematical Modelling"),
    ("Materials Engineering", "Materials Engineering"),
    ("Life Science", "Life Science"),
    ("Mechatronics", "Mechatronics"),
    ("Accident Prevention", "Accident Prevention"),
    ("Product Development", "Product Development"),
    ("Programming", "Programming"),
    ("Planning", "Planning"),
    ("Project Management", "Project Management"),
    ("Risk Management", "Risk Management"),
    ("Technology And Society", "Technology and Society"),
    ("Civil Engineering", "Civil Engineering"),
    ("Simulations", "Simulations"),
    ("Manufacturing", "Manufacturing"),
    ("Interdisciplinary Competences", "Interdisciplinary Competences"),
    ("Physics", "Physics"),
]

POSITION_CHOICES = [
    ("Thesis", "Thesis"),
    ("Trainee Employment", "Trainee Employment"),
    ("Internship", "Internship"),
    ("Summer Job", "Summer Job"),
    ("Foreign Opportunity", "Foreign Opportunity"),
    ("Part Time", "Part Time"),
]

INDUSTRY_CHOICES = [
    ("Electricity Energy Power", "Electricity Energy Power"),
    ("Environment", "Environment"),
    ("Banking Finance", "Banking Finance"),
    ("Union", "Union"),
    ("Investment", "Investment"),
    ("Insurance", "Insurance"),
    ("Recruitment", "Recruitment"),
    ("Construction", "Construction"),
    ("Architecture", "Architecture"),
    ("Graphic Design", "Graphic Design"),
    ("Data IT", "Data IT"),
    ("Finance Consultancy", "Finance Consultancy"),
    ("Telecommunication", "Telecommunication"),
    ("Consulting", "Consulting"),
    ("Management", "Management"),
    ("Media", "Media"),
    ("Industry", "Industry"),
    ("Nuclear Power", "Nuclear Power"),
    ("Life Science", "Life Science"),
    ("Medical Techniques", "Medical Techniques"),
    ("Property Infrastructure", "Property Infrastructure"),
    ("Research", "Research"),
    ("Coaching", "Coaching"),
]


class Job(models.Model):
    link = models.CharField(max_length=400, null=True)
    description = models.TextField(max_length=2000, null=True)
    location = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    job_type = ArrayField(models.CharField(max_length=255), default=list, blank=True)
    title = models.CharField(max_length=500, null=True)

    def __str__(self) -> str:
        return f"{self.title} - {self.job_type}"


class Company(models.Model):
    """Represents a company"""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    did_you_know = models.TextField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    url_linkedin = models.CharField(max_length=255, blank=True, null=True)
    url_instagram = models.CharField(max_length=255, blank=True, null=True)
    url_facebook = models.CharField(max_length=255, blank=True, null=True)
    url_twitter = models.CharField(max_length=255, blank=True, null=True)
    url_youtube = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_email = models.EmailField(blank=True, null=True)
    company_phone = models.CharField(max_length=100, blank=True, null=True)
    student_session_motivation = models.TextField(blank=True, null=True)
    days_with_studentsession = models.IntegerField(default=0)

    # ArrayFields for lists
    desired_degrees = ArrayField(
        models.CharField(max_length=50, choices=DEGREE_CHOICES),
        default=list,
        blank=True,
        help_text=f"Choose from {', '.join([e[0] for e in DEGREE_CHOICES])}",
    )  # List of degrees with enforced choices
    desired_programme = ArrayField(
        models.CharField(max_length=255), default=list, blank=True
    )  # List of programmes
    desired_competences = ArrayField(
        models.CharField(max_length=50, choices=COMPETENCE_CHOICES),
        default=list,
        blank=True,
        help_text=f"Choose from {', '.join([e[0] for e in COMPETENCE_CHOICES])}",
    )  # List of competences with enforced choices
    positions = ArrayField(
        models.CharField(max_length=50, choices=POSITION_CHOICES),
        default=list,
        blank=True,
        help_text=f"Choose from {', '.join([e[0] for e in POSITION_CHOICES])}",
    )  # List of positions with enforced choices
    industries = ArrayField(
        models.CharField(max_length=50, choices=INDUSTRY_CHOICES),
        help_text=f"Choose from {', '.join([e[0] for e in INDUSTRY_CHOICES])}",
        default=list,
        blank=True,
    )  # List of industries with enforced choices

    employees_locally = models.IntegerField(default=None, null=True, blank=True)
    employees_globally = models.IntegerField(default=None, null=True, blank=True)

    jobs = models.ManyToManyField(Job, blank=True)
    visible_in_company_list = models.BooleanField(
        default=True,
        help_text="If false, the company will not be visible in the company list. Useful if a company for example only has a student session.",
    )

    def __str__(self) -> str:
        return self.name
