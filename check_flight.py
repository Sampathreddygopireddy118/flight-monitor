import requests, smtplib, os, sys
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta

# ── Timezones ──────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))
EDT = timezone(timedelta(hours=-4))

# ── Config ─────────────────────────────────────────────
FLIGHT      = "AA293"
API_KEY     = os.environ["AVIATIONSTACK_KEY"]
GMAIL_USER  = os.environ["GMAIL_USER"]
GMAIL_PASS  = os.environ["GMAIL_PASS"]
CHECK_LABEL = sys.argv[1] if len(sys.argv) > 1 else "Status Check"

# ── Helpers ────────────────────────────────────────────
def fmt(iso_str):
    if not iso_str or iso_str in ("N/A", "None", None):
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str).replace(tzinfo=None)
        return dt.strftime("%b %d, %Y  %I:%M %p")
    except:
        return "—"

def calc_delay(scheduled, actual):
    if not scheduled or not actual:
        return "—"
    try:
        s = datetime.fromisoformat(scheduled).replace(tzinfo=None)
        a = datetime.fromisoformat(actual).replace(tzinfo=None)
        diff = int((a - s).total_seconds() / 60)
        if diff < 0:   return f"{abs(diff)} min early 🟢"
        elif diff == 0: return "On Time ✅"
        elif diff <= 15: return f"{diff} min late 🟡"
        else:           return f"{diff} min late 🔴"
    except:
        return "—"

# ── Fetch Flight ───────────────────────────────────────
def get_status():
    r = requests.get(
        "http://api.aviationstack.com/v1/flights",
        params={
            "access_key": API_KEY,
            "flight_iata": FLIGHT,
            "dep_iata": "DEL",
            "arr_iata": "JFK"
        },
        timeout=15
    )
    data = r.json()

    if not data.get("data"):
        return None, "⚠️ No flight data found. Flight may not be active today."

    f = data["data"][0]
    raw_status = f.get("flight_status", "unknown")
    status_map = {
        "scheduled": "🕐 Scheduled",
        "active":    "✈️  In Flight",
        "landed":    "🛬 Landed",
        "cancelled": "❌ Cancelled",
        "diverted":  "⚠️  Diverted"
    }
    status = status_map.get(raw_status, f"❓ {raw_status.title()}")

    dep = f["departure"]
    arr = f["arrival"]

    dep_sched  = dep.get("scheduled")
    dep_est    = dep.get("estimated")
    dep_actual = dep.get("actual")
    arr_sched  = arr.get("scheduled")
    arr_est    = arr.get("estimated")
    arr_actual = arr.get("actual")

    dep_for_delay = dep_actual or dep_est
    arr_for_delay = arr_actual or arr_est

    now_ist = datetime.now(IST).strftime("%b %d, %Y  %I:%M %p")
    now_edt = datetime.now(EDT).strftime("%b %d, %Y  %I:%M %p")

    body = f"""
✈️  AA293  |  New Delhi  →  New York JFK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Check     :  {CHECK_LABEL}
  Status    :  {status}


🛫  DEPARTURE  —  Indira Gandhi Intl (DEL)
─────────────────────────────────────────
  Scheduled :  {fmt(dep_sched)}  IST
  Estimated :  {fmt(dep_est)}    IST
  Actual    :  {fmt(dep_actual)} IST
  Delay     :  {calc_delay(dep_sched, dep_for_delay)}
  Terminal  :  {dep.get("terminal", "3")}   Gate: {dep.get("gate", "—")}


🛬  ARRIVAL  —  John F. Kennedy Intl (JFK)
─────────────────────────────────────────
  Scheduled :  {fmt(arr_sched)}  EDT
  Estimated :  {fmt(arr_est)}    EDT
  Actual    :  {fmt(arr_actual)} EDT
  Delay     :  {calc_delay(arr_sched, arr_for_delay)}
  Terminal  :  {arr.get("terminal", "8")}   Gate: {arr.get("gate", "—")}


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Checked at:  {now_ist}  IST
               {now_edt}  EDT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return raw_status, body


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
raw_status, body = get_status()
print(body)

status_emoji = {
    "scheduled": "🕐",
    "active":    "✈️",
    "landed":    "🛬",
    "cancelled": "❌",
    "diverted":  "⚠️"
}.get(raw_status, "✈️")

subject = f"{status_emoji} AA293 DEL→JFK  |  {CHECK_LABEL}  |  {datetime.now(IST).strftime('%b %d, %Y')}"
send_email(subject, body)
