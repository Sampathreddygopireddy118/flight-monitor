import requests, smtplib, os, sys
from email.mime.text import MIMEText
from datetime import datetime

FLIGHT = "AA293"
API_KEY = os.environ["AVIATIONSTACK_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASS = os.environ["GMAIL_PASS"]
CHECK_LABEL = sys.argv[1] if len(sys.argv) > 1 else "Status Check"

def get_status():
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": API_KEY,
        "flight_iata": FLIGHT,
        "dep_iata": "DEL",
        "arr_iata": "JFK"
    }
    r = requests.get(url, params=params, timeout=15)
    data = r.json()

    if not data.get("data"):
        return "⚠️ Could not fetch flight data. Check API or flight may not be active today."

    f = data["data"][0]
    status     = f.get("flight_status", "Unknown").upper()
    dep_sched  = f["departure"].get("scheduled", "N/A")
    dep_est    = f["departure"].get("estimated", "N/A")
    dep_actual = f["departure"].get("actual", "Not departed yet")
    dep_delay  = f["departure"].get("delay", 0) or 0
    arr_sched  = f["arrival"].get("scheduled", "N/A")
    arr_est    = f["arrival"].get("estimated", "N/A")
    arr_actual = f["arrival"].get("actual", "Not arrived yet")
    arr_delay  = f["arrival"].get("delay", 0) or 0
    gate_dep   = f["departure"].get("gate", "N/A")
    gate_arr   = f["arrival"].get("gate", "N/A")
    terminal   = f["departure"].get("terminal", "3")

    emoji = {"scheduled":"🕐","active":"✈️","landed":"🛬","cancelled":"❌","diverted":"⚠️"}.get(f.get("flight_status",""), "❓")

    body = f"""
{emoji} AA293 FLIGHT STATUS — {CHECK_LABEL}
{'='*45}
Status     : {status}

🛫 DEPARTURE (DEL - New Delhi)
  Scheduled : {dep_sched}
  Estimated : {dep_est}
  Actual    : {dep_actual}
  Delay     : {dep_delay} minutes
  Terminal  : {terminal} | Gate: {gate_dep}

🛬 ARRIVAL (JFK - New York)
  Scheduled : {arr_sched}
  Estimated : {arr_est}
  Actual    : {arr_actual}
  Delay     : {arr_delay} minutes
  Gate      : {gate_arr}

Checked at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
"""
    return body

def send_email(body):
    msg = MIMEText(body)
    msg["Subject"] = f"✈️ AA293 DEL→JFK | {CHECK_LABEL} | {datetime.utcnow().strftime('%b %d')}"
    msg["From"] = GMAIL_USER
    msg["To"] = GMAIL_USER
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(GMAIL_USER, GMAIL_PASS)
        s.send_message(msg)
    print("✅ Email sent!")

body = get_status()
print(body)
send_email(body)
