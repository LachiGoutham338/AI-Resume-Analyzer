from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from modules.skill_extractor import find_skills, check_sections

def analyze_resume(resume, job):
    resume = resume or ""
    job = job or ""
    resume_skills = set(find_skills(resume))
    job_skills = set(find_skills(job))
    matched = sorted(resume_skills & job_skills) if job_skills else sorted(resume_skills)
    missing = sorted(job_skills - resume_skills) if job_skills else []

    keyword_score = 0
    if job.strip() and resume.strip():
        try:
            matrix = TfidfVectorizer(stop_words="english").fit_transform([resume, job])
            keyword_score = round(float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100), 1)
        except ValueError:
            keyword_score = 0

    if job_skills:
        skill_score = round(len(matched) / max(len(job_skills), 1) * 100, 1)
    else:
        skill_score = min(100, round(len(resume_skills) * 6.5, 1))

    sections = check_sections(resume)
    section_score = round(sum(sections.values()) / len(sections) * 100, 1)
    words = len(resume.split())
    length_score = 100 if 250 <= words <= 900 else (70 if words >= 150 else 40)

    if job.strip():
        overall = skill_score * .40 + keyword_score * .35 + section_score * .15 + length_score * .10
    else:
        overall = skill_score * .55 + section_score * .30 + length_score * .15

    return {
        "score": round(min(100, overall), 1),
        "matched": matched,
        "missing": missing,
        "sections": sections,
        "breakdown": {
            "Skills Match": skill_score,
            "Keyword Match": keyword_score,
            "Resume Sections": section_score,
            "Resume Length": length_score
        },
        "word_count": words
    }
