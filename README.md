# ResumeIQ – AI Resume Analyzer

A Flask + MySQL student project with resume text extraction, estimated ATS matching, skill comparison, recommendations, history, comparison, PDF reports, sentence improvement helper and a basic career roadmap.

## 1. Requirements
- Python 3.10 or newer
- MySQL Server and MySQL Workbench
- Windows Command Prompt

## 2. Set up the database
1. Open MySQL Workbench and connect to your local server.
2. Open `database.sql`.
3. Run the complete script.
4. Confirm the `ai_resume_analyzer` database exists.

## 3. Set your MySQL password
Open `config.py`. Replace `YOUR_MYSQL_PASSWORD` with your local MySQL root password. Do not share this password.

## 4. Install Python packages
Open Command Prompt in this project folder and run:

```cmd
py -m pip install -r requirements.txt
```

## 5. Start the project

```cmd
py app.py
```

Open `http://127.0.0.1:5000` in your browser.

## 6. Test
1. Register a new account.
2. Log in.
3. Open Resume Analyzer.
4. Upload a text-based PDF or DOCX resume.
5. Paste a job description and enter a target role.
6. Review the estimated score and recommendations.

## Important notes
- The ATS score is a simple project estimate based on extracted text, detected skills, TF-IDF keyword similarity and section presence. It is not a real ATS certification or a guarantee of hiring.
- The sentence improver uses basic local wording rules, not a generative AI model. Do not use suggestions that add claims you did not actually achieve.
- Scanned/image-only PDFs may not extract correctly. Use a text-based PDF or DOCX.
- The PDF report uses ReportLab.
- Uploaded files are saved in `uploads/`. Keep this folder private. Add authentication and access controls before deploying publicly.
- For a production deployment, disable Flask debug mode, use a strong secret key, validate uploads more strictly, and add CSRF protection.
