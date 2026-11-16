import os, csv, json
from datetime import datetime
import streamlit as st

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screening_responses.csv")
VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_voice_names")
ADMIN_PASSCODE = "neil2026"
GOOGLE_SHEET_WEBHOOK_URL = ""

CSV_HEADERS = [
    "Case ID",
    "Date & Time",
    "Patient Name / Initials",
    "Screening Language",
    "Patient Age",
    "Memory Score (AD8)",
    "Movement & Balance",
    "Physical & Nutrition",
    "Total Observations",
    "Clinical Recommendation",
    "Postal PIN Code",
    "Flagged Clinical Areas"
]

def init_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        return
    try:
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            rows = [r for r in csv.reader(f) if any(cell.strip() for cell in r)]
        if not rows or rows[0] != CSV_HEADERS:
            data_rows = rows[1:] if rows else []
            upgraded_rows = []
            for idx, r in enumerate(data_rows, 1):
                if len(r) == 10:
                    cid = f"SCR-{idx:03d}"
                    upgraded_rows.append([cid, r[0], f"Anonymous ({cid})", r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]])
                elif len(r) >= 12:
                    upgraded_rows.append(r[:12])
            with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
                writer.writerows(upgraded_rows)
    except Exception:
        pass

def get_total_screenings():
    init_csv()
    try:
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            rows = [r for r in csv.reader(f) if any(cell.strip() for cell in r)]
            return max(0, len(rows) - 1)
    except Exception:
        return 0

def log_screening_response(lang, age, report, answers_dict, pin_code, patient_name="", voice_bytes=None):
    init_csv()
    total_so_far = get_total_screenings() + 1
    case_id = f"SCR-{total_so_far:03d}"

    raw_name = patient_name.strip() if patient_name and patient_name.strip() else ""
    if voice_bytes:
        try:
            os.makedirs(VOICE_DIR, exist_ok=True)
            v_path = os.path.join(VOICE_DIR, f"{case_id}_name.wav")
            with open(v_path, "wb") as vf:
                vf.write(voice_bytes)
            clean_name = f"{raw_name} 🎙️ (Voice Saved)" if raw_name else f"Voice Recorded ({case_id}) 🎙️"
        except Exception:
            clean_name = raw_name or f"Anonymous ({case_id})"
    else:
        clean_name = raw_name if raw_name else f"Anonymous ({case_id})"

    c = report["counts"]
    checked = report.get("checked_items", [])
    if checked:
        flagged_desc = "; ".join([f"{it['code']} ({it.get('label_en', it['code'])[:28]})" for it in checked])
    else:
        flagged_desc = "No warning signs flagged"

    risk_label = "Clinical Evaluation Advised" if report.get("moderate_to_high_risk") else "Within Normal Healthy Range"
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    row = [
        case_id,
        now_str,
        clean_name,
        "Hindi (हिंदी)" if lang == "hi" else "English",
        f"{age} yrs",
        f"{report['ad8_score']} / 8",
        f"{c['motor']} / 4",
        f"{c['body']} / 3",
        f"{c['total']} / 15",
        risk_label,
        pin_code.strip() if pin_code and pin_code.strip() else "Not Provided",
        flagged_desc
    ]

    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(row)
    except Exception:
        pass

def get_csv_bytes():
    init_csv()
    with open(CSV_PATH, "rb") as f:
        return f.read()

def get_recent_records():
    init_csv()
    try:
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            rows = [r for r in csv.reader(f) if any(cell.strip() for cell in r)]
            if len(rows) > 1:
                return rows[0], rows[1:]
            return CSV_HEADERS, []
    except Exception:
        return CSV_HEADERS, []

def get_styled_html_report():
    headers, rows = get_recent_records()
    total = len(rows)
    high_risk = sum(1 for r in rows if len(r) > 9 and "Advised" in r[9])
    normal_cnt = total - high_risk

    trs = ""
    for r in rows[::-1]:
        if len(r) < 12:
            continue
        is_adv = "Advised" in r[9]
        badge_bg = "#FEE2E2" if is_adv else "#DCFCE7"
        badge_fg = "#991B1B" if is_adv else "#166534"
        trs += f"""
        <tr>
            <td style="font-weight:800; color:#1E3A8A; white-space:nowrap;">{r[0]}</td>
            <td style="color:#475569; white-space:nowrap;">{r[1]}</td>
            <td style="font-weight:800; color:#0F172A;">{r[2]}</td>
            <td>{r[3]}</td>
            <td style="font-weight:700;">{r[4]}</td>
            <td style="font-weight:800; color:#1D4ED8;">{r[5]}</td>
            <td>{r[6]}</td>
            <td>{r[7]}</td>
            <td style="font-weight:700;">{r[8]}</td>
            <td><span style="background:{badge_bg}; color:{badge_fg}; font-weight:800; padding:4px 10px; border-radius:999px; font-size:0.78rem; white-space:nowrap;">{r[9]}</span></td>
            <td>{r[10]}</td>
            <td style="font-size:0.82rem; color:#334155; max-width:260px;">{r[11]}</td>
        </tr>"""

    if not trs:
        trs = '<tr><td colspan="12" style="text-align:center; padding:28px; color:#64748B; font-weight:600;">No screenings recorded yet. Complete a screening in the app to populate this registry.</td></tr>'

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Community Brain Health Screening Registry</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
    body {{
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
        background: #F8FAFC;
        color: #0F172A;
        margin: 0;
        padding: 36px;
    }}
    .wrap {{
        max-width: 1320px;
        margin: 0 auto;
        background: #FFFFFF;
        border: 1.5px solid #E2E8F0;
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
    }}
    .hdr {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 20px;
        margin-bottom: 24px;
    }}
    .eyebrow {{
        font-size: 0.75rem;
        font-weight: 800;
        color: #2563EB;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }}
    h1 {{
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0;
        color: #0F172A;
        letter-spacing: -0.02em;
    }}
    .stats {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 28px;
    }}
    .stat-card {{
        background: #F8FAFC;
        border: 1.5px solid #E2E8F0;
        border-radius: 14px;
        padding: 16px 20px;
    }}
    .stat-lbl {{
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .stat-val {{
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
    }}
    th {{
        background: #0F172A;
        color: #FFFFFF;
        font-weight: 700;
        text-align: left;
        padding: 12px 14px;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    td {{
        padding: 12px 14px;
        border-bottom: 1px solid #E2E8F0;
        vertical-align: middle;
    }}
    tr:nth-child(even) td {{
        background: #F8FAFC;
    }}
</style>
</head>
<body>
<div class="wrap">
    <div class="hdr">
        <div>
            <div class="eyebrow">Neurogenetics & Elder Care Initiative</div>
            <h1>Community Brain Health & AD8 Screening Registry</h1>
        </div>
        <div style="text-align:right; font-size:0.85rem; color:#475569; font-weight:600;">
            Generated: {datetime.now().strftime("%d %b %Y, %I:%M %p")}<br>
            Target Cohort Goal: 100 Families
        </div>
    </div>
    <div class="stats">
        <div class="stat-card">
            <div class="stat-lbl">Total Families Screened</div>
            <div class="stat-val" style="color:#2563EB;">{total} / 100</div>
        </div>
        <div class="stat-card">
            <div class="stat-lbl">Clinical Evaluation Advised</div>
            <div class="stat-val" style="color:#DC2626;">{high_risk}</div>
        </div>
        <div class="stat-card">
            <div class="stat-lbl">Within Healthy Baseline</div>
            <div class="stat-val" style="color:#16A34A;">{normal_cnt}</div>
        </div>
    </div>
    <div style="overflow-x:auto;">
        <table>
            <thead>
                <tr>{"".join(f"<th>{h}</th>" for h in CSV_HEADERS)}</tr>
            </thead>
            <tbody>
                {trs}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>"""
    return html.encode("utf-8")

def render_sidebar_tracker(*args, **kwargs):
    key_suffix = args[0] if args else kwargs.get("key_suffix", "main")
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
        @media (prefers-color-scheme: dark) {{
            .impact-card-box {{
                background: #0F172A !important;
                border-color: #334155 !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
            }}
            .impact-eyebrow {{ color: #60A5FA !important; }}
            .impact-badge-inline {{
                background: #1E293B !important;
                color: #93C5FD !important;
                border-color: #3B82F6 !important;
            }}
            .impact-count-line {{ color: #F8FAFC !important; }}
            .impact-sub-line {{ color: #94A3B8 !important; }}
            .impact-progress-track {{ background: #1E293B !important; }}
            .impact-progress-fill {{ background: linear-gradient(90deg, #2563EB 0%, #38BDF8 100%) !important; }}
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

    with st.sidebar.expander("🔒 Researcher Data Export"):
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
                label="📄 Styled Clinical Registry (.HTML)",
                data=get_styled_html_report(),
                file_name="community_screening_registry.html",
                mime="text/html",
                use_container_width=True,
                key=f"dl_html_btn_{key_suffix}"
            )
            st.download_button(
                label="📊 Clean Spreadsheet (.CSV)",
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
                    if len(r) >= 6:
                        st.markdown(f"- **{r[2]}** ({r[4]}) • `{r[5]}`")
