def get_tips(result, resume_text="", job_text=""):
    tips = []
    sections = result.get("sections", {})
    for name, present in sections.items():
        if not present:
            tips.append("Add a clear " + name.title() + " section to your resume.")
    for skill in result.get("missing", [])[:8]:
        tips.append("If you genuinely know it, include relevant evidence of " + skill.title() + " in your skills or projects.")
    if len((resume_text or "").split()) < 150:
        tips.append("Add more relevant details about your education, projects, skills and responsibilities.")
    if len((resume_text or "").split()) > 900:
        tips.append("Make your resume concise and prioritize the most relevant information.")
    if not tips:
        tips.append("Your resume structure looks good. Keep tailoring it to each job description.")
    return tips

def improve_bullets(text):
    lines = [x.strip(" •-\t") for x in (text or "").splitlines() if x.strip()]
    results = []
    for line in lines[:12]:
        if len(line.split()) < 3:
            results.append(line)
        elif line.lower().startswith(("developed ", "created ", "built ", "analyzed ", "designed ", "implemented ")):
            results.append(line[0].upper() + line[1:])
        else:
            results.append("Worked on " + line[0].lower() + line[1:] + ".")
    return results

def career_roadmap(missing):
    paths = []
    for skill in missing[:8]:
        paths.append({
            "skill": skill.title(),
            "level": "Beginner",
            "task": "Learn the fundamentals of " + skill.title() + " and complete one small practical exercise."
        })
    if not paths:
        paths.append({
            "skill": "Portfolio projects",
            "level": "Next step",
            "task": "Build one project related to the target role and document your contribution."
        })
    return paths
