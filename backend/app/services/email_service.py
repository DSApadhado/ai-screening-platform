import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_EMAIL, SMTP_PASSWORD


async def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP (Gmail)."""
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"[EMAIL MOCK] To: {to_email}, Subject: {subject}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


async def send_test_link_email(to_email: str, candidate_name: str, test_link: str, job_title: str) -> bool:
    html = f"""<html><body>
    <h2>Congratulations, {candidate_name}!</h2>
    <p>You have been shortlisted for the <strong>{job_title}</strong> position.</p>
    <p>Please complete the assessment using the link below:</p>
    <p><a href="{test_link}" style="background:#4F46E5;color:white;padding:12px 24px;text-decoration:none;border-radius:6px;">Take Assessment</a></p>
    <p>Best regards,<br>Recruitment Team</p>
    </body></html>"""
    return await send_email(to_email, f"Assessment Invitation - {job_title}", html)


async def send_interview_email(to_email: str, candidate_name: str, interview_time: str, meet_link: str, job_title: str) -> bool:
    html = f"""<html><body>
    <h2>Interview Invitation</h2>
    <p>Dear {candidate_name},</p>
    <p>We are pleased to invite you for an interview for the <strong>{job_title}</strong> position.</p>
    <p><strong>Date & Time:</strong> {interview_time}</p>
    <p><strong>Google Meet Link:</strong> <a href="{meet_link}">{meet_link}</a></p>
    <p>Please join the meeting 5 minutes before the scheduled time.</p>
    <p>Best regards,<br>Recruitment Team</p>
    </body></html>"""
    return await send_email(to_email, f"Interview Invitation - {job_title}", html)
