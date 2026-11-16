import os, csv, json
from datetime import datetime
import streamlit as st

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screening_responses.csv")
ADMIN_PASSCODE = "neil2026"
GOOGLE_SHEET_WEBHOOK_URL = ""

CSV_HEADERS = [
    "Case_ID", "Timestamp", "Patient_Name_or_Initials", "Language", "Patient_Age",
    "Memory_Score_AD8", "Movement_Score", "Body_Vitamin_Score", "Total_Flags",
    "Risk_Category", "PIN_Code", "Flagged_Codes"
]

def init_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)

def get_total_screenings():
    init_csv()
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if any(cell.strip() for cell in r)]
            return max(0, len(rows) - 1)
    except Exception:
        return 0

def log_screening_response(lang, age, report, answers_dict, pin_code, patient_name=""):
    """Logs a completed screening immediately and increments the live counter."""
    init_csv()
    total_so_far = get_total_screenings() + 1
    case_id = f"SCR-{total_so_far:03d}"
    clean_name = patient_name.strip() if patient_name and patient_name.strip() else f"Anonymous ({case_id})"

    c = report["counts"]
    flagged_codes = ", ".join([it["code"] for it in report.get("checked_items", [])]) or "None"
    risk_label = "Doctor Evaluation Advised" if report.get("moderate_to_high_risk") else "Normal / Low Risk"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        case_id,
        now_str,
        clean_name,
        "Hindi" if lang == "hi" else "English",
        age,
        f"{report['ad8_score']}/8",
        f"{c['motor']}/4",
        f"{c['body']}/3",
        c["total"],
        risk_label,
        pin_code or "N/A",
        flagged_codes
    ]

    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)
    except Exception:
        pass

    webhook = GOOGLE_SHEET_WEBHOOK_URL or (st.secrets.get("SHEET_WEBHOOK_URL", "") if hasattr(st, "secrets") else "")
    if webhook:
        try:
            import urllib.request
            payload = json.dumps({
                "case_id": case_id, "timestamp": now_str, "patient": clean_name,
                "language": lang, "age": age, "ad8_score": report["ad8_score"],
                "motor_score": c["motor"], "body_score": c["body"],
                "total_flags": c["total"], "risk": risk_label,
                "pin_code": pin_code, "flagged_codes": flagged_codes
            }).encode("utf-8")
            req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=2.5)
        except Exception:
            pass

def get_csv_bytes():
    init_csv()
    with open(CSV_PATH, "rb") as f:
        return f.read()

def get_recent_records():
    init_csv()
    try:
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            rows = list(csv.reader(f))
            return rows[0], rows[1:]
    except Exception:
        return CSV_HEADERS, []

def render_sidebar_tracker(key_suffix="main"):
    total = get_total_screenings()
    goal = 100 if total < 100 else ((total // 100) + 1) * 100
    pct = min(100, int((total / goal) * 100)) if goal > 0 else 0
    bar_width = max(pct, 6) if total > 0 else 0

    st.sidebar.markdown(f"""
    <style>
        .impact-card-box {{
            background: #FFFFFF;
            border: 1.5px solid #CBD5E1;
            border-radius: 14px;
            padding: 12px 12px;
            margin: 8px 0 12px 0;
            box-sizing: border-box !important;
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        }}
        .impact-eyebrow {{
            font-size: 0.65rem;
            font-weight: 800;
            color: #2563EB;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 6px;
            display: block;
        }}
        .impact-badge-inline {{
            display: inline-block;
            background: #EFF6FF;
            color: #1D4ED8;
            font-size: 0.68rem;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 6px;
            border: 1px solid #BFDBFE;
            margin-bottom: 8px;
        }}
        .impact-count-line {{
            font-size: 1.55rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.1;
            margin-bottom: 2px;
        }}
        .impact-sub-line {{
            font-size: 0.76rem;
            font-weight: 700;
            color: #475569;
            margin-bottom: 10px;
        }}
        .impact-progress-track {{
            width: 100%;
            background: #E2E8F0;
            height: 8px;
            border-radius: 999px;
            overflow: hidden;
        }}
        .impact-progress-fill {{
            width: {bar_width}%;
            background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
            height: 100%;
            border-radius: 999px;
            transition: width 0.35s ease;
        }}
    </style>
    <div class="impact-card-box">
        <span class="impact-eyebrow">Community Impact</span>
        <span class="impact-badge-inline">Goal: {total} / {goal}</span>
        <div class="impact-count-line">{total}</div>
        <div class="impact-sub-line">Screenings Completed</div>
        <div class="impact-progress-track">
            <div class="impact-progress-fill"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "admin_unlocked" not in st.session_state:
        st.session_state.admin_unlocked = False

    with st.sidebar.expander("🔒 Researcher Data Export", expanded=st.session_state.admin_unlocked):
        pwd = st.text_input(
            "Researcher Passcode:",
            type="password",
            placeholder="Enter passcode (neil2026)",
            key=f"admin_pin_input_{key_suffix}"
        )
        if pwd == ADMIN_PASSCODE:
            st.session_state.admin_unlocked = True
        elif pwd and pwd != ADMIN_PASSCODE:
            st.session_state.admin_unlocked = False
            st.error("Incorrect passcode")

        if st.session_state.admin_unlocked:
            st.success(f"Unlocked • {total} Saved")
            st.download_button(
                label="📥 Download CSV Log",
                data=get_csv_bytes(),
                file_name="elder_care_screening_responses.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"dl_csv_btn_{key_suffix}"
            )
             headers, rows = get_recent_records()
            if rows:
                st.caption("Latest Submissions:")
                for r in rows[-5:][::-1]:
                    st.markdown(f"- **{r[2]}** (Age {r[4]}) • `{r[5]}`")
