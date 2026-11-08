SECRET_KEY = "my_resume_analyzer_secret_key_123"

MAX_CONTENT_LENGTH = 5 * 1024 * 1024

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {"pdf", "docx"}

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "MYSQL_PASSWORD",
    "database": "ai_resume_analyzer"
}