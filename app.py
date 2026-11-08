import os, json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
import config
from modules.resume_parser import extract_text
from modules.scorer import analyze_resume
from modules.suggestions import get_tips, improve_bullets, career_roadmap

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

def get_db():
    return mysql.connector.connect(**config.DB_CONFIG)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS

def load_analysis(row):
    for key in ("matched", "missing", "tips", "breakdown"):
        try:
            row[key] = json.loads(row.get(key) or ("{}" if key == "breakdown" else "[]"))
        except (TypeError, ValueError):
            row[key] = {} if key == "breakdown" else []
    return row

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or len(password) < 6:
            flash("Enter all details. Password must contain at least 6 characters.", "danger")
            return redirect(url_for("register"))
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username,email,password) VALUES (%s,%s,%s)",
                        (username, email, generate_password_hash(password)))
            db.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))
        except mysql.connector.IntegrityError:
            flash("That email is already registered.", "danger")
        finally:
            cur.close(); db.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close(); db.close()
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS total, COALESCE(AVG(score),0) AS avg_score, MAX(score) AS best FROM analysis WHERE user_id=%s", (session["user_id"],))
    stats = cur.fetchone()
    cur.execute("SELECT id,filename,score,job_title,created_at FROM analysis WHERE user_id=%s ORDER BY id DESC LIMIT 5", (session["user_id"],))
    recent = cur.fetchall()
    cur.close(); db.close()
    return render_template("dashboard.html", stats=stats, recent=recent)

@app.route("/analyze", methods=["GET", "POST"])
@login_required
def analyze():
    if request.method == "POST":
        file = request.files.get("resume")
        job_text = request.form.get("job_description", "").strip()
        job_title = request.form.get("job_title", "General").strip()[:150]
        if not file or not file.filename:
            flash("Choose a resume file first.", "danger")
            return redirect(url_for("analyze"))
        if not allowed_file(file.filename):
            flash("Upload a PDF or DOCX file only.", "danger")
            return redirect(url_for("analyze"))
        safe_name = secure_filename(file.filename)
        stored_name = str(session["user_id"]) + "_" + safe_name
        path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
        file.save(path)
        try:
            resume_text = extract_text(path)
            result = analyze_resume(resume_text, job_text)
            tips = get_tips(result, resume_text, job_text)
            db = get_db(); cur = db.cursor()
            cur.execute("""INSERT INTO analysis
                (user_id,filename,score,matched,missing,tips,breakdown,job_title)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (session["user_id"], safe_name, result["score"],
                 json.dumps(result["matched"]), json.dumps(result["missing"]),
                 json.dumps(tips), json.dumps(result["breakdown"]), job_title))
            analysis_id = cur.lastrowid
            db.commit(); cur.close(); db.close()
            return redirect(url_for("result", analysis_id=analysis_id))
        except Exception as exc:
            if os.path.exists(path):
                os.remove(path)
            flash("Could not analyze this file: " + str(exc), "danger")
            return redirect(url_for("analyze"))
    return render_template("analyze.html")

@app.route("/result/<int:analysis_id>")
@login_required
def result(analysis_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM analysis WHERE id=%s AND user_id=%s", (analysis_id, session["user_id"]))
    record = cur.fetchone()
    cur.close(); db.close()
    if not record:
        flash("Analysis not found.", "danger")
        return redirect(url_for("history"))
    record = load_analysis(record)
    return render_template("result.html", record=record)

@app.route("/history")
@login_required
def history():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT id,filename,score,job_title,created_at FROM analysis WHERE user_id=%s ORDER BY id DESC", (session["user_id"],))
    records = cur.fetchall()
    cur.close(); db.close()
    return render_template("history.html", records=records)

@app.route("/delete/<int:analysis_id>", methods=["POST"])
@login_required
def delete_analysis(analysis_id):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM analysis WHERE id=%s AND user_id=%s", (analysis_id, session["user_id"]))
    db.commit(); cur.close(); db.close()
    flash("Analysis record deleted.", "success")
    return redirect(url_for("history"))

@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    comparison = None
    if request.method == "POST":
        ids = [request.form.get("resume1"), request.form.get("resume2")]
        db = get_db(); cur = db.cursor(dictionary=True)
        rows = []
        for item in ids:
            if item and item.isdigit():
                cur.execute("SELECT id,filename,score,job_title,created_at FROM analysis WHERE id=%s AND user_id=%s", (int(item), session["user_id"]))
                row = cur.fetchone()
                if row: rows.append(row)
        cur.close(); db.close()
        if len(rows) == 2:
            comparison = rows
        else:
            flash("Select two different saved analyses.", "warning")
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT id,filename,score,job_title FROM analysis WHERE user_id=%s ORDER BY id DESC", (session["user_id"],))
    records = cur.fetchall()
    cur.close(); db.close()
    return render_template("compare.html", records=records, comparison=comparison)

@app.route("/improve", methods=["GET", "POST"])
@login_required
def improve():
    improved = []
    if request.method == "POST":
        improved = improve_bullets(request.form.get("bullet_text", ""))
    return render_template("improve.html", improved=improved)

@app.route("/roadmap")
@login_required
def roadmap():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT missing FROM analysis WHERE user_id=%s ORDER BY id DESC LIMIT 1", (session["user_id"],))
    row = cur.fetchone()
    cur.close(); db.close()
    try:
        missing = json.loads(row["missing"]) if row and row["missing"] else []
    except (ValueError, TypeError):
        missing = []
    return render_template("roadmap.html", paths=career_roadmap(missing))

@app.route("/report/<int:analysis_id>")
@login_required
def report(analysis_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM analysis WHERE id=%s AND user_id=%s", (analysis_id, session["user_id"]))
    row = cur.fetchone()
    cur.close(); db.close()
    if not row:
        flash("Report not found.", "danger")
        return redirect(url_for("history"))
    row = load_analysis(row)
    report_path = os.path.join(config.UPLOAD_FOLDER, f"report_{session['user_id']}_{analysis_id}.pdf")
    doc = SimpleDocTemplate(report_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph("AI Resume Analysis Report", styles["Title"]), Spacer(1, 16),
             Paragraph("File: " + row["filename"], styles["BodyText"]),
             Paragraph("Target role: " + (row["job_title"] or "General"), styles["BodyText"]),
             Paragraph("ATS Match Score: " + str(row["score"]) + "/100", styles["Heading2"]),
             Spacer(1, 12), Paragraph("Score breakdown", styles["Heading2"])]
    for k,v in row["breakdown"].items():
        story.append(Paragraph(f"{k}: {v}%", styles["BodyText"]))
    story += [Spacer(1, 12), Paragraph("Matched skills", styles["Heading2"]),
              Paragraph(", ".join(row["matched"]) or "No matched skills recorded.", styles["BodyText"]),
              Paragraph("Skills to improve", styles["Heading2"]),
              Paragraph(", ".join(row["missing"]) or "No missing skills recorded.", styles["BodyText"]),
              Paragraph("Recommendations", styles["Heading2"])]
    for tip in row["tips"]:
        story.append(Paragraph("• " + tip, styles["BodyText"]))
    doc.build(story)
    return send_file(report_path, as_attachment=True, download_name="resume_analysis_report.pdf")

@app.errorhandler(413)
def too_large(error):
    flash("File is too large. Maximum size is 5 MB.", "danger")
    return redirect(url_for("analyze"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
