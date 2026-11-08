SKILLS = [
    "python", "java", "c++", "c", "html", "css", "javascript",
    "sql", "mysql", "excel", "power bi", "tableau", "pandas",
    "numpy", "flask", "django", "react", "machine learning",
    "data analysis", "data visualization", "statistics", "git",
    "github", "communication", "problem solving", "data cleaning",
    "aws", "azure", "linux", "api", "oop", "data structures"
]

SECTIONS = ["education", "skills", "projects", "experience", "certifications"]

def find_skills(text):
    text = (text or "").lower()
    found = []
    for skill in SKILLS:
        if skill == "c":
            import re
            if re.search(r'(?<![a-z])c(?![a-z])', text):
                found.append(skill)
        elif skill in text:
            found.append(skill)
    return sorted(set(found))

def check_sections(text):
    text = (text or "").lower()
    return {section: section in text for section in SECTIONS}
