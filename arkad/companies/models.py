from django.contrib.postgres.fields import ArrayField
from django.db import models

DEGREE_CHOICES = [("Bachelor", "Bachelor"), ("Master", "Master"), ("PhD", "PhD")]

COMPETENCE_CHOICES = [
    ("Architecture", "Architecture"),
    ("ArtificialIntelligence", "Artificial Intelligence"),
    ("Usability", "Usability"),
    ("Applications", "Applications"),
    ("Automation", "Automation"),
    ("Computation", "Computation"),
    ("FireSafety", "Fire Safety"),
    ("ComputerSecurity", "Computer Security"),
    ("Design", "Design"),
    ("EHealth", "E-Health"),
    ("Electronics", "Electronics"),
    ("EnergySystems", "Energy Systems"),
    ("Law", "Law"),
    ("Finance", "Finance"),
    ("Geography", "Geography"),
    ("Sustainability", "Sustainability"),
    ("IndustrialProcesses", "Industrial Processes"),
    ("Interactivity", "Interactivity"),
    ("Chemistry", "Chemistry"),
    ("Communications", "Communications"),
    ("Construction", "Construction"),
    ("FoodTechnology", "Food Technology"),
    ("PharmaceuticalTechnology", "Pharmaceutical Technology"),
    ("MathematicalModelling", "Mathematical Modelling"),
    ("MaterialsEngineering", "Materials Engineering"),
    ("LifeScience", "Life Science"),
    ("Mechatronics", "Mechatronics"),
    ("AccidentPrevention", "Accident Prevention"),
    ("ProductDevelopment", "Product Development"),
    ("Programming", "Programming"),
    ("Planning", "Planning"),
    ("ProjectManagement", "Project Management"),
    ("RiskManagement", "Risk Management"),
    ("TechnologyAndSociety", "Technology and Society"),
    ("CivilEngineering", "Civil Engineering"),
    ("Simulations", "Simulations"),
    ("Manufacturing", "Manufacturing"),
    ("InterdisciplinaryCompetences", "Interdisciplinary Competences"),
    ("Physics", "Physics"),
]

POSITION_CHOICES = [
    ("Thesis", "Thesis"),
    ("TraineeEmployment", "Trainee Employment"),
    ("Internship", "Internship"),
    ("SummerJob", "Summer Job"),
    ("ForeignOppurtunity", "Foreign Opportunity"),
    ("PartTime", "Part Time"),
]

INDUSTRY_CHOICES = [
    ("ElectricityEnergyPower", "Electricity Energy Power"),
    ("Environment", "Environment"),
    ("BankingFinance", "Banking Finance"),
    ("Union", "Union"),
    ("Investment", "Investment"),
    ("Insurance", "Insurance"),
    ("Recruitment", "Recruitment"),
    ("Construction", "Construction"),
    ("Architecture", "Architecture"),
    ("GraphicDesign", "Graphic Design"),
    ("DataIT", "Data IT"),
    ("FinanceConsultancy", "Finance Consultancy"),
    ("Telecommunication", "Telecommunication"),
    ("Consulting", "Consulting"),
    ("Management", "Management"),
    ("Media", "Media"),
    ("Industry", "Industry"),
    ("NuclearPower", "Nuclear Power"),
    ("LifeScience", "Life Science"),
    ("MedicalTechniques", "Medical Techniques"),
    ("PropertyInfrastructure", "Property Infrastructure"),
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
    )  # List of degrees with enforced choices
    desired_programme = ArrayField(
        models.CharField(max_length=255), default=list, blank=True
    )  # List of programmes
    desired_competences = ArrayField(
        models.CharField(max_length=50, choices=COMPETENCE_CHOICES),
        default=list,
        blank=True,
    )  # List of competences with enforced choices
    positions = ArrayField(
        models.CharField(max_length=50, choices=POSITION_CHOICES),
        default=list,
        blank=True,
    )  # List of positions with enforced choices
    industries = ArrayField(
        models.CharField(max_length=50, choices=INDUSTRY_CHOICES),
        default=list,
        blank=True,
    )  # List of industries with enforced choices

    employees_locally = models.IntegerField(default=None, null=True, blank=True)
    employees_globally = models.IntegerField(default=None, null=True, blank=True)

    jobs = models.ManyToManyField(Job)

    def __str__(self):
        return self.name
