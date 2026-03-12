import datetime
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")


def get_calendar_service():
    """Get authenticated Google Calendar service."""
    from app.config import GOOGLE_CREDENTIALS_JSON

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_JSON, SCOPES)
            creds = flow.run_local_server(port=8090)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


async def schedule_interview(
    candidate_name: str,
    candidate_email: str,
    job_title: str,
    interview_time: datetime.datetime,
    duration_minutes: int = 45,
) -> dict:
    """Schedule a Google Calendar event with Meet link."""
    try:
        service = get_calendar_service()
        end_time = interview_time + datetime.timedelta(minutes=duration_minutes)

        event = {
            "summary": f"Interview: {candidate_name} - {job_title}",
            "description": f"Technical interview for {job_title} position.\nCandidate: {candidate_name} ({candidate_email})",
            "start": {"dateTime": interview_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "Asia/Kolkata"},
            "attendees": [{"email": candidate_email}],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"interview-{candidate_name.replace(' ', '-').lower()}-{interview_time.strftime('%Y%m%d%H%M')}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
            "reminders": {"useDefault": False, "overrides": [{"method": "email", "minutes": 60}, {"method": "popup", "minutes": 15}]},
        }

        created = service.events().insert(
            calendarId="primary", body=event, conferenceDataVersion=1, sendUpdates="all"
        ).execute()

        meet_link = created.get("hangoutLink", "")
        return {"success": True, "event_id": created["id"], "meet_link": meet_link, "html_link": created.get("htmlLink", "")}
    except Exception as e:
        return {"success": False, "error": str(e), "meet_link": "", "event_id": ""}


async def find_available_slots(
    start_date: datetime.datetime, num_slots: int = 10, slot_duration: int = 45
) -> list[datetime.datetime]:
    """Find available interview slots starting from a date."""
    try:
        service = get_calendar_service()
    except Exception:
        # Fallback: generate slots without checking calendar
        return _generate_default_slots(start_date, num_slots, slot_duration)

    slots = []
    current = start_date.replace(hour=10, minute=0, second=0, microsecond=0)

    while len(slots) < num_slots:
        if current.weekday() < 5 and 10 <= current.hour < 17:
            end = current + datetime.timedelta(minutes=slot_duration)
            try:
                body = {
                    "timeMin": current.isoformat() + "+05:30",
                    "timeMax": end.isoformat() + "+05:30",
                    "items": [{"id": "primary"}],
                }
                result = service.freebusy().query(body=body).execute()
                busy = result["calendars"]["primary"]["busy"]
                if not busy:
                    slots.append(current)
            except Exception:
                slots.append(current)

            current += datetime.timedelta(minutes=slot_duration + 15)
            if current.hour >= 17:
                current = (current + datetime.timedelta(days=1)).replace(hour=10, minute=0)
        else:
            current = (current + datetime.timedelta(days=1)).replace(hour=10, minute=0)

    return slots


def _generate_default_slots(start_date, num_slots, slot_duration):
    slots = []
    current = start_date.replace(hour=10, minute=0, second=0, microsecond=0)
    while len(slots) < num_slots:
        if current.weekday() < 5 and 10 <= current.hour < 17:
            slots.append(current)
            current += datetime.timedelta(minutes=slot_duration + 15)
            if current.hour >= 17:
                current = (current + datetime.timedelta(days=1)).replace(hour=10, minute=0)
        else:
            current = (current + datetime.timedelta(days=1)).replace(hour=10, minute=0)
    return slots
