import os, csv, json
from datetime import datetime
import streamlit as st

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screening_responses.csv")
ADMIN_PASSCODE = "neil2026"  # Only you know this passcode to unlock CSV downloads!
GOOGLE_SHEET_WEBHOOK_URL = ""

CSV_HEADERS = [
    "Case_ID", "Timestamp", "Patient_Name_or_ID", "Language", "Patient_Age",
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
            rows = list(csv.reader(f))
            return max(0, len(rows) - 1)
    except Exception:
        return 0

def log_screening_response(lang, age, report, answers_dict, pin_code, patient_name=""):
    """Logs a completed screening once per test run."""
    init_csv()
    total_so_far = get_total_screenings() + 1
    case_id = f"SCR-{total_so_far:03d}"
    clean_name = patient_name.strip() if patient_name and patient_name.strip() else f"Anonymous ({case_id})"

    c = report["counts"]
    flagged_codes = ", ".join([it["code"] for it in report.get("checked_items", [])]) or "None"
    risk_label = "Doctor Evaluation Advised" if report.get("moderate_to_high_risk") else "Normal / Low Risk"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

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

def render_sidebar_tracker(key_suffix="main"):
    # Guard so it never renders twice on the same page run
    if st.session_state.get("_tracker_rendered_this_run", False):
        return
    st.session_state["_tracker_rendered_this_run"] = True

    total = get_total_screenings()
    goal = 100 if total < 100 else ((total // 100) + 1) * 100
    pct = min(100, int((total / goal) * 100)) if goal > 0 else 0

    st.sidebar.markdown(f"""
    <style>
        .impact-card {{
            background: #FFFFFF;
            border: 1.5px solid #E2E8F0;
            border-radius: 14px;
            padding: 14px 14px 12px 14px;
            margin: 8px 0 12px 0;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        }}
        .impact-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }}
        .impact-tag {{
            font-size: 0.68rem;
            font-weight: 800;
            color: #2563EB;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        .impact-goal {{
            background: #EFF6FF;
            color: #1D4ED8;
            font-size: 0.7rem;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
            border: 1px solid #BFDBFE;
            white-space: nowrap;
        }}
        .impact-num-row {{
            display: flex;
            align-items: baseline;
            gap: 6px;
            margin-bottom: 10px;
        }}
        .impact-num {{
            font-size: 1.65rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1;
            letter-spacing: -0.02em;
        }}
        .impact-unit {{
            font-size: 0.82rem;
            font-weight: 700;
            color: #475569;
        }}
        .impact-bar-bg {{
            width: 100%;
            background: #F1F5F9;
            height: 7px;
            border-radius: 999px;
            overflow: hidden;
        }}
        .impact-bar-fill {{
            width: {max(pct, 4) if total > 0 else 0}%;
            background: linear-gradient(90deg, #1E3A8A 0%, #2563EB 100%);
            height: 100%;
            border-radius: 999px;
            transition: width 0.3s ease;
        }}
        /* Make sidebar expander compact and clean */
        section[data-testid="stSidebar"] details summary p {{
            font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            color: #475569 !important;
        }}
    </style>
    <div class="impact-card">
        <div class="impact-top">
            <span class="impact-tag">Community Impact</span>
            <span class="impact-goal">Target: {goal}</span>
        </div>
        <div class="impact-num-row">
            <span class="impact-num">{total}</span>
            <span class="impact-unit">Screenings Completed</span>
        </div>
        <div class="impact-bar-bg">
            <div class="impact-bar-fill"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar.expander("🔒 Researcher Data Export"):
        pwd = st.text_input(
            "Admin Passcode:",
            type="password",
            placeholder="Enter researcher PIN",
            key=f"admin_pin_{key_suffix}"
        )
        if pwd == ADMIN_PASSCODE:
            st.success(f"Unlocked ({total} records)")
            st.download_button(
                label="📥 Export CSV Log",
                data=get_csv_bytes(),
                file_name="elder_care_screening_responses.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"dl_csv_btn_{key_suffix}"
            )
        elif pwd:
            st.error("Invalid passcode")
