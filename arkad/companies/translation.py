SWEDISH_TO_ENGLISH: dict[str, str] = {
    # Programme Choices (Swedish to English)
    "Arkitekt": "Architecture",
    "Automation": "Automation",
    "Automotive": "Automotive",
    "Bioteknik": "Biotechnology",
    "Brandingenjörsutbildning": "Fire Protection Engineering",
    "Byggteknik med arkitektur": "Civil Engineering with Architecture",
    "Byggteknik med järnvägsteknik": "Civil Engineering with Railway Engineering",
    "Byggteknik med väg- och trafikteknik": "Civil Engineering with Road and Traffic Engineering",
    "Chemicals": "Chemicals",
    "Computer Science and Engineering": "Computer Science and Engineering",
    "Datateknik": "Computer Engineering",
    "Ekosystemteknik": "Ecosystem Engineering",
    "Electrical Engineering": "Electrical Engineering",
    "Electronics": "Electronics",
    "Elektroteknik": "Electrical Engineering",
    "Engineering Mathematics": "Engineering Mathematics",
    "Engineering Physics": "Engineering Physics",
    "IT Consulting": "IT Consulting",
    "Industridesign": "Industrial Design",
    "Industriell ekonomi": "Industrial Engineering and Management",
    "Informations- och kommunikationsteknik": "Information and Communication Technology",
    "Kemiteknik": "Chemical Engineering",
    "Lantmäteri": "Surveying",
    "Maskinteknik": "Mechanical Engineering",
    "Maskinteknik med teknisk design": "Mechanical Engineering with Technical Design",
    "Mechanical Engineering": "Mechanical Engineering",
    "Medicin och teknik": "Medicine and Technology",
    "Risk": "Risk Management",
    "Teknisk Fysik": "Engineering Physics",
    "Teknisk Matematik": "Engineering Mathematics",
    "Teknisk Nanovetenskap": "Engineering Nanoscience",
    "Väg- och vatttenbyggnad": "Road and Water Engineering",
    # Competence Choices (Swedish to English)
    "Applications": "Applications",
    "Architecture": "Architecture",
    "Chemistry": "Chemistry",
    "Communications": "Communications",
    "Computation": "Computation",
    "Construction": "Construction",
    "Design": "Design",
    "E-Health": "E-Health",
    "Finance": "Finance",
    "Geography": "Geography",
    "Law": "Law",
    "Mechatronics": "Mechatronics",
    "Physics": "Physics",
    "Programming": "Programming",
    "Project Management": "Project Management",
    "Sustainability": "Sustainability",
    "ai": "Artificial Intelligence",
    "applikationer": "Applications",
    "arkitektur": "Architecture",
    "artificiell intelligens": "Artificial Intelligence",
    "automation": "Automation",
    "brandskydd": "Fire Protection",
    "brandsäkerhet": "Fire Protection",  # Unified with brandskydd
    "beräkning": "Computation",
    "datorsäkerhet": "Computer Security",
    "datasäkerhet": "Computer Security",
    "design": "Design",
    "e-hälsa": "E-Health",
    "elektroteknik": "Electrical Engineering",
    "elektronik": "Electronics",
    "energi": "Energy",
    "energisystem": "Energy",  # Unified with energi
    "finans": "Finance",
    "fysik": "Physics",
    "geografi": "Geography",
    "hållbarhet": "Sustainability",
    "industriella processer": "Industrial Processes",
    "industriprocesser": "Industrial Processes",
    "infrastruktur": "Infrastructure",
    "interaktion": "Interaction",
    "interaktivitet": "Interaction",  # Unified with interaktion
    "juridik": "Law",
    "kemi": "Chemistry",
    "kommunikation": "Communications",
    "konstruktion": "Construction",
    "livsmedel": "Food Technology",
    "livsmedelsteknik": "Food Technology",
    "livsvetenskap": "Life Science",
    "logistik": "Logistics",
    "läkemedel": "Pharmaceuticals",
    "läkemedelsteknik": "Pharmaceuticals",  # Unified with läkemedel
    "material": "Materials",
    "materialteknik": "Materials",  # Unified with material
    "matematisk modellering": "Mathematical Modelling",
    "medicinteknik": "Medical Technology",
    "mekatronik": "Mechatronics",
    "modellering": "Mathematical Modelling",  # Unified with matematisk modellering
    "olyckor": "Accident Prevention",  # Unified with olycksförebyggande
    "olycksförebyggande": "Accident Prevention",
    "planering": "Planning",
    "produkt-dev": "Product Development",
    "produktutveckling": "Product Development",
    "programmering": "Programming",
    "projektering": "Project Engineering",
    "projektledning": "Project Management",
    "risk": "Risk Management",
    "riskanalys": "Risk Management",
    "samhälle": "Society",
    "samhällsplanering": "Urban Planning",
    "simulering": "Simulation",
    "simuleringar": "Simulation",  # Unified - singular form
    "teknik och samhälle": "Society",  # Unified with samhälle
    "tillverknings": "Manufacturing",
    "tillverkning": "Manufacturing",
    "tvärvetenskap": "Interdisciplinary",
    "tvärvetenskapliga kompetenser": "Interdisciplinary",  # Unified with tvärvetenskap
    "användarbarhet": "Usability",
    "användbarhet": "Usability",
    "väg- och vattenbyggnad": "Civil Engineering",
    # Position Choices
    "Extrajobb": "Part Time",
    "extrajobb": "Part Time",
    "Foreign Opportunity": "Foreign Opportunity",
    "Full Time": "Full Time",
    "Internship": "Internship",
    "Sommarjobb": "Summer Job",
    "sommarjobb": "Summer Job",
    "Thesis": "Thesis",
    "Trainee Employment": "Trainee Employment",
    "exjobb": "Thesis",
    "Exjobb": "Thesis",
    "Heltidsjobb": "Full Time",
    "heltidsjobb": "Full Time",
    "Praktikplatser": "Internship",
    "praktik": "Internship",
    "Traineeplatser": "Trainee Employment",
    "trainee": "Trainee Employment",
    "Utlandsmöjligheter": "Foreign Opportunity",
    "utlandsmöjlighet": "Foreign Opportunity",
    "deltid": "Part Time",
    # Industry Choices
    "Arkitektur och Grafisk design": "Architecture and Graphic Design",
    "Bank och finans": "Banking and Finance",
    "bank finans": "Banking and Finance",  # Unified
    "Bemanning & Arbetsförmedling": "Staffing and Employment Services",
    "Bygg": "Construction",
    "bygg": "Construction",  # Unified
    "Consulting": "Consulting",
    "konsult": "Consulting",  # Unified
    "Konsultverksamhet": "Consulting",  # Unified
    "Data": "Data and IT",  # Unified with Data and IT
    "data": "Data and IT",  # Unified
    "Data and IT": "Data and IT",
    "data IT": "Data and IT",  # Unified
    "Ekonomi och konsultverksamhet": "Economics and Consulting",
    "El, Energi och Kraft": "Electricity, Energy and Power",
    "el energi kraft": "Electricity, Energy and Power",  # Unified
    "Environment": "Environment",
    "miljö": "Environment",  # Unified
    "Miljö": "Environment",  # Unified
    "Fackförbund": "Trade Union",
    "fackförening": "Trade Union",  # Unified
    "Fastigheter & Infrastruktur": "Real Estate and Infrastructure",
    "fastighet infrastruktur": "Real Estate and Infrastructure",  # Unified
    "Forskning": "Research",
    "forskning": "Research",  # Unified
    "Research": "Research",  # Unified
    "Försäkring": "Insurance",
    "försäkring": "Insurance",  # Unified
    "grafikdesign": "Architecture and Graphic Design",  # Unified with Arkitektur och Grafisk design
    "Industri": "Industry",
    "industri": "Industry",  # Unified
    "Industry": "Industry",  # Unified
    "Investering": "Investment",
    "investering": "Investment",  # Unified
    "Kärnkraft": "Nuclear Power",
    "kärnkraft": "Nuclear Power",  # Unified
    "Life Science": "Life Science",
    "Management": "Management",
    "ledning": "Management",  # Unified
    "Media": "Media",
    "media": "Media",  # Unified
    "Medical Techniques": "Medical Technology",  # Unified with Medicinteknik
    "medicinsk teknik": "Medical Technology",  # Unified
    "Medicinteknik": "Medical Technology",
    "Telecommunication": "Telecommunication",
    "telekommunikation": "Telecommunication",  # Unified
    "Telekommunikation": "Telecommunication",  # Unified
    "Vägledning": "Guidance",
    "coaching": "Guidance",  # Unified with Vägledning
    "rekrytering": "Recruitment",
    "finanskonsult": "Finance Consultancy",
}

ENGLISH_TO_SWEDISH: dict[str, str] = {v: k for k, v in SWEDISH_TO_ENGLISH.items()}


def attempt_translate(term: str) -> str | None:
    """
    Attempt to translate a term from Swedish to English or verify if it is already in English.
    """
    attempt: str | None = SWEDISH_TO_ENGLISH.get(term, None) or (
        term if term in ENGLISH_TO_SWEDISH else None
    )
    if attempt is None:
        print(
            f"Warning: Term '{term}' is neither in Swedish nor English and will be omitted."
        )
    return attempt


def translate_to_english(terms: list[str]) -> list[str]:
    """
    Translate a list of terms from Swedish to English or verify if they are already in English.
    If a term is neither in Swedish nor English, it is omitted from the result.
    """

    return [w for w in list(attempt_translate(term) for term in terms) if w is not None]
