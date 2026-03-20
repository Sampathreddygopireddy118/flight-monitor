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

# ── Scrape Google Flight Status ────────────────────────
def get_status():
    url = "https://www.google.com/search"
    params = {"q": "AA293 flight status"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    r = requests.get(url, params=params, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # ── Debug: print first 100 lines to see what Google returns
    print("=== RAW GOOGLE TEXT (first 100 lines) ===")
    for i, line in enumerate(lines[:100]):
        print(f"{i:03}: {line}")
    print("==========================================")

    now_ist = datetime.now(IST).strftime("%b %d, %Y  %I:%M %p")
    now_edt = datetime.now(EDT).strftime("%b %d, %Y  %I:%M %p")

    # ── Try to find key fields ─────────────────────────
    def find_after(keyword, lines, window=3):
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                for j in range(1, window+1):
                    if i+j < len(lines) and lines[i+j].strip():
                        return lines[i+j].strip()
        return "—"

    status   = find_after("flight status", lines)
    dep_act  = find_after("actual", lines)
    dep_sch  = find_after("scheduled", lines)
    arr_est  = find_after("estimated", lines)
    terminal = find_after("terminal", lines)
    gate     = find_after("gate", lines)

    body = f"""
✈️  AA293  |  New Delhi  →  New York JFK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Check     :  {CHECK_LABEL}
  Status    :  {status}


🛫  DEPARTURE  —  Indira Gandhi Intl (DEL)
─────────────────────────────────────────
  Scheduled :  {dep_sch}  IST
  Actual    :  {dep_act}  IST


🛬  ARRIVAL  —  John F. Kennedy Intl (JFK)
─────────────────────────────────────────
  Scheduled :  07:10 AM  EDT
  Estimated :  {arr_est}  EDT
  Terminal  :  {terminal}   Gate: {gate}


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
