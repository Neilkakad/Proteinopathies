import os, csv, json
from datetime import datetime
import streamlit as st

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screening_responses.csv")

# Optional: Paste a Google Apps Script Webhook URL or Formspree/SheetDB URL here if you want cloud Google Sheets sync
GOOGLE_SHEET_WEBHOOK_URL = ""

CSV_HEADERS = [
    "Timestamp", "Language", "Patient_Age", "Memory_Score_AD8",
    "Movement_Score", "Body_Vitamin_Score", "Total_Flags",
    "Risk_Category", "PIN_Code", "Flagged_Codes"
]

def init_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def log_screening_response(lang, age, report, answers_dict, pin_code):
    """Logs a completed screening once per test run."""
    init_csv()
    c = report["counts"]
    flagged_codes = ", ".join([it["code"] for it in report.get("checked_items", [])]) or "None"
    risk_label = "Doctor Evaluation Advised" if report.get("moderate_to_high_risk") else "Normal / Healthy"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        now_str,
        "Hindi" if lang == "hi" else "English",
        age,
        f"{report['ad8_score']}/8",
        f"{c['motor']}/4",
        f"{c['body']}/3",
        c["total"],
        risk_label,
        pin_code,
        flagged_codes
    ]

    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
    except Exception:
        pass

    # If a Google Sheet Webhook is configured, send it asynchronously
    webhook = GOOGLE_SHEET_WEBHOOK_URL or st.secrets.get("SHEET_WEBHOOK_URL", "") if hasattr(st, "secrets") else ""
    if webhook:
        try:
            import urllib.request
            payload = json.dumps({
                "timestamp": now_str, "language": lang, "age": age,
                "ad8_score": report["ad8_score"], "motor_score": c["motor"],
                "body_score": c["body"], "total_flags": c["total"],
                "risk": risk_label, "pin_code": pin_code, "flagged_codes": flagged_codes
            }).encode("utf-8")
            req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2.5)
        except Exception:
            pass

def get_total_screenings():
    init_csv()
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            return max(0, len(rows) - 1)
    except Exception:
        return 0

def get_csv_bytes():
    init_csv()
    with open(CSV_PATH, "rb") as f:
        return f.read()

def render_sidebar_tracker():
    total = get_total_screenings()
    goal = 50 if total < 50 else (100 if total < 100 else ((total // 100) + 1) * 100)
    pct = min(100, int((total / goal) * 100)) if goal > 0 else 0

    st.sidebar.markdown(f"""
    <div style="background: linear-gradient(145deg, #F8FAFC 0%, #EFF6FF 100%); border: 1.5px solid #BFDBFE; border-radius: 14px; padding: 14px 16px; margin: 10px 0 14px 0; box-shadow: 0 4px 10px rgba(37, 99, 235, 0.06);">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:0.76rem; font-weight:800; color:#1E40AF; text-transform:uppercase; letter-spacing:0.04em;">📊 Live Screening Impact</span>
            <span style="background:#DBEAFE; color:#1D4ED8; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:999px;">Goal: {goal}</span>
        </div>
        <div style="font-size:1.55rem; font-weight:800; color:#0F172A; line-height:1.2;">
            {total} <span style="font-size:0.9rem; font-weight:700; color:#475569;">Families Screened</span>
        </div>
        <div style="font-size:0.78rem; color:#64748B; font-weight:600; margin-top:2px; margin-bottom:8px;">
            अब तक {total} परिवारों की जाँच पूरी हुई
        </div>
        <div style="width:100%; background:#E2E8F0; height:8px; border-radius:999px; overflow:hidden;">
            <div style="width:{pct}%; background:linear-gradient(90deg, #2563EB 0%, #10B981 100%); height:100%; border-radius:999px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar.expander("📥 View / Download Saved Responses"):
        st.caption(f"Total recorded screenings: **{total}**")
        st.download_button(
            label="📥 Download Responses (.CSV)",
            data=get_csv_bytes(),
            file_name="elder_care_screening_responses.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv_sidebar_btn"
        )
