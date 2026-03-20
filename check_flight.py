import smtplib, os, sys
import requests
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

# ── Timezones ──────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
EDT = timezone(timedelta(hours=-4))

# ── Config ─────────────────────────────────────────────
GMAIL_USER  = os.environ["GMAIL_USER"]
GMAIL_PASS  = os.environ["GMAIL_PASS"]
SERPAPI_KEY = os.environ["SERPAPI_KEY"]
CHECK_LABEL = sys.argv[1] if len(sys.argv) > 1 else "Status Check"

# ── Fetch from SerpAPI Google Flights ─────────────────
def get_status():
    url = "https://serpapi.com/search"
    params = {
        "engine":  "google_flights",
        "api_key": SERPAPI_KEY,
        "q":       "AA293 flight status",
        "hl":      "en",
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    print("=== RAW SERPAPI RESPONSE ===")
    import json
    print(json.dumps(data, indent=2)[:3000])
    print("============================")

    # ── Try flight status endpoint instead ────────────
    url2 = "https://serpapi.com/search"
    params2 = {
        "engine":        "google",
        "api_key":       SERPAPI_KEY,
        "q":             "AA293 flight status",
        "hl":            "en",
        "gl":            "us",
    }

    r2 = requests.get(url2, params=params2, timeout=20)
    data2 = r2.json()

    print("=== RAW SERPAPI GOOGLE RESPONSE ===")
    print(json.dumps(data2, indent=2)[:5000])
    print("====================================")

    now_ist = datetime.now(IST).strftime("%b %d, %Y  %I:%M %p")
    now_edt = datetime.now(EDT).strftime("%b %d, %Y  %I:%M %p")

    # ── Parse flight status from knowledge graph ──────
    kg = data2.get("knowledge_graph", {})
    answer_box = data2.get("answer_box", {})
    flights = data2.get("flights", {})

    print("=== KNOWLEDGE GRAPH ===")
    print(json.dumps(kg, indent=2))
    print("=== ANSWER BOX ===")
    print(json.dumps(answer_box, indent=2))
    print("=== FLIGHTS ===")
    print(json.dumps(flights, indent=2))

    body = f"""
✈️  AA293  |  New Delhi  →  New York JFK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Check     :  {CHECK_LABEL}
  Status    :  Parsing in progress - check logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checked at:  {now_ist}  IST
               {now_edt}  EDT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return body


# ── Send Email ─────────────────────────────────────────
def send_email(subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = GMAIL_USER
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print("✅ Email sent!")


# ── Main ───────────────────────────────────────────────
body = get_status()
print(body)
subject = f"✈️ AA293 DEL→JFK  |  {CHECK_LABEL}  |  {datetime.now(IST).strftime('%b %d, %Y')}"
send_email(subject, body)
