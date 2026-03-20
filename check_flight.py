import smtplib, os, sys, re
import requests
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ── Timezones ──────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
EDT = timezone(timedelta(hours=-4))

# ── Config ─────────────────────────────────────────────
GMAIL_USER  = os.environ["GMAIL_USER"]
GMAIL_PASS  = os.environ["GMAIL_PASS"]
CHECK_LABEL = sys.argv[1] if len(sys.argv) > 1 else "Status Check"

# ── Scrape FlightStats ─────────────────────────────────
def get_status():
    url = "https://www.flightstats.com/v2/flight-tracker/AA/293"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    # ── Extract JSON data embedded in page ────────────
    scripts = soup.find_all("script")
    flight_data = None
    for script in scripts:
        if script.string and "flightState" in script.string:
            match = re.search(r'"flightState"\s*:\s*"([^"]+)"', script.string)
            if match:
                flight_data = script.string
                break

    # ── Parse visible text as fallback ────────────────
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Find status
    status = "Unknown"
    status_map = {
        "departed": "🛫 Departed",
        "in flight": "✈️  In Flight",
        "landed": "🛬 Landed",
        "cancelled": "❌ Cancelled",
        "scheduled": "🕐 Scheduled",
        "diverted": "⚠️  Diverted",
        "on time": "✅ On Time",
        "delayed": "⚠️  Delayed"
    }
    for line in lines:
        lower = line.lower()
        for key, val in status_map.items():
            if key in lower:
                status = val
                break

    # Extract times using regex
    def find_time(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else "—"

    # Departure times (IST)
    dep_actual    = find_time(r'Actual\s*[\n\r]+([^\n\r]+(?:AM|PM)[^\n\r]*IST)', text)
    dep_scheduled = find_time(r'Scheduled\s*:\s*([^\n\r]+IST)', text)
    dep_estimated = find_time(r'Estimated\s*:\s*([^\n\r]+IST)', text)
    dep_terminal  = find_time(r'Terminal\s*:\s*(\d+)', text)
    dep_gate      = find_time(r'Gate\s*:\s*(\w+)(?=.*DEL)', text)

    # Arrival times (EDT)
    arr_scheduled = find_time(r'Scheduled\s*:\s*([^\n\r]+EDT)', text)
    arr_estimated = find_time(r'Estimated\s*[\n\r]+([^\n\r]+(?:AM|PM)[^\n\r]*EDT)', text)
    arr_actual    = find_time(r'Actual\s*[\n\r]+([^\n\r]+(?:AM|PM)[^\n\r]*EDT)', text)
    arr_terminal  = find_time(r'Terminal\s*:\s*(\w+)(?=.*JFK)', text)
    arr_gate      = find_time(r'Gate\s*:\s*(\w+)(?=.*JFK)', text)

    now_ist = datetime.now(IST).strftime("%b %d, %Y  %I:%M %p")
    now_edt = datetime.now(EDT).strftime("%b %d, %Y  %I:%M %p")

    body = f"""
✈️  AA293  |  New Delhi  →  New York JFK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Check     :  {CHECK_LABEL}
  Status    :  {status}


🛫  DEPARTURE  —  Indira Gandhi Intl (DEL)
─────────────────────────────────────────
  Scheduled :  {dep_scheduled}
  Estimated :  {dep_estimated}
  Actual    :  {dep_actual}
  Terminal  :  {dep_terminal}   Gate: {dep_gate}


🛬  ARRIVAL  —  John F. Kennedy Intl (JFK)
─────────────────────────────────────────
  Scheduled :  {arr_scheduled}
  Estimated :  {arr_estimated}
  Actual    :  {arr_actual}
  Terminal  :  {arr_terminal}   Gate: {arr_gate}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checked at:  {now_ist}  IST
               {now_edt}  EDT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return status, body


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
status, body = get_status()
print(body)

subject = f"✈️ AA293 DEL→JFK  |  {CHECK_LABEL}  |  {datetime.now(IST).strftime('%b %d, %Y')}"
send_email(subject, body)
