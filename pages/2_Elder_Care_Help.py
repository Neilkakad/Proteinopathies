import streamlit as st
import streamlit.components.v1 as components
import os, subprocess, sys, hashlib, json, urllib.request, urllib.parse, ssl, re
from datetime import datetime

try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl._create_unverified_context()

st.set_page_config(page_title='Elder Care Help', page_icon='🤝', layout='wide')

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    /* Preserve Material Icons so sidebar toggle arrow always renders properly */
    .stMarkdown, p, h1, h2, h3, h4, label,
    .q-card, .inst-card, .rule-card, .step-bar, .score-panel, .symptom-card, .hospital-card, .wellness-sheet, .wellness-col-card, .lang-box,
    [data-testid="stRadio"] label p {
        font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.01em;
    }
    [data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }

    .block-container { padding-top: 2.0rem !important; padding-bottom: 4rem !important; max-width: 980px !important; }
    [data-testid="stSidebarNav"] a span { font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', sans-serif !important; font-size: 1.0rem !important; font-weight: 600 !important; color: #0F172A !important; white-space: normal !important; line-height: 1.45 !important; }
    
    /* Vibrant Primary Buttons & Download Buttons */
    div.stButton > button[kind="primary"], div.stDownloadButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        min-height: 54px !important;
        padding: 0.7rem 1.4rem !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 16px rgba(37, 99, 235, 0.25) !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button[kind="primary"]:hover, div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
        box-shadow: 0 8px 20px rgba(29, 78, 216, 0.35) !important;
    }
    div.stButton > button[kind="secondary"] {
        border-radius: 14px !important;
        min-height: 52px !important;
        font-size: 1.02rem !important;
        font-weight: 700 !important;
        border: 1.5px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* Equal Height Language Selection Cards */
    .lang-box {
        background: linear-gradient(145deg, #EFF6FF 0%, #F8FAFC 100%);
        border: 1.5px solid #BFDBFE;
        border-top: 5px solid #2563EB;
        border-radius: 18px;
        padding: 24px 22px;
        min-height: 158px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.06);
    }
    .lang-box-title { font-size: 1.22rem; font-weight: 800; color: #1E3A8A; margin-bottom: 8px; }
    .lang-box-desc { font-size: 1.02rem; color: #334155; line-height: 1.6; font-weight: 500; margin: 0; }

    /* Sleek Step Progress Bar */
    .step-bar { display: flex; justify-content: space-between; gap: 10px; margin: 4px 0 20px 0; background: #F1F5F9; padding: 7px; border-radius: 14px; border: 1px solid #CBD5E1; }
    .step-pill { flex: 1; text-align: center; padding: 10px 8px; border-radius: 10px; font-size: 0.94rem; font-weight: 700; color: #475569; }
    .step-pill.active { background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%); color: #FFFFFF !important; box-shadow: 0 4px 10px rgba(37,99,235,0.22); }
    .step-pill.done { background: #DCFCE7; color: #166534 !important; }

    /* Clean Age & Rule Cards */
    .page-header-title { font-size: 2.1rem; font-weight: 800; color: #0F172A; line-height: 1.3; margin-bottom: 16px; text-align: center; }
    .inst-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #EFF6FF 100%);
        border: 1.5px solid #BFDBFE;
        border-left: 6px solid #2563EB;
        border-radius: 18px;
        padding: 22px 26px;
        margin: 8px 0 12px 0;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.06);
    }
    .inst-card-title { font-size: 1.35rem; font-weight: 800; color: #0F172A; line-height: 1.4; margin-bottom: 6px; }
    .inst-card-sub { font-size: 1.02rem; color: #334155; font-weight: 500; line-height: 1.6; margin: 0; }

    .rule-card {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1.5px solid #FDE68A;
        border-left: 6px solid #D97706;
        border-radius: 18px;
        padding: 20px 24px;
        margin: 20px 0 10px 0;
    }
    .rule-card-title { font-size: 1.14rem; font-weight: 800; color: #92400E; margin-bottom: 6px; }
    .rule-card-body { font-size: 1.0rem; color: #78350F; line-height: 1.6; font-weight: 600; }

    /* Centered Question Cards & Dead-Center Radio Options */
    .q-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 18px;
        padding: 22px 26px 18px 26px;
        border: 1.5px solid #CBD5E1;
        border-top: 4px solid #3B82F6;
        margin-top: 18px;
        margin-bottom: 8px;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
        text-align: center;
    }
    .q-title { font-size: 1.2rem; font-weight: 800; color: #0F172A; line-height: 1.55; text-align: center; }
    
    /* Force Streamlit Radio Container to Dead-Center in Both English & Hindi */
    div[data-testid="stElementContainer"]:has(div[data-testid="stRadio"]),
    div.element-container:has(div[data-testid="stRadio"]),
    div[data-testid="stRadio"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 4px auto 14px auto !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        background: #EFF6FF !important;
        padding: 12px 32px !important;
        border-radius: 999px !important;
        border: 1.5px solid #93C5FD !important;
        gap: 32px !important;
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08) !important;
    }
    div[data-testid="stRadio"] label { cursor: pointer !important; padding: 4px 10px !important; font-weight: 700 !important; }
    audio { width: 100%; height: 42px; margin: 6px 0 12px 0; border-radius: 10px; }

    /* Calm, Motivating Report Banners (Never Scary) */
    .care-doc-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: #FFFFFF !important;
        border-radius: 20px;
        padding: 26px 30px;
        margin: 14px 0 14px 0;
        box-shadow: 0 12px 28px rgba(37, 99, 235, 0.22);
        border: 2px solid #93C5FD;
    }
    .healthy-doc-banner {
        background: linear-gradient(135deg, #047857 0%, #10B981 100%);
        color: #FFFFFF !important;
        border-radius: 20px;
        padding: 26px 30px;
        margin: 14px 0 14px 0;
        box-shadow: 0 12px 28px rgba(16, 185, 129, 0.22);
        border: 2px solid #6EE7B7;
    }
    .score-panel {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 2px solid #CBD5E1;
        border-radius: 20px;
        padding: 22px 26px;
        margin-bottom: 22px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }
    .score-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 16px; }
    .score-metric { background: #FFFFFF; border: 1.5px solid #CBD5E1; border-radius: 16px; padding: 16px 12px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    .score-num { font-size: 1.75rem; font-weight: 800; color: #0F172A; line-height: 1.2; }
    .score-lbl { font-size: 0.88rem; font-weight: 700; color: #334155; margin-top: 6px; }
    .score-unit { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 800; margin-top: 6px; }

    /* Calm Symptom, Hospital & Wellness Cards */
    .symptom-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1.5px solid #BFDBFE;
        border-left: 6px solid #2563EB;
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.05);
    }
    .mild-symptom-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #FFFBEB 100%);
        border: 1.5px solid #FDE68A;
        border-left: 6px solid #D97706;
        border-radius: 16px;
        padding: 18px 22px;
        margin-bottom: 14px;
    }
    .hospital-card {
        background: #FFFFFF;
        border: 1.5px solid #BFDBFE;
        border-left: 6px solid #2563EB;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.06);
    }
    .wellness-sheet {
        background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
        border: 2px solid #93C5FD;
        border-radius: 20px;
        padding: 24px 28px;
        margin-top: 18px;
        margin-bottom: 14px;
    }
    .wellness-col-card {
        background: #FFFFFF;
        border: 1.5px solid #CBD5E1;
        border-top: 5px solid #10B981;
        border-radius: 16px;
        padding: 22px;
        height: 100%;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.04);
    }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.expanduser('~/Documents/Neuro-Genetic-Visualizer')
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')
CACHE_DIR = os.path.join(AUDIO_DIR, 'tts_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

@st.cache_data(show_spinner=False)
def _read_audio_cached(abs_path, mtime):
    with open(abs_path, 'rb') as f:
        return f.read()

def load_audio_bytes(rel_or_abs_path):
    candidates = [
        rel_or_abs_path,
        os.path.join(BASE_DIR, rel_or_abs_path),
        os.path.join(AUDIO_DIR, os.path.basename(rel_or_abs_path))
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.getsize(p) > 100:
            return _read_audio_cached(os.path.abspath(p), os.path.getmtime(p))
    return None

@st.cache_data(show_spinner=False)
def get_Dynamic_Result_Voice(text, lang, tag='v140_fast'):
    """
    Fast, cached, calm & motivating female voice synthesis.
    Uses a fast 5s timeout with instant gTTS fallback so the report never lags.
    """
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    clean_text = clean_text.replace('/', ' ').replace('—', ', ').replace('*', '').replace('•', ' ').replace('(', ', ').replace(')', ', ')
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    h = hashlib.md5(f'{tag}_{lang}_{clean_text}'.encode('utf-8')).hexdigest()[:16]
    fp = os.path.join(CACHE_DIR, f'calm_voice_{lang}_{h}.mp3')
    if os.path.exists(fp) and os.path.getsize(fp) > 1000:
        return load_audio_bytes(fp)
    voice = 'hi-IN-SwaraNeural' if lang == 'hi' else 'en-IN-NeerjaNeural'
    try:
        subprocess.run(
            [sys.executable, '-m', 'edge_tts', '--voice', voice, '--rate=-4%', '--pitch=+0Hz', '--text', clean_text, '--write-media', fp],
            check=True, timeout=6, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if os.path.exists(fp) and os.path.getsize(fp) > 1000:
            return load_audio_bytes(fp)
    except Exception:
        pass
    try:
        from gtts import gTTS
        gTTS(text=clean_text, lang='hi' if lang == 'hi' else 'en', tld='co.in', slow=False).save(fp)
        if os.path.exists(fp) and os.path.getsize(fp) > 500:
            return load_audio_bytes(fp)
    except Exception:
        pass
    return None

def force_scroll_to_top(step_name, nav_count):
    st.markdown("<div id='top-anchor-point'></div>", unsafe_allow_html=True)
    components.html(
        f"""
        <script>
            // trigger_id: {step_name}_{nav_count}
            (function() {{
                function resetScroll() {{
                    try {{
                        const doc = window.parent.document;
                        if (doc.activeElement && doc.activeElement !== doc.body) {{
                            doc.activeElement.blur();
                        }}
                        const anchor = doc.getElementById('top-anchor-point');
                        if (anchor) {{
                            anchor.scrollIntoView({{top: 0, behavior: 'instant', block: 'start'}});
                        }}
                        const selectors = [
                            '[data-testid="stMain"]',
                            '[data-testid="stAppViewContainer"]',
                            '[data-testid="stVerticalBlock"]',
                            'section.main',
                            '.main',
                            'html',
                            'body'
                        ];
                        selectors.forEach(sel => {{
                            doc.querySelectorAll(sel).forEach(el => {{
                                if (el.scrollTop > 0) el.scrollTop = 0;
                                try {{ el.scrollTo({{top: 0, left: 0, behavior: 'instant'}}); }} catch(e){{}}
                            }});
                        }});
                        window.parent.scrollTo(0, 0);
                    }} catch (err) {{}}
                }}
                resetScroll();
                setTimeout(resetScroll, 30);
                setTimeout(resetScroll, 100);
                setTimeout(resetScroll, 220);
            }})();
        </script>
        """,
        height=0,
    )

ARDSI_CHAPTERS = {
    'Maharashtra': ('ARDSI Mumbai & Maharashtra Chapter', '+91-22-24938022', 'Lower Parel, Mumbai - 400013'),
    'Delhi': ('ARDSI Delhi & NCR Chapter', '+91-11-26922940', 'Lajpat Nagar, New Delhi - 110024'),
    'Karnataka': ('ARDSI Bengaluru Chapter', '+91-80-22258937', 'Vasanth Nagar, Bengaluru - 560052'),
    'Tamil Nadu': ('ARDSI Chennai Chapter', '+91-44-26412030', 'Kilpauk, Chennai - 600010'),
    'Kerala': ('ARDSI National Office', '+91-484-2808088', 'Kochi / Thrissur - 680506'),
    'West Bengal': ('ARDSI Kolkata Chapter', '+91-33-24653564', 'Ballygunge, Kolkata - 700019'),
    'Telangana': ('ARDSI Hyderabad Chapter', '+91-40-27664660', 'Secunderabad, Hyderabad - 500003'),
    'Gujarat': ('ARDSI Ahmedabad & Gujarat Chapter', '+91-79-26857555', 'Ahmedabad, Gujarat - 380015'),
    'Uttar Pradesh': ('ARDSI Lucknow & UP Nodal Center', '+91-522-2668700', 'SGPGI / KGMU Network, Lucknow - 226014'),
    'Rajasthan': ('ARDSI Jaipur & Rajasthan Nodal Center', '+91-141-2560291', 'SMS Medical Campus, Jaipur - 302004'),
}

@st.cache_data(ttl=7200, show_spinner=False)
def lookup_india_pincode_and_clinics(pincode):
    pin = pincode.strip()
    if len(pin) != 6 or not pin.isdigit():
        return {'error': 'Invalid PIN'}
    
    district, state, locality, block = '', '', '', ''
    post_offices = []
    try:
        req = urllib.request.Request(f'https://api.postalpincode.in/pincode/{pin}', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2.5, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and data[0].get('Status') == 'Success':
                pos = data[0].get('PostOffice', [])
                if pos:
                    district = pos[0].get('District', '')
                    state = pos[0].get('State', '')
                    block = pos[0].get('Block', '') or pos[0].get('Taluk', '')
                    raw_name = pos[0].get('Name', '')
                    locality = re.sub(r'\b(B\.O|S\.O|H\.O|G\.P\.O|PO|SO|BO|HO)\b\.?', '', raw_name, flags=re.IGNORECASE).strip(' ,()-')
                    for po in pos[:4]:
                        clean_po = re.sub(r'\b(B\.O|S\.O|H\.O|G\.P\.O)\b\.?', '', po.get('Name', ''), flags=re.IGNORECASE).strip(' ,()-')
                        if clean_po and clean_po not in post_offices:
                            post_offices.append(clean_po)
    except Exception:
        pass

    clinics = []
    seen = set()

    hq = f'hospital in {locality or district}, {district or state}'
    if locality or district:
        try:
            url = f'https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(hq)}&format=json&addressdetails=1&extratags=1&limit=6&countrycodes=in'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
            with urllib.request.urlopen(req, timeout=2.0, context=SSL_CTX) as resp:
                h_list = json.loads(resp.read().decode('utf-8'))
                for item in h_list:
                    name = item.get('name') or item.get('display_name', '').split(',')[0]
                    if not name or name in seen or len(name) < 3:
                        continue
                    seen.add(name)
                    addr_obj = item.get('address', {})
                    ext_obj = item.get('extratags', {}) or {}
                    c_pin = addr_obj.get('postcode') or pin
                    road = addr_obj.get('road') or addr_obj.get('suburb') or addr_obj.get('neighbourhood') or locality
                    city_v = addr_obj.get('city') or addr_obj.get('state_district') or district
                    full_addr = f"{road}, {city_v}, {state} - {c_pin}".strip(', ')
                    phone = ext_obj.get('phone') or ext_obj.get('contact:phone') or '108 / 104 (24x7 Medical Helpline)'
                    is_govt = any(k in name.lower() for k in ['government', 'govt', 'municipal', 'bmc', 'district', 'civil', 'aiims', 'kem', 'sion', 'nair', 'rajawadi', 'shatabdi', 'phc', 'chc', 'general hospital', 'medical college'])
                    clinics.append({
                        'name': name,
                        'sector': 'Government Hospital' if is_govt else 'Hospital & Medical Center',
                        'sector_hi': 'सरकारी अस्पताल' if is_govt else 'अस्पताल और मेडिकल सेंटर',
                        'phone': phone,
                        'address': full_addr,
                        'pincode': c_pin,
                        'maps_url': f'https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(name + " " + city_v + " " + c_pin)}'
                    })
        except Exception:
            pass

    loc_label = locality or block or district or f"PIN {pin}"
    dist_label = district or state or "India"
    guaranteed_centers = [
        {
            'name': f"Civil / District Government Hospital ({dist_label})",
            'sector': 'Government District Hospital (Neurology & Geriatrics OPD)',
            'sector_hi': 'सरकारी ज़िला अस्पताल (दिमागी व बुज़ुर्ग ओपीडी)',
            'phone': '108 (Ambulance) / 104 (Health Helpline) / 14567 (Elderline)',
            'address': f"District Hospital Area, {loc_label}, {dist_label}, {state} - {pin}",
            'pincode': pin,
            'maps_url': f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'Government District Civil Hospital near {loc_label} {dist_label} {pin}')}"
        },
        {
            'name': f"Primary / Community Health Center (PHC / CHC — {loc_label})",
            'sector': 'Government Primary Health Center',
            'sector_hi': 'प्राथमिक / सामुदायिक स्वास्थ्य केंद्र (PHC/CHC)',
            'phone': '14416 (Tele-MANAS Neuro Helpline) / 104 (Medical Helpline)',
            'address': f"{', '.join(post_offices[:2]) or loc_label}, {dist_label}, {state} - {pin}",
            'pincode': pin,
            'maps_url': f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(f'Hospital Clinic near {loc_label} {dist_label} {pin}')}"
        }
    ]
    for gc in guaranteed_centers:
        if len(clinics) < 6:
            clinics.append(gc)

    clinics.sort(key=lambda x: 0 if 'Government' in x['sector'] else 1)
    ardsi = ARDSI_CHAPTERS.get(state, ('ARDSI National Dementia Helpline & Memory Clinic Network', '+91-484-2808088', f'{dist_label}, {state} - {pin}'))
    return {
        'pin': pin,
        'locality': locality or district or pin,
        'district': district or pin,
        'state': state or 'India',
        'clinics': clinics[:6],
        'ardsi': ardsi
    }

SCREENING_DATA = {
    'intro': {
        'en': {'welcome': 'Family Brain Health & Memory Check', 'title_box': '🇬🇧 English Screening', 'desc': 'A simple, caring family tool to check early changes in memory, daily habits, and body movement—calibrated for your loved one’s exact age.', 'btn_text': 'Continue in English ➔', 'audio_file': 'audio/intro_en.mp3'},
        'hi': {'welcome': 'दिमागी सेहत और याददाश्त की जाँच', 'title_box': '🇮🇳 हिंदी में जाँच', 'desc': 'उम्र के हिसाब से अपने परिवार के बुज़ुर्गों या सदस्यों की याददाश्त, शरीर और चलने-फिरने में आ रहे शुरुआती बदलावों को पहचानने का आसान तरीका।', 'btn_text': 'हिंदी में आगे बढ़ें ➔', 'audio_file': 'audio/intro_hi.mp3'}
    },
    'instructions': {
        'en': {
            'title': 'Patient Age & Simple Instructions',
            'age_title': 'How old is the person being checked today?',
            'age_sub': 'Listen to the calm voice guide and move the slider right below to select their exact age (in Years). Medical advice, diet, and exercises adjust automatically.',
            'age_voice_script': 'Please use the slider below to select your loved one’s exact age. Selecting their age helps us calibrate their memory score, daily nutrition, and gentle exercises accurately for their stage of life.',
            'rule_title': 'Important Rule Before You Start:',
            'rule': 'Select "Yes, a change" ONLY if you noticed a new change in the last few years caused by memory or thinking trouble—not just due to weak eyesight or joint pain.',
            'btn_text': 'Start Step 1 Check ➔',
            'back_text': '⬅ Change Language',
            'audio_file': 'audio/inst_en.mp3',
            'age_audio': 'audio/custom_age_en.mp3'
        },
        'hi': {
            'title': 'व्यक्ति की उम्र और आसान निर्देश',
            'age_title': 'जिस व्यक्ति की जाँच हो रही है, उनकी सही उम्र क्या है?',
            'age_sub': 'नीचे ऑडियो सुनें और तुरंत नीचे दिए गए स्लाइडर से उनकी सही उम्र (वर्षों में) चुनें। उम्र के अनुसार डॉक्टरी सलाह और खान-पान अपने-आप तय होगा।',
            'age_voice_script': 'कृपया नीचे दिए गए स्लाइडर से अपने परिवार के सदस्य की सही उम्र चुनें। सही उम्र चुनने से उनकी याददाश्त की रिपोर्ट, रोज़ के खान-पान और व्यायाम की सलाह बिल्कुल सटीक तैयार होगी।',
            'rule_title': 'सवालों का जवाब देने का आसान नियम:',
            'rule': '"हाँ, नया बदलाव है" तभी चुनें जब पिछले कुछ सालों में याददाश्त या सोचने की वजह से यह बदलाव आया हो—कमज़ोर नज़र या घुटनों के दर्द की वजह से नहीं।',
            'btn_text': 'जाँच शुरू करें (कदम 1) ➔',
            'back_text': '⬅ भाषा बदलें',
            'audio_file': 'audio/inst_hi.mp3',
            'age_audio': 'audio/custom_age_hi.mp3'
        }
    },
    'bucket1': {
        'title_en': 'Step 1: Body Health & Vitamin Check (3 Questions)', 'title_hi': 'पहला कदम: शरीर और विटामिन की जाँच (3 सवाल)',
        'desc_en': 'Checks if weak eyesight, Vitamin B12 deficiency, or sudden fever is causing confusion.', 'desc_hi': 'जाँचें कि कहीं कमज़ोर नज़र, विटामिन की कमी या बुखार की वजह से तो उलझन नहीं हो रही।',
        'audio_en': 'audio/step1_desc_en.mp3', 'audio_hi': 'audio/step1_desc_hi.mp3',
        'questions': [
            {'id': 'q_eyes_ears', 'code': 'B1', 'bucket_tag_en': 'Eyesight & Hearing', 'bucket_tag_hi': 'आँख और कान', 'en': '1. Eyes & Ears: Do they struggle to see clearly, or do you have to speak loudly so they can hear you?', 'hi': '1. आँख और कान: क्या उन्हें साफ देखने में दिक्कत होती है, या उनसे बात करने के लिए आपको ज़ोर से बोलना पड़ता है?', 'label_en': 'Weak Eyesight or Difficulty Hearing', 'label_hi': 'कमज़ोर नज़र या ऊँचा सुनाई देना', 'doc_note': 'Sensory deficit (vision/hearing) affecting communication.', 'why_en': 'When someone cannot see or hear clearly, they miss parts of conversations and seem forgetful. A simple eye checkup for glasses or ear cleaning restores their confidence quickly.', 'why_hi': 'जब साफ दिखाई या सुनाई नहीं देता, तो इंसान पूरी बात सुन नहीं पाता और परिवार को लगता है कि वह भूल रहा है। चश्मे या कान की सामान्य जाँच कराने से तुरंत आराम मिलता है।'},
            {'id': 'q_weakness', 'code': 'B2', 'bucket_tag_en': 'Vitamins & Strength', 'bucket_tag_hi': 'विटामिन और ताकत', 'en': '2. Weakness & Tingling: Do their hands or feet feel numb/tingling, or do they feel very weak and tired?', 'hi': '2. कमज़ोरी और सुन्नपन: क्या उनके हाथ-पैरों में सुन्नपन या झुनझुनी होती है, या वे बहुत कमज़ोर और थके दिखते हैं?', 'label_en': 'Numbness in Hands/Feet or Body Weakness', 'label_hi': 'हाथ-पैर में सुन्नपन और शरीर में कमज़ोरी', 'doc_note': 'Peripheral paresthesia / fatigue — evaluate Vitamin B12, Thyroid (TSH), and Hemoglobin.', 'why_en': 'Numbness in the hands or feet and constant tiredness are classic signs of Vitamin B12 deficiency, thyroid imbalance, or low hemoglobin. A simple blood test and vitamin tablets can completely fix this.', 'why_hi': 'हाथ-पैर सुन्न पड़ना और थकान शरीर में विटामिन B12, थायराइड या खून की कमी का मुख्य लक्षण है, जिससे याददाश्त भी कमज़ोर लगती है। खून की साधारण जाँच और ताकत की दवाइयों से यह पूरी तरह ठीक हो जाता है।'},
            {'id': 'q_fever', 'code': 'B3', 'bucket_tag_en': 'Recent Fever / Infection', 'bucket_tag_hi': 'हाल का बुखार या इन्फेक्शन', 'en': '3. Sudden Confusion (2–3 Days): Did this confusion start suddenly in the last 2–3 days along with fever or burning urine?', 'hi': '3. अचानक घबराहट (2-3 दिन): क्या यह उलझन पिछले 2-3 दिनों में अचानक बुखार या पेशाब में जलन के साथ शुरू हुई है?', 'label_en': 'Sudden 2–3 Day Fever or Urine Infection Confusion', 'label_hi': '2-3 दिन में अचानक बुखार या पेशाब के इन्फेक्शन से उलझन', 'doc_note': 'ACUTE ONSET (2–3 days) confusion with fever/dysuria — rule out acute delirium / UTI / hyponatremia.', 'why_en': 'Sudden confusion over just 2 to 3 days is almost always caused by a simple, treatable infection or low water and salt levels in the body, and improves rapidly once a doctor treats the infection.', 'why_hi': 'सिर्फ 2 से 3 दिनों में अचानक आई उलझन किसी बड़ी दिमागी बीमारी से नहीं, बल्कि मामूली इन्फेक्शन या शरीर में पानी-नमक की कमी से होती है, और डॉक्टर की साधारण दवाई से बहुत जल्दी ठीक हो जाती है।'}
        ],
        'options_en': ['Yes, a change', 'No, no change', 'Dont know'], 'options_hi': ['हाँ, नया बदलाव है', 'नहीं, कोई बदलाव नहीं', 'पता नहीं'],
        'btn_en': 'Next: Step 2 (Memory Check) ➔', 'btn_hi': 'अगला कदम: याददाश्त की जाँच ➔', 'back_en': '⬅ Back to Age Setup', 'back_hi': '⬅ उम्र कार्ड पर वापस जाएं'
    },
    'bucket2': {
        'title_en': 'Step 2: Memory & Daily Thinking Check (8 Questions)', 'title_hi': 'चरण 2: याददाश्त और रोज़मर्रा की समझ (8 सवाल)',
        'desc_en': 'Checks 8 everyday memory and thinking habits. Answering "Yes" to 2 or more means a doctor checkup is helpful.', 'desc_hi': 'रोज़मर्रा की याददाश्त से जुड़े 8 आसान सवाल। 2 या अधिक सवालों में "हाँ" होने पर डॉक्टर की सलाह लेना फायदेमंद रहता है।',
        'audio_en': 'audio/step2_desc_en.mp3', 'audio_hi': 'audio/step2_desc_hi.mp3',
        'questions': [
            {'id': 'q_d1', 'code': 'M-1', 'bucket_tag_en': 'Judgment & Decisions', 'bucket_tag_hi': 'सही-गलत के फैसले', 'en': '1. Making Decisions: Do they have trouble making everyday decisions, make unsafe money choices, or get easily tricked?', 'hi': '1. सही-गलत के फैसले: क्या उन्हें रोज़मर्रा के फैसले लेने में दिक्कत होती है, या वे अनजान लोगों की बातों में जल्दी आ जाते हैं?', 'label_en': 'Trouble Making Safe Everyday or Money Decisions', 'label_hi': 'सही-गलत और पैसों के फैसले लेने में उलझन', 'doc_note': 'Impaired executive judgment and financial decision-making.', 'why_en': 'Difficulty making everyday decisions shows the planning center of the brain needs gentle family support and a routine medical checkup.', 'why_hi': 'रोज़मर्रा के सही-गलत या पैसों के फैसलों में उलझन होना बताता है कि दिमाग के सोचने वाले हिस्से को परिवार के साथ और डॉक्टर की सलाह से बहुत सहारा मिलेगा।'},
            {'id': 'q_d2', 'code': 'M-2', 'bucket_tag_en': 'Interest & Mood', 'bucket_tag_hi': 'मन और रुचि', 'en': '2. Less Interest: Have they lost interest in hobbies, festivals, prayers, or sitting and chatting with family?', 'hi': '2. काम और त्योहारों में मन: क्या अब उनका त्योहारों, पूजा-पाठ या घरवालों से बातचीत करने में पहले से कम मन लगता है?', 'label_en': 'Less Interest in Festivals, Hobbies & Family Talk', 'label_hi': 'त्योहारों और परिवार की बातचीत में कम मन लगना', 'doc_note': 'Apathy / decreased interest in hobbies and social engagement.', 'why_en': 'Quietness or less interest in festivals and hobbies often happens due to mild low mood or fatigue, which responds wonderfully to warm family conversation and medical care.', 'why_hi': 'त्योहारों या बातचीत में कम मन लगना अक्सर हल्की उदासी या थकान से होता है, जो परिवार के प्यार, बातचीत और डॉक्टर की सलाह से बहुत जल्दी बेहतर हो जाता है।'},
            {'id': 'q_d3', 'code': 'M-3', 'bucket_tag_en': 'Short-Term Memory', 'bucket_tag_hi': 'हाल की याददाश्त', 'en': '3. Repeating Things: Do they ask the exact same question or tell the same story over and over within a short time?', 'hi': '3. बात दोहराना: क्या वे एक ही सवाल या एक ही बात को थोड़ी-थोड़ी देर में बार-बार पूछते या दोहराते हैं?', 'label_en': 'Repeating Questions or Stories Again and Again', 'label_hi': 'थोड़ी-थोड़ी देर में एक ही सवाल या बात दोहराना', 'doc_note': 'Short-term episodic repetition (repeating questions/stories).', 'why_en': 'Repeating questions happens when the short-term memory center needs a little extra support holding onto recent answers. Doctors have gentle medicines that strengthen these memory pathways.', 'why_hi': 'बात को दोहराना जानबूझकर नहीं होता, बल्कि दिमाग को नई बात सहेजने में थोड़ा सहारा चाहिए होता है। डॉक्टर की साधारण दवाइयों से याददाश्त की नसों को अच्छी मज़बूती मिलती है।'},
            {'id': 'q_d4', 'code': 'M-4', 'bucket_tag_en': 'Using Daily Appliances', 'bucket_tag_hi': 'रोज़ के उपकरण', 'en': '4. Using Daily Items: Do they struggle to use familiar things like a mobile phone, TV remote, or kitchen stove?', 'hi': '4. रोज़ की चीज़ें चलाना: क्या उन्हें मोबाइल फोन, टीवी रिमोट या गैस चूल्हा जैसी रोज़ की चीज़ें चलाने में उलझन होती है?', 'label_en': 'Trouble Using Phone, TV Remote, or Household Items', 'label_hi': 'मोबाइल फोन, टीवी रिमोट या घरेलू चीज़ें चलाने में उलझन', 'doc_note': 'Difficulty operating familiar household appliances / procedural praxis.', 'why_en': 'Trouble using a TV remote or phone simply means step-by-step coordination needs a calm checkup and simplified daily tools at home.', 'why_hi': 'रिमोट या फोन चलाने में उलझन का मतलब है कि उन्हें आसान दिनचर्या और डॉक्टर के मार्गदर्शन से बहुत आराम मिलेगा।'},
            {'id': 'q_d5', 'code': 'M-5', 'bucket_tag_en': 'Time & Date Awareness', 'bucket_tag_hi': 'महीना और साल की पहचान', 'en': '5. Forgetting Month or Year: Do they often forget which month, year, or season it is right now?', 'hi': '5. महीना और साल भूलना: क्या वे अक्सर भूल जाते हैं कि अभी कौन सा महीना, साल या मौसम चल रहा है?', 'label_en': 'Forgetting the Current Month, Year, or Season', 'label_hi': 'चल रहा महीना, साल या मौसम भूल जाना', 'doc_note': 'Temporal disorientation to current month or year.', 'why_en': 'Forgetting the month or year is common when daily routines feel similar. Placing a large wall calendar in their room and consulting a doctor keeps them confident.', 'why_hi': 'महीना या साल भूल जाने पर कमरे में बड़े अक्षरों वाला कैलेंडर लगाना और डॉक्टर से परामर्श लेना उन्हें बहुत आत्मविश्वास देता है।'},
            {'id': 'q_d6', 'code': 'M-6', 'bucket_tag_en': 'Money & Calculations', 'bucket_tag_hi': 'पैसों का हिसाब', 'en': '6. Counting Money & Bills: Do they struggle to count currency notes, check shop change, or manage household bills?', 'hi': '6. पैसों का हिसाब: क्या उन्हें नोट गिनने, दुकान पर छुट्टे पैसे सँभालने या घर के बिल के हिसाब में दिक्कत होती है?', 'label_en': 'Trouble Counting Currency Notes or Managing Bills', 'label_hi': 'नोट गिनने और पैसों के हिसाब-किताब में परेशानी', 'doc_note': 'Difficulty handling financial affairs and calculations.', 'why_en': 'Difficulty counting change or managing bills is an early sign that benefits greatly from timely medical guidance and family assistance with shopping.', 'why_hi': 'नोट गिनने या हिसाब में गलती होने पर परिवार का छोटा-सा सहयोग और समय पर डॉक्टरी सलाह बहुत काम आती है।'},
            {'id': 'q_d7', 'code': 'M-7', 'bucket_tag_en': 'Medicines & Schedules', 'bucket_tag_hi': 'दवाई और ज़रूरी काम', 'en': '7. Remembering Medicines & Tasks: Do they forget doctor appointments, family events, or taking daily medicines?', 'hi': '7. दवाई और काम याद रखना: क्या वे रोज़ की दवाई लेना, डॉक्टर के पास जाना या घर के ज़रूरी काम भूल जाते हैं?', 'label_en': 'Forgetting Daily Medicines or Appointments', 'label_hi': 'रोज़ की दवाई लेना या ज़रूरी काम भूल जाना', 'doc_note': 'Impaired prospective memory affecting appointments and medication adherence.', 'why_en': 'Forgetting daily tablets is very easy to solve by using a morning-evening pill organizer box and having a family member hand them their medicines.', 'why_hi': 'दवाई भूलने की समस्या को सुबह-शाम के दवाई के डिब्बे (Pill Box) और परिवार की देखरेख से बहुत आसानी से संभाला जा सकता है।'},
            {'id': 'q_d8', 'code': 'M-8', 'bucket_tag_en': 'Daily Life Impact', 'bucket_tag_hi': 'रोज़मर्रा की दिनचर्या', 'en': '8. Everyday Forgetfulness: Is this forgetting or thinking trouble happening almost every single day now?', 'hi': '8. हर दिन की परेशानी: क्या भूलने और सोचने की यह परेशानी अब लगभग हर रोज़ दिखने लगी है?', 'label_en': 'Daily Problems with Memory & Thinking', 'label_hi': 'लगभग हर दिन भूलने और सोचने में परेशानी होना', 'doc_note': 'Consistent daily problems with thinking and memory affecting routine.', 'why_en': 'When forgetfulness happens daily, a calm visit to a doctor helps identify the exact cause and start supportive care that keeps their daily life comfortable.', 'why_hi': 'जब रोज़मर्रा में भूलने की दिक्कत दिखे, तो डॉक्टर की सलाह से सही विटामिन और दवाइयाँ शुरू करके उनकी दिनचर्या को बहुत आसान बनाया जा सकता है।'}
        ],
        'options_en': ['Yes, a change', 'No, no change', 'Dont know'], 'options_hi': ['हाँ, नया बदलाव है', 'नहीं, कोई बदलाव नहीं', 'पता नहीं'],
        'btn_en': 'Next: Step 3 (Movement Check) ➔', 'btn_hi': 'अगला कदम: चलने-फिरने की जाँच ➔', 'back_en': '⬅ Back to Step 1', 'back_hi': '⬅ पिछले कदम पर जाएं'
    },
    'bucket3': {
        'title_en': 'Step 3: Walking, Balance & Hand Steadiness (4 Questions)', 'title_hi': 'चरण 3: चलने-फिरने और संतुलन की जाँच (4 सवाल)',
        'desc_en': 'Checks for hand shaking at rest, small dragging steps, stiffness, or coughing while drinking water.', 'desc_hi': 'हाथ काँपना, छोटे कदम चलना, शरीर की अकड़न या पानी पीते समय ठसका लगने की जाँच।',
        'audio_en': 'audio/step3_desc_en.mp3', 'audio_hi': 'audio/step3_desc_hi.mp3',
        'questions': [
            {'id': 'q_m1', 'code': 'MV-1', 'bucket_tag_en': 'Hand Steadiness', 'bucket_tag_hi': 'हाथ की स्थिरता', 'en': '1. Hand Shaking: Does one hand, thumb, or jaw shake on its own while they are sitting quietly at rest?', 'hi': '1. हाथ काँपना: क्या आराम से चुपचाप बैठे समय उनका हाथ, अंगूठा या जबड़ा अपने आप काँपता है?', 'label_en': 'Hand or Thumb Shaking While Sitting Quietly', 'label_hi': 'आराम से बैठे समय हाथ या अंगूठा काँपना', 'doc_note': 'Resting tremor of hand/thumb/jaw (Extrapyramidal motor domain).', 'why_en': 'Hand shaking while resting happens when a natural brain messenger called dopamine is slightly low. Doctors have very effective tablets that steady the hands.', 'why_hi': 'शांत बैठे समय हाथ काँपना दिमाग में डोपामाइन की हल्की कमी से होता है, और डॉक्टर की साधारण दवाइयों से हाथ में बहुत अच्छी स्थिरता आ जाती है।'},
            {'id': 'q_m2', 'code': 'MV-2', 'bucket_tag_en': 'Walking & Balance', 'bucket_tag_hi': 'चाल और संतुलन', 'en': '2. Small Dragging Steps: Have their walking steps become very small, or do their feet drag on the floor?', 'hi': '2. छोटे कदम: क्या चलते समय उनके कदम बहुत छोटे हो गए हैं या वे पैर ज़मीन से घिसटकर चलते हैं?', 'label_en': 'Walking with Small or Dragging Steps', 'label_hi': 'छोटे कदम चलना या पैर घिसटकर चलना', 'doc_note': 'Shortened stride / shuffling gait with increased fall risk.', 'why_en': 'Small steps can be improved with simple physiotherapy stretches, supportive footwear, and nerve-supporting medication from a doctor.', 'why_hi': 'छोटे कदम चलने में हल्की फिजियोथेरेपी कसरत, आरामदायक जूते और डॉक्टर की सलाह से बहुत अच्छा सुधार आता है।'},
            {'id': 'q_m3', 'code': 'MV-3', 'bucket_tag_en': 'Muscle Flexibility', 'bucket_tag_hi': 'मांसपेशियों का लचीलापन', 'en': '3. Body Stiffness: Has their body become stiff when buttoning clothes, dressing, or turning over in bed?', 'hi': '3. शरीर में अकड़न: क्या अकड़न की वजह से कपड़े पहनने, बटन लगाने या बिस्तर पर करवट लेने में दिक्कत होती है?', 'label_en': 'Body Stiffness When Dressing or Turning in Bed', 'label_hi': 'कपड़े पहनने या करवट लेने में शरीर की अकड़न', 'doc_note': 'Limb rigidity / bradykinesia affecting dressing and bed mobility.', 'why_en': 'Muscle stiffness while dressing or turning in bed relaxes nicely with gentle warm oil massage, stretching, and doctor-prescribed muscle support.', 'why_hi': 'शरीर की अकड़न में हल्के व्यायाम और डॉक्टर द्वारा दी गई नसों को आराम देने वाली दवाई से बहुत राहत मिलती है।'},
            {'id': 'q_m4', 'code': 'MV-4', 'bucket_tag_en': 'Voice & Swallowing', 'bucket_tag_hi': 'आवाज़ और निगलना', 'en': '4. Soft Voice & Swallowing: Has their voice become very soft, or do they cough when drinking water?', 'hi': '4. धीमी आवाज़ और ठसका: क्या उनकी आवाज़ बहुत धीमी हो गई है, या पानी पीते समय खाँसी (ठसका) आती है?', 'label_en': 'Soft Voice or Coughing While Drinking Water', 'label_hi': 'धीमी आवाज़ या पानी पीते समय ठसका आना', 'doc_note': 'Hypophonia or coughing on thin liquids (swallowing coordination).', 'why_en': 'If they cough while drinking water, having them sit straight upright and take small, slow sips keeps swallowing completely safe.', 'why_hi': 'पानी पीते समय ठसका लगने पर उन्हें हमेशा सीधा बैठाकर छोटे-छोटे घूँट में पानी पिलाने से यह पूरी तरह सुरक्षित रहता है।'}
        ],
        'options_en': ['Yes, a change', 'No, no change', 'Dont know'], 'options_hi': ['हाँ, नया बदलाव है', 'नहीं, कोई बदलाव नहीं', 'पता नहीं'],
        'btn_en': 'Finish & View Full Health Report ➔', 'btn_hi': 'जाँच पूरी करें और पूरी रिपोर्ट देखें ➔', 'back_en': '⬅ Back to Step 2', 'back_hi': '⬅ पिछले कदम पर जाएं'
    }
}

def get_age_and_rural_urban_plan(age, lang):
    if age < 50:
        age_band_en = "Young & Working Adult Group"
        age_band_hi = "युवा और कामकाजी आयु वर्ग"
        ex_en = "30 minutes of brisk walking or jogging daily, 15 minutes of neck and shoulder stretches, and 10 minutes of deep breathing to lower stress and keep memory sharp."
        ex_hi = "रोज़ 30 मिनट तेज़ पैदल चलना या जॉगिंग, 15 मिनट गर्दन और कंधों की स्ट्रेचिंग, और 10 मिनट अनुलोम-विलोम प्राणायाम जिससे तनाव कम हो और दिमाग शांत व तेज़ रहे।"
    elif age < 65:
        age_band_en = "Mid-Life Active Care Group"
        age_band_hi = "मध्यम आयु स्वास्थ्य वर्ग"
        ex_en = "25 minutes of morning sunlight walking, hand-grip and light shoulder exercises, standing balance practice near a wall, and reading or solving puzzles in the evening."
        ex_hi = "सुबह की हल्की धूप में 25 मिनट पैदल चलना, हाथों की पकड़ और कंधों की हल्की कसरत, दीवार के सहारे संतुलन का अभ्यास, और शाम को अख़बार पढ़ना या पहेलियाँ सुलझाना।"
    else:
        age_band_en = "Senior Citizen Care Group"
        age_band_hi = "वरिष्ठ नागरिक देखभाल वर्ग"
        ex_en = "20 minutes of gentle morning walk in sunlight with supportive footwear, seated ankle, knee, and wrist rotations, finger-tapping exercises, and warm evening family conversations."
        ex_hi = "सुबह की हल्की धूप में 20 मिनट आराम से टहलना, कुर्सी पर बैठकर पैरों, घुटनों और कलाई को घुमाने की कसरत, उँगलियों का व्यायाम और शाम को परिवार के साथ बैठकर बातचीत।"

    if lang == 'en':
        dry_html = "<b>• Daily Dry Fruits & Seeds:</b> 4 to 5 soaked & peeled almonds + 2 walnut halves + 2 soaked black raisins + 1 teaspoon roasted flax or pumpkin seeds every morning."
        rural_html = "<b>• Rural & Traditional Home Diet:</b> Ragi (finger millet), Bajra or Jowar rotis, roasted Phool Makhana (foxnuts), drumstick leaves (Moringa), fresh green leafy vegetables, homemade curd or buttermilk (for natural Vitamin B12), roasted chana with jaggery, and warm turmeric milk at night."
        urban_html = "<b>• Urban & Modern Kitchen Diet:</b> Multigrain daliya or oats, paneer/tofu/lentils for protein, seasonal citrus fruits and amla, unsalted roasted nuts instead of packaged snacks, low-salt and low-sugar meals, and a yearly blood check for Vitamin B12, Vitamin D3, Thyroid, and Blood Sugar."
    else:
        dry_html = "<b>• रोज़ सुबह के सूखे मेवे (Dry Fruits):</b> रोज़ सुबह 4 से 5 भीगे और छिले हुए बादाम + 2 अखरोट की गिरी + 2 भीगी मुनक्का + 1 चम्मच भुनी अलसी या कद्दू के बीज ज़रूर दें।"
        rural_html = "<b>• ग्रामीण और देसी घर का आहार (Rural Diet):</b> रागी (नाचनी), बाजरा या ज्वार की रोटी, भुना हुआ फूल मखाना, सहजन (मोरिंगा) की फली व पत्तियाँ, हरी पत्तेदार सब्ज़ियाँ, घर का ताज़ा दही या छाछ, भुना चना-गुड़ और रात को चुटकी भर हल्दी वाला गुनगुना दूध।"
        urban_html = "<b>• शहरी और मॉडर्न किचन आहार (Urban Diet):</b> मल्टीग्रेन दलिया या ओट्स, पनीर, सोया व गाढ़ी दालें, आँवला और मौसमी फल, पैकेट वाले नमकीन-बिस्किट की जगह भुने मखाने व मेवे, कम नमक-चीनी का खाना, और साल में एक बार विटामिन B12, D3 व शुगर-बीपी की जाँच।"

    return {
        'band': age_band_hi if lang == 'hi' else age_band_en,
        'dry_fruits_html': dry_html,
        'rural_diet_html': rural_html,
        'urban_diet_html': urban_html,
        'exercise': ex_hi if lang == 'hi' else ex_en
    }

def generate_custom_analysis(answers_dict, age=68):
    def is_yes(ans):
        return ans and (str(ans).startswith('Yes') or str(ans).startswith('हाँ'))

    b1 = [q for q in SCREENING_DATA['bucket1']['questions'] if is_yes(answers_dict.get(q['id']))]
    b2 = [q for q in SCREENING_DATA['bucket2']['questions'] if is_yes(answers_dict.get(q['id']))]
    b3 = [q for q in SCREENING_DATA['bucket3']['questions'] if is_yes(answers_dict.get(q['id']))]
    r3 = is_yes(answers_dict.get('q_fever'))

    body_c = len(b1)
    mem_score = len(b2)
    mot_c = len(b3)
    tot = body_c + mem_score + mot_c

    mem_impaired = (mem_score >= 2)
    moderate_to_high_risk = (r3 or mem_score >= 2 or mot_c >= 2 or tot >= 3)

    all_c = b1 + b2 + b3
    names_en = ", ".join([it['label_en'].lower() for it in all_c[:4]])
    names_hi = ", ".join([it['label_hi'] for it in all_c[:4]])

    if r3:
        verdict_en = f"Prompt Doctor Visit Advised: Treatable Recent Fever or Infection Noted"
        verdict_hi = f"डॉक्टर की सलाह से तुरंत आराम मिलेगा: हाल के बुखार या इन्फेक्शन पर ध्यान दें"
        sub_en = f"Patient Age: {age} Years  •  Memory Score: {mem_score} / 8  •  Movement Score: {mot_c} / 4  •  Body Check: {body_c} / 3"
        sub_hi = f"मरीज़ की उम्र: {age} वर्ष  •  याददाश्त स्कोर: 8 में से {mem_score}  •  चलना-फिरना: 4 में से {mot_c}  •  शारीरिक संकेत: 3 में से {body_c}"
        voice_en = f"In this report for age {age} years, the memory score is {mem_score} out of 8, the movement score is {mot_c} out of 4, and the body check score is {body_c} out of 3. Because sudden confusion over the last 2 to 3 days was selected along with {names_en}, this points to a very treatable infection or low water and salt levels rather than a permanent brain condition. With a simple doctor visit and routine medicines today, patients recover their clarity and strength very quickly."
        voice_hi = f"{age} वर्ष की उम्र की इस रिपोर्ट में याददाश्त का स्कोर 8 में से {mem_score} है, चलने-फिरने का स्कोर 4 में से {mot_c} है, और शारीरिक जाँच का स्कोर 3 में से {body_c} है। रिपोर्ट में पिछले 2 से 3 दिनों की अचानक उलझन के साथ {names_hi} जैसे बदलाव चुने गए हैं। यह किसी बड़ी बीमारी का नहीं, बल्कि मामूली इन्फेक्शन या शरीर में पानी और विटामिन की कमी का संकेत है, जो डॉक्टर की साधारण दवाई से बहुत जल्दी और आसानी से ठीक हो जाता है।"
    elif moderate_to_high_risk:
        verdict_en = f"Supportive Doctor Checkup Recommended: Early Care Brings Great Improvement"
        verdict_hi = f"डॉक्टर से सामान्य जाँच कराएं: शुरुआती देखभाल से बहुत अच्छा सुधार संभव है"
        sub_en = f"Patient Age: {age} Years  •  Memory Score: {mem_score} / 8  •  Movement Score: {mot_c} / 4  •  Body Check: {body_c} / 3"
        sub_hi = f"मरीज़ की उम्र: {age} वर्ष  •  याददाश्त स्कोर: 8 में से {mem_score}  •  चलना-फिरना: 4 में से {mot_c}  •  शारीरिक संकेत: 3 में से {body_c}"
        voice_en = f"In this report for age {age} years, the memory score is {mem_score} out of 8, the movement score is {mot_c} out of 4, and the body check score is {body_c} out of 3. The main changes noted are {names_en}. Please feel reassured—many of these changes are linked to simple vitamin deficiencies or early nerve pathways that respond very well to timely medical care. Sharing the downloadable doctor report and visiting a nearby clinic using the PIN code map below will help keep their daily life active, comfortable, and independent."
        voice_hi = f"{age} वर्ष की उम्र की इस रिपोर्ट में याददाश्त का स्कोर 8 में से {mem_score} है, चलने-फिरने का स्कोर 4 में से {mot_c} है, और शारीरिक जाँच का स्कोर 3 में से {body_c} है। इसमें मुख्य रूप से {names_hi} जैसे बदलाव देखे गए हैं। इसमें घबराने की कोई बात नहीं है—सही समय पर विटामिन की जाँच और डॉक्टर के मार्गदर्शन से इन बदलावों में बहुत अच्छा सुधार आता है। आप नीचे पिन-कोड से नज़दीकी अस्पताल देख सकते हैं और डॉक्टर को दिखाने के लिए रिपोर्ट डाउनलोड कर सकते हैं।"
    elif tot == 1:
        verdict_en = f"Reassuring & Healthy Report: Only 1 Mild Change Noted for Age {age} Years"
        verdict_hi = f"राहत भरी और सामान्य रिपोर्ट: {age} वर्ष की उम्र में केवल 1 हल्का बदलाव दिखा है"
        sub_en = f"Patient Age: {age} Years  •  Memory Score: {mem_score} / 8 (Normal Range)  •  Movement Score: {mot_c} / 4"
        sub_hi = f"मरीज़ की उम्र: {age} वर्ष  •  याददाश्त स्कोर: 8 में से {mem_score} (बिल्कुल सामान्य)  •  चलना-फिरना: 4 में से {mot_c}"
        voice_en = f"In this report for age {age} years, the memory score is {mem_score} out of 8, which is safely within the normal range. Only one mild change was noted regarding {names_en}, and no hospital visit is needed right now. Following the daily soaked almonds, walnuts, balanced home meals, and 20-minute morning sunlight walk shown below will keep their mind and body strong."
        voice_hi = f"{age} वर्ष की उम्र की इस रिपोर्ट में याददाश्त का स्कोर 8 में से {mem_score} है, जो पूरी तरह सामान्य और सुरक्षित रेंज में है। केवल {names_hi} से जुड़ा एक हल्का बदलाव दिखा है, और अभी अस्पताल जाने की कोई आवश्यकता नहीं है। नीचे दिए गए चार्ट के अनुसार रोज़ सुबह भीगे बादाम, अखरोट, पौष्टिक घर का भोजन और 20 मिनट सुबह की धूप में टहलने से उनकी सेहत बहुत अच्छी बनी रहेगी।"
    else:
        verdict_en = f"Excellent Health Report: Strong Memory & Steady Movement for Age {age} Years"
        verdict_hi = f"उत्तम स्वास्थ्य रिपोर्ट: {age} वर्ष की उम्र में याददाश्त और सेहत बिल्कुल स्वस्थ है"
        sub_en = f"Patient Age: {age} Years  •  Memory Score: 0 / 8 (Healthy)  •  Movement Score: 0 / 4 (Healthy)"
        sub_hi = f"मरीज़ की उम्र: {age} वर्ष  •  याददाश्त स्कोर: 8 में से 0 (बिल्कुल स्वस्थ)  •  चलना-फिरना: 4 में से 0 (बिल्कुल स्वस्थ)"
        voice_en = f"In this report for age {age} years, the memory score is 0 out of 8 and the movement score is 0 out of 4, showing healthy memory, clear thinking, and steady balance. Continuing daily soaked almonds, walnuts, green leafy vegetables, and a 20-minute morning walk will keep their brain sharp and energetic for years to come."
        voice_hi = f"{age} वर्ष की उम्र की इस रिपोर्ट में याददाश्त का स्कोर 8 में से शून्य है और चलने-फिरने का स्कोर भी शून्य है, जो बताता है कि उनकी याददाश्त और संतुलन बिल्कुल स्वस्थ है। नीचे दिए गए चार्ट के अनुसार रोज़ भीगे बादाम, अखरोट, हरी सब्ज़ियाँ और सुबह की सैर जारी रखने से उनका दिमाग हमेशा चुस्त और तंदुरुस्त रहेगा।"

    return {
        'age': age,
        'ad8_score': mem_score,
        'ad8_impaired': mem_impaired,
        'counts': {'body': body_c, 'memory': mem_score, 'motor': mot_c, 'total': tot},
        'moderate_to_high_risk': moderate_to_high_risk,
        'verdict_en': verdict_en,
        'verdict_hi': verdict_hi,
        'sub_en': sub_en,
        'sub_hi': sub_hi,
        'checked_items': all_c,
        'voice_en': voice_en,
        'voice_hi': voice_hi
    }

def build_doctor_dossier_html(report, answers_dict, lang):
    c = report['counts']
    age = report['age']
    ad8 = report['ad8_score']
    ad8_imp = report['ad8_impaired']
    date_str = datetime.now().strftime('%d %B %Y • %I:%M %p')
    plan = get_age_and_rural_urban_plan(age, lang)
    
    status_color = '#2563EB' if report['moderate_to_high_risk'] else '#059669'
    
    if lang == 'en':
        doc_title = "Patient Brain Health & Memory Evaluation Report"
        doc_sub = f"Patient Age: <b>{age} Years</b> ({plan['band']})  |  Date: {date_str}"
        verdict_main = report['verdict_en']
        verdict_sub = f"Memory Score: <b>{ad8} out of 8</b> ({'2 or more indicates a doctor evaluation is advised' if ad8_imp else '0 to 1 is within the normal range'})  |  Movement Score: <b>{c['motor']} out of 4</b>  |  Body Check: <b>{c['body']} out of 3</b>"
        sec1_title = "1. Summary of Changes Noticed by Family (Plain-Language & Clinical Notes)"
        sec2_title = "2. Complete 15-Question Screening Checklist"
        sec3_title = f"3. Suggested Blood Tests & Daily Care Plan (Age {age} Years)"
        th_cols = ("Code", "Category", "Question / Observation", "Family Answer", "Doctor Note")
    else:
        doc_title = "मरीज़ की दिमागी सेहत और याददाश्त की डॉक्टरी रिपोर्ट (Clinical Report)"
        doc_sub = f"मरीज़ की उम्र: <b>{age} वर्ष</b> ({plan['band']})  |  तारीख: {date_str}"
        verdict_main = f"{report['verdict_hi']}<br><span style='font-size:1.05rem;font-weight:600;opacity:0.92;'>{report['verdict_en']}</span>"
        verdict_sub = f"याददाश्त स्कोर (AD8): <b>8 में से {ad8}</b>  |  चलना-फिरना: <b>4 में से {c['motor']}</b>  |  शारीरिक जाँच: <b>3 में से {c['body']}</b>"
        sec1_title = "1. परिवार द्वारा देखे गए मुख्य लक्षण और उनका अर्थ (Observed Changes)"
        sec2_title = "2. सभी 15 सवालों की पूरी तालिका (Complete 15-Item Checklist)"
        sec3_title = f"3. डॉक्टर के लिए सुझाई गई जाँच और {age} वर्ष के अनुसार आहार-व्यायाम"
        th_cols = ("कोड (Code)", "हिस्सा (Domain)", "सवाल (Screening Item)", "जवाब (Response)", "डॉक्टरी नोट (Clinical Note)")

    rows_html = ''
    all_qs = (
        SCREENING_DATA['bucket1']['questions'] +
        SCREENING_DATA['bucket2']['questions'] +
        SCREENING_DATA['bucket3']['questions']
    )
    for q in all_qs:
        raw_ans = str(answers_dict.get(q['id'], 'No, no change'))
        is_pos = raw_ans.startswith('Yes') or raw_ans.startswith('हाँ')
        pill_bg = '#DBEAFE' if is_pos else '#DCFCE7'
        pill_fg = '#1E40AF' if is_pos else '#166534'
        
        if lang == 'en':
            dom_txt = q['bucket_tag_en']
            item_txt = f"<b>{q['label_en']}</b><br><span style='color:#475569;font-size:0.84rem;'>{q['en']}</span>"
            ans_tag = 'YES, A CHANGE (+1)' if is_pos else 'NO CHANGE (0)'
            note_txt = q['doc_note'] if is_pos else 'Normal / No new change'
        else:
            dom_txt = f"<b>{q['bucket_tag_hi']}</b><br><span style='font-size:0.8rem;color:#64748B;'>{q['bucket_tag_en']}</span>"
            item_txt = f"<b>{q['label_hi']}</b><br><span style='color:#475569;font-size:0.84rem;'>{q['label_en']}</span>"
            ans_tag = 'हाँ, बदलाव है (+1)' if is_pos else 'कोई बदलाव नहीं (0)'
            note_txt = q['doc_note'] if is_pos else 'सामान्य (Normal baseline)'

        rows_html += f"""
        <tr>
            <td style='font-weight:800;color:#0F172A;'>{q['code']}</td>
            <td>{dom_txt}</td>
            <td>{item_txt}</td>
            <td><span style='background:{pill_bg};color:{pill_fg};padding:4px 10px;border-radius:999px;font-weight:800;font-size:0.78rem;'>{ans_tag}</span></td>
            <td style='font-size:0.85rem;color:#334155;'>{note_txt}</td>
        </tr>
        """

    flagged_cards_html = ''
    if report['checked_items']:
        for it in report['checked_items']:
            if lang == 'en':
                flagged_cards_html += f"""
                <div style='background:#F8FAFC;border:1.5px solid #BFDBFE;border-left:6px solid #2563EB;border-radius:12px;padding:14px 18px;margin-bottom:12px;'>
                    <div style='font-size:0.78rem;font-weight:800;color:#1E40AF;text-transform:uppercase;'>[{it['code']}] • {it['bucket_tag_en']}</div>
                    <div style='font-size:1.06rem;font-weight:800;color:#0F172A;margin:4px 0;'>{it['label_en']}</div>
                    <div style='font-size:0.9rem;color:#1E293B;margin-bottom:4px;'><b>Note for Doctor:</b> {it['doc_note']}</div>
                    <div style='font-size:0.9rem;color:#334155;'><b>What This Means:</b> {it['why_en']}</div>
                </div>
                """
            else:
                flagged_cards_html += f"""
                <div style='background:#F8FAFC;border:1.5px solid #BFDBFE;border-left:6px solid #2563EB;border-radius:12px;padding:14px 18px;margin-bottom:12px;'>
                    <div style='font-size:0.78rem;font-weight:800;color:#1E40AF;text-transform:uppercase;'>[{it['code']}] • {it['bucket_tag_hi']} ({it['bucket_tag_en']})</div>
                    <div style='font-size:1.06rem;font-weight:800;color:#0F172A;margin:4px 0;'>{it['label_hi']} ({it['label_en']})</div>
                    <div style='font-size:0.9rem;color:#1E293B;margin-bottom:4px;'><b>डॉक्टर के लिए नोट (Clinical Note):</b> {it['doc_note']}</div>
                    <div style='font-size:0.9rem;color:#334155;'><b>सरल विवरण:</b> {it['why_hi']}</div>
                </div>
                """
    else:
        if lang == 'en':
            flagged_cards_html = "<div style='background:#F0FDF4;border:1.5px solid #BBF7D0;border-radius:12px;padding:16px;color:#166534;font-weight:700;'>No concerning symptoms reported (0 out of 15). Memory, daily thinking, and movement look healthy.</div>"
        else:
            flagged_cards_html = "<div style='background:#F0FDF4;border:1.5px solid #BBF7D0;border-radius:12px;padding:16px;color:#166534;font-weight:700;'>कोई भी चिंताजनक लक्षण नहीं मिला (15 में से 0)। याददाश्त और चलना-फिरना बिल्कुल सामान्य है।</div>"

    lab_note = (
        "<b>• Helpful Blood Tests to Discuss with Doctor:</b> Complete Blood Count (Hemoglobin), Vitamin B12, Vitamin D3, Thyroid (TSH), Blood Sugar (HbA1c), Kidney/Liver & Electrolyte levels, and Urine routine check (if sudden confusion)."
        if lang == 'en' else
        "<b>• डॉक्टर की सलाह से कराई जाने वाली सामान्य खून की जाँचें:</b> हीमोग्लोबिन (CBC), विटामिन B12, विटामिन D3, थायराइड (TSH), शुगर (HbA1c), शरीर में नमक-पानी (Electrolytes) और पेशाब की जाँच (यदि अचानक उलझन हो)।"
    )

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{doc_title} — Age {age}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    body {{ font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', sans-serif; background: #0F172A; color: #0F172A; margin: 0; padding: 28px 16px; }}
    .dossier {{ max-width: 960px; margin: 0 auto; background: #FFFFFF; border-radius: 22px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.45); }}
    .header {{ background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%); color: #FFFFFF; padding: 30px 36px; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; border-bottom: 5px solid {status_color}; }}
    .tag {{ display: inline-block; background: rgba(255,255,255,0.16); padding: 5px 14px; border-radius: 999px; font-size: 0.78rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 10px; }}
    .title {{ font-size: 1.75rem; font-weight: 800; margin: 0 0 6px 0; }}
    .sub {{ font-size: 0.95rem; opacity: 0.9; margin: 0; }}
    .print-btn {{ background: #FFFFFF; color: #0F172A; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 800; cursor: pointer; font-size: 0.9rem; }}
    .content {{ padding: 30px 36px; }}
    .verdict-box {{ background: {status_color}; color: #FFFFFF; border-radius: 16px; padding: 20px 24px; margin-bottom: 24px; }}
    .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 26px; }}
    .metric-card {{ background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 14px; padding: 16px; text-align: center; }}
    .metric-val {{ font-size: 1.75rem; font-weight: 800; color: #0F172A; }}
    .metric-lbl {{ font-size: 0.82rem; font-weight: 700; color: #475569; margin-top: 4px; }}
    h2 {{ font-size: 1.22rem; font-weight: 800; color: #0F172A; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; margin-top: 28px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 0.9rem; }}
    th {{ background: #F1F5F9; text-align: left; padding: 11px 12px; font-weight: 800; color: #1E293B; border-bottom: 2px solid #CBD5E1; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #E2E8F0; vertical-align: top; }}
    .footer {{ background: #F8FAFC; padding: 18px 36px; border-top: 1.5px solid #E2E8F0; font-size: 0.82rem; color: #475569; }}
    @media print {{ body {{ background: #FFFFFF; padding: 0; }} .dossier {{ box-shadow: none; }} .print-btn {{ display: none; }} }}
</style>
</head>
<body>
<div class="dossier">
    <div class="header">
        <div>
            <div class="tag">{'ELDER CARE CLINICAL REPORT' if lang=='en' else 'बुज़ुर्ग स्वास्थ्य एवं याददाश्त रिपोर्ट'}</div>
            <h1 class="title">{doc_title}</h1>
            <p class="sub">{doc_sub}</p>
        </div>
        <button class="print-btn" onclick="window.print()">🖨️ {'Print / Save as PDF' if lang=='en' else 'प्रिंट करें / PDF सेव करें'}</button>
    </div>
    <div class="content">
        <div class="verdict-box">
            <div style="font-size:1.38rem;font-weight:800;margin:2px 0 8px 0;">{verdict_main}</div>
            <div style="font-size:0.95rem;opacity:0.95;">{verdict_sub}</div>
        </div>

        <div class="grid-4">
            <div class="metric-card">
                <div class="metric-val">{age} {'Years' if lang=='en' else 'वर्ष'}</div>
                <div class="metric-lbl">{'Patient Age' if lang=='en' else 'मरीज़ की उम्र'}</div>
            </div>
            <div class="metric-card" style="border-color:{'#2563EB' if ad8_imp else '#16A34A'};border-width:2px;">
                <div class="metric-val" style="color:{'#1D4ED8' if ad8_imp else '#15803D'};">{ad8} / 8</div>
                <div class="metric-lbl">{'Memory Score (Out of 8)' if lang=='en' else 'याददाश्त स्कोर (8 में से)'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{c['motor']} / 4</div>
                <div class="metric-lbl">{'Movement Score (Out of 4)' if lang=='en' else 'चलना-फिरना (4 में से)'}</div>
            </div>
            <div class="metric-card">
                <div class="metric-val">{c['body']} / 3</div>
                <div class="metric-lbl">{'Body & Vitamin Check (Out of 3)' if lang=='en' else 'शरीर व विटामिन (3 में से)'}</div>
            </div>
        </div>

        <h2>{sec1_title}</h2>
        {flagged_cards_html}

        <h2>{sec2_title}</h2>
        <table>
            <thead>
                <tr>
                    <th style="width:65px;">{th_cols[0]}</th>
                    <th style="width:155px;">{th_cols[1]}</th>
                    <th>{th_cols[2]}</th>
                    <th style="width:160px;">{th_cols[3]}</th>
                    <th style="width:210px;">{th_cols[4]}</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <h2>{sec3_title}</h2>
        <div style="background:#F8FAFC;border:1.5px solid #CBD5E1;border-radius:14px;padding:18px;font-size:0.92rem;line-height:1.68;">
            <p style="margin:0 0 8px 0;">{lab_note}</p>
            <p style="margin:0 0 8px 0;">{plan['dry_fruits_html']}</p>
            <p style="margin:0 0 8px 0;">{plan['rural_diet_html']}</p>
            <p style="margin:0 0 8px 0;">{plan['urban_diet_html']}</p>
            <p style="margin:0;"><b>• {'Daily Exercise (' + str(age) + ' Years)' if lang=='en' else 'दैनिक व्यायाम (' + str(age) + ' वर्ष)'}:</b> {plan['exercise']}</p>
        </div>
    </div>
    <div class="footer">
        {'<b>Medical Note:</b> This report summarizes family observations (including the validated 8-item informant memory interview) to help your doctor during consultation.' if lang=='en' else '<b>मेडिकल नोट:</b> यह रिपोर्ट परिवार द्वारा देखे गए लक्षणों का सार है ताकि डॉक्टर को जाँच और इलाज में आसानी हो।'}
    </div>
</div>
</body>
</html>"""
    return html

if 'lang' not in st.session_state: st.session_state.lang = None
if 'screening_step' not in st.session_state: st.session_state.screening_step = 'language_selection'
if 'answers' not in st.session_state: st.session_state.answers = {}
if 'patient_age' not in st.session_state: st.session_state.patient_age = 68
if 'pin_input' not in st.session_state: st.session_state.pin_input = '400071'
if 'nav_count' not in st.session_state: st.session_state.nav_count = 0

def change_step(new_step, set_lang=None):
    if set_lang:
        st.session_state.lang = set_lang
    st.session_state.screening_step = new_step
    st.session_state.nav_count = st.session_state.get('nav_count', 0) + 1

force_scroll_to_top(st.session_state.screening_step, st.session_state.nav_count)

def render_step_progress(current_step, lang):
    steps = [
        ('bucket1', '1. शरीर और विटामिन (3 सवाल)' if lang == 'hi' else '1. Body & Vitamins (3 Items)'),
        ('bucket2', '2. याददाश्त की जाँच (8 सवाल)' if lang == 'hi' else '2. Memory Check (8 Items)'),
        ('bucket3', '3. चलना-फिरना (4 सवाल)' if lang == 'hi' else '3. Movement Check (4 Items)')
    ]
    curr_idx = ['bucket1', 'bucket2', 'bucket3'].index(current_step)
    pills = ''.join([f"<div class='step-pill {'active' if i==curr_idx else ('done' if i<curr_idx else '')}'>{'✓ ' if i<curr_idx else ''}{lbl}</div>" for i, (_, lbl) in enumerate(steps)])
    st.markdown(f"<div class='step-bar'>{pills}</div>", unsafe_allow_html=True)

_frag = getattr(st, 'fragment', lambda f: f)

@_frag
def render_age_slider_fragment(lang):
    if 'age_slider_val' not in st.session_state:
        st.session_state.age_slider_val = int(st.session_state.patient_age)
    val = st.slider(
        'उम्र चुनें (25 से 100 वर्ष)' if lang == 'hi' else 'Select Patient Age (25 to 100 Years)',
        min_value=25, max_value=100, key='age_slider_val', step=1
    )
    st.session_state.patient_age = val

@_frag
def render_questions_only(step_id, lang):
    data = SCREENING_DATA[step_id]
    opts = data['options_' + lang]
    
    for q in data['questions']:
        q_id = q['id']
        rad_key = f"rad_{q_id}_{lang}"
        if rad_key not in st.session_state:
            saved_ans = st.session_state.answers.get(q_id)
            st.session_state[rad_key] = saved_ans if saved_ans in opts else opts[1]

        st.markdown(f"<div class='q-card'><div class='q-title'>{q[lang]}</div></div>", unsafe_allow_html=True)
        ab = load_audio_bytes(f"audio/{q_id}_{lang}.mp3")
        if ab:
            st.audio(ab, format='audio/mp3')

        selected_val = st.radio(
            label=q[lang],
            options=opts,
            key=rad_key,
            horizontal=True,
            label_visibility='collapsed'
        )
        st.session_state.answers[q_id] = selected_val

# ==================== PAGE 1: EQUAL-HEIGHT LANGUAGE SELECTION ====================
if st.session_state.screening_step == 'language_selection':
    st.markdown(f"<div style='text-align:center;margin-bottom:2rem;'><h1 style='color:#0F172A;font-size:2.4rem;font-weight:800;margin-bottom:6px;'>{SCREENING_DATA['intro']['hi']['welcome']}</h1><h3 style='color:#2563EB;font-weight:700;margin-top:0;'>{SCREENING_DATA['intro']['en']['welcome']}</h3></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap='large')
    with c1:
        st.markdown(f"<div class='lang-box'><div class='lang-box-title'>{SCREENING_DATA['intro']['hi']['title_box']}</div><p class='lang-box-desc'>{SCREENING_DATA['intro']['hi']['desc']}</p></div>", unsafe_allow_html=True)
        b_hi = load_audio_bytes(SCREENING_DATA['intro']['hi']['audio_file'])
        if b_hi: st.audio(b_hi, format='audio/mp3')
        if st.button(SCREENING_DATA['intro']['hi']['btn_text'], use_container_width=True, type='primary', key='btn_lang_hi'):
            change_step('instructions', 'hi')
            st.rerun()
    with c2:
        st.markdown(f"<div class='lang-box'><div class='lang-box-title'>{SCREENING_DATA['intro']['en']['title_box']}</div><p class='lang-box-desc'>{SCREENING_DATA['intro']['en']['desc']}</p></div>", unsafe_allow_html=True)
        b_en = load_audio_bytes(SCREENING_DATA['intro']['en']['audio_file'])
        if b_en: st.audio(b_en, format='audio/mp3')
        if st.button(SCREENING_DATA['intro']['en']['btn_text'], use_container_width=True, type='primary', key='btn_lang_en'):
            change_step('instructions', 'en')
            st.rerun()

# ==================== PAGE 2: CLEAN AGE CARD + CALM AGE VOICE + ZERO-LAG SLIDER ====================
elif st.session_state.screening_step == 'instructions':
    lang = st.session_state.lang
    data = SCREENING_DATA['instructions'][lang]
    
    st.markdown(f"<div class='page-header-title'>{data['title']}</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='inst-card'>
        <div class='inst-card-title'>👤 {data['age_title']}</div>
        <p class='inst-card-sub'>{data['age_sub']}</p>
    </div>
    """, unsafe_allow_html=True)

    age_audio_bytes = (
        load_audio_bytes(data['age_audio'])
        or get_Dynamic_Result_Voice(data['age_voice_script'], lang, tag='calm_age_v140')
    )
    if age_audio_bytes:
        st.audio(age_audio_bytes, format='audio/mp3')

    render_age_slider_fragment(lang)

    st.markdown(f"""
    <div class='rule-card'>
        <div class='rule-card-title'>📌 {data['rule_title']}</div>
        <div class='rule-card-body'>{data['rule']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    b_inst = load_audio_bytes(data['audio_file'])
    if b_inst:
        st.audio(b_inst, format='audio/mp3')

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button(data['back_text'], use_container_width=True, key='inst_back'):
            change_step('language_selection')
            st.rerun()
    with c2:
        if st.button(data['btn_text'], use_container_width=True, type='primary', key='inst_next'):
            change_step('bucket1')
            st.rerun()

# ==================== PAGE 3: QUESTION BUCKETS (STARTS AT QUESTION 1 EVERY TIME) ====================
elif st.session_state.screening_step in ['bucket1', 'bucket2', 'bucket3']:
    step_id, lang = st.session_state.screening_step, st.session_state.lang
    data = SCREENING_DATA[step_id]
    render_step_progress(step_id, lang)
    st.markdown(f"<h1 style='text-align:center;color:#0F172A;font-weight:800;font-size:1.95rem;'>{data['title_' + lang]}</h1><p style='text-align:center;color:#475569;font-size:1.04rem;'>{data['desc_' + lang]}</p>", unsafe_allow_html=True)
    b_sec = load_audio_bytes(data['audio_' + lang])
    if b_sec:
        st.audio(b_sec, format='audio/mp3')
    
    render_questions_only(step_id, lang)

    st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button(data['back_' + lang], use_container_width=True, key=f"nav_back_{step_id}"):
            change_step({'bucket1': 'instructions', 'bucket2': 'bucket1', 'bucket3': 'bucket2'}[step_id])
            st.rerun()
    with c2:
        if st.button(data['btn_' + lang], use_container_width=True, type='primary', key=f"nav_next_{step_id}"):
            change_step({'bucket1': 'bucket2', 'bucket2': 'bucket3', 'bucket3': 'results'}[step_id])
            st.rerun()

# ==================== PAGE 4: ATOMIC ALL-AT-ONCE REPORT RENDERING ====================
elif st.session_state.screening_step == 'results':
    lang = st.session_state.lang
    age = int(st.session_state.patient_age)

    # Pre-compute EVERYTHING (Analysis + Voice Audio + Dossier HTML + Initial PIN Data) BEFORE rendering a single element
    # so the entire report, banner, audio player, scoreboard, and recommendations appear all together at the exact same moment!
    with st.spinner('पूरी स्वास्थ्य रिपोर्ट और ऑडियो तैयार किया जा रहा है...' if lang == 'hi' else 'Preparing your complete health report, audio guide, and recommendations...'):
        report = generate_custom_analysis(st.session_state.answers, age)
        counts = report['counts']
        ad8_score = report['ad8_score']
        ad8_impaired = report['ad8_impaired']
        plan = get_age_and_rural_urban_plan(age, lang)
        voice_bytes = get_Dynamic_Result_Voice(report['voice_hi'] if lang == 'hi' else report['voice_en'], lang, tag='res_calm_v140')
        dossier_html = build_doctor_dossier_html(report, st.session_state.answers, lang)
        initial_pin_data = None
        if report['moderate_to_high_risk'] and len(st.session_state.pin_input.strip()) == 6 and st.session_state.pin_input.strip().isdigit():
            initial_pin_data = lookup_india_pincode_and_clinics(st.session_state.pin_input)

    # Single atomic container so all UI elements paint onto the screen simultaneously
    main_report_box = st.container()
    with main_report_box:
        c_top1, c_top2 = st.columns(2)
        with c_top1:
            if st.button('⬅ Back to Questions' if lang == 'en' else '⬅ सवालों पर वापस जाएं', use_container_width=True, key='res_back'):
                change_step('bucket3')
                st.rerun()
        with c_top2:
            if st.button('🆕 Start New Check' if lang == 'en' else '🆕 नई जाँच शुरू करें', use_container_width=True, type='primary', key='res_new'):
                for k in list(st.session_state.keys()):
                    if str(k).startswith('rad_'):
                        del st.session_state[k]
                st.session_state.answers = {}
                change_step('language_selection')
                st.rerun()

        banner_cls = 'care-doc-banner' if report['moderate_to_high_risk'] else 'healthy-doc-banner'
        verdict_txt = report['verdict_hi'] if lang == 'hi' else report['verdict_en']
        sub_txt = report['sub_hi'] if lang == 'hi' else report['sub_en']
        
        st.markdown(f"""
        <div class='{banner_cls}'>
            <div style='font-size:0.9rem;font-weight:800;text-transform:uppercase;letter-spacing:0.06em;opacity:0.94;margin-bottom:6px;'>
                {'🩺 स्वास्थ्य मार्गदर्शन और डॉक्टरी सलाह' if report['moderate_to_high_risk'] and lang=='hi' else ('🩺 HEALTH GUIDANCE & DOCTOR CONSULTATION NOTE' if report['moderate_to_high_risk'] else ('✅ समग्र स्वास्थ्य परिणाम' if lang=='hi' else '✅ OVERALL HEALTH SCREENING RESULT'))}
            </div>
            <div style='font-size:1.72rem;font-weight:800;line-height:1.32;margin-bottom:8px;'>{verdict_txt}</div>
            <div style='font-size:1.05rem;font-weight:600;opacity:0.96;'>{sub_txt}</div>
        </div>
        """, unsafe_allow_html=True)

        if voice_bytes:
            st.audio(voice_bytes, format='audio/mp3')

        ad8_badge_bg = '#DBEAFE' if ad8_impaired else '#DCFCE7'
        ad8_badge_col = '#1E40AF' if ad8_impaired else '#166534'
        ad8_status_txt = (
            ('2 या अधिक अंक: डॉक्टर से सलाह लें' if ad8_impaired else '0 से 1 अंक: सामान्य याददाश्त')
            if lang == 'hi' else
            ('2 or More Points: Doctor Check Advised' if ad8_impaired else '0 to 1 Point: Normal Memory Range')
        )

        st.markdown(f"""
        <div class='score-panel'>
            <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;'>
                <div>
                    <span style='font-size:1.22rem;font-weight:800;color:#0F172A;'>
                        {'📊 स्वास्थ्य और याददाश्त स्कोर कार्ड (Scoreboard)' if lang == 'hi' else '📊 Complete Health & Memory Scoreboard'}
                    </span>
                    <div style='font-size:0.9rem;color:#475569;margin-top:2px;'>
                        {'0 से 1 अंक = सामान्य | 2 या अधिक अंक = डॉक्टर से जाँच कराएं' if lang == 'hi' else 'Memory Score Guide: 0 to 1 Point = Normal | 2 or More Points = Doctor Evaluation Recommended'}
                    </div>
                </div>
                <span style='background:{ad8_badge_bg};color:{ad8_badge_col};padding:6px 16px;border-radius:999px;font-weight:800;font-size:0.9rem;'>
                    {ad8_status_txt}
                </span>
            </div>
            <div class='score-grid'>
                <div class='score-metric'>
                    <div class='score-num'>{age} {'वर्ष' if lang=='hi' else 'Yrs'}</div>
                    <div class='score-lbl'>{'मरीज़ की उम्र' if lang == 'hi' else 'Patient Age'}</div>
                    <span class='score-unit' style='background:#EFF6FF;color:#1D4ED8;'>{plan['band']}</span>
                </div>
                <div class='score-metric' style='border-color:{"#2563EB" if ad8_impaired else "#10B981"};border-width:2px;'>
                    <div class='score-num' style='color:{"#1D4ED8" if ad8_impaired else "#047857"};'>{ad8_score} / 8</div>
                    <div class='score-lbl'>{'याददाश्त स्कोर' if lang == 'hi' else 'Memory Score'}</div>
                    <span class='score-unit' style='background:{ad8_badge_bg};color:{ad8_badge_col};'>{'8 सवालों में से अंक' if lang=='hi' else 'Points out of 8'}</span>
                </div>
                <div class='score-metric'>
                    <div class='score-num' style='color:{"#1D4ED8" if counts["motor"]>=2 else "#0F172A"};'>{counts['motor']} / 4</div>
                    <div class='score-lbl'>{'चलना-फिरना और संतुलन' if lang == 'hi' else 'Movement & Balance'}</div>
                    <span class='score-unit' style='background:#F1F5F9;color:#334155;'>{'4 सवालों में से अंक' if lang == 'hi' else 'Points out of 4'}</span>
                </div>
                <div class='score-metric'>
                    <div class='score-num' style='color:{"#D97706" if counts["body"]>=1 else "#0F172A"};'>{counts['body']} / 3</div>
                    <div class='score-lbl'>{'शरीर और विटामिन' if lang == 'hi' else 'Body & Vitamins'}</div>
                    <span class='score-unit' style='background:#F1F5F9;color:#334155;'>{'3 सवालों में से अंक' if lang == 'hi' else 'Points out of 3'}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        download_btn_label = (
            '🩺 डॉक्टर को दिखाने के लिए पूरी मेडिकल रिपोर्ट डाउनलोड करें (Download Doctor Report)'
            if lang == 'hi' else
            '🩺 Download Official Doctor Consultation Report (Printable File)'
        )

        if report['moderate_to_high_risk']:
            col_left, col_right = st.columns([1.12, 1], gap='large')

            with col_left:
                st.subheader('🩺 ' + ('लक्षणों की आसान समझ और सलाह' if lang == 'hi' else 'Clear Explanation of Changes Noticed'))
                
                for item in report['checked_items']:
                    t_lbl = item['label_hi'] if lang == 'hi' else item['label_en']
                    w_txt = item['why_hi'] if lang == 'hi' else item['why_en']
                    b_tag = item['bucket_tag_hi'] if lang == 'hi' else item['bucket_tag_en']
                    st.markdown(f"""
                    <div class='symptom-card'>
                        <div style='font-size:0.78rem;font-weight:800;color:#1D4ED8;text-transform:uppercase;margin-bottom:4px;'>{b_tag}</div>
                        <div style='font-size:1.1rem;font-weight:800;color:#0F172A;margin-bottom:6px;'>✔️ {t_lbl}</div>
                        <div style='font-size:0.98rem;color:#334155;line-height:1.62;'>{w_txt}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.download_button(
                    download_btn_label,
                    data=dossier_html,
                    file_name=f'Doctor_Medical_Report_Age_{age}_{lang.upper()}.html',
                    mime='text/html',
                    type='primary',
                    use_container_width=True
                )

            with col_right:
                st.subheader('📍 ' + ('पिन-कोड से नज़दीकी अस्पताल, पता और फोन नंबर' if lang == 'hi' else 'PIN-Code Map & Nearest Hospital Directory'))
                st.caption('भारत के किसी भी 6-अंकों के पिन-कोड को डालें और तुरंत नज़दीकी अस्पताल का मैप, पता और फोन नंबर देखें:' if lang == 'hi' else 'Enter any 6-digit India PIN code to view the live hospital map, address, PIN code, and phone numbers:')
                
                pin_val = st.text_input(
                    'अपना 6-अंकों का पिन कोड लिखें (जैसे 400071, 400061, 110001):' if lang == 'hi' else 'Enter 6-Digit India PIN Code (e.g., 400071, 400061, 110001):',
                    value=st.session_state.pin_input,
                    max_chars=6
                )
                if pin_val and pin_val != st.session_state.pin_input:
                    st.session_state.pin_input = pin_val
                    initial_pin_data = lookup_india_pincode_and_clinics(pin_val)

                if initial_pin_data and 'error' not in initial_pin_data:
                    pin_data = initial_pin_data
                    ardsi_name, ardsi_phone, ardsi_addr = pin_data['ardsi']
                    st.success(f"📮 **PIN {pin_data['pin']}:** {pin_data['locality']}, {pin_data['district']}, {pin_data['state']}")
                    
                    map_search_q = urllib.parse.quote(f"Hospitals near {pin_data['locality']}, {pin_data['district']}, {pin_data['state']} {pin_data['pin']}, India")
                    st.markdown(f"""
                    <div style='border:2px solid #93C5FD;border-radius:16px;overflow:hidden;margin-bottom:12px;box-shadow:0 4px 12px rgba(37,99,235,0.1);'>
                        <iframe width="100%" height="260" frameborder="0" style="border:0"
                            src="https://maps.google.com/maps?q={map_search_q}&t=&z=13&ie=UTF8&iwloc=&output=embed" allowfullscreen>
                        </iframe>
                    </div>
                    """, unsafe_allow_html=True)

                    dist_q = urllib.parse.quote(f"Government Hospital Neurologist near {pin_data['locality']} {pin_data['district']} {pin_data['pin']}")
                    st.markdown(f"<a href='https://www.google.com/maps/search/?api=1&query={dist_q}' target='_blank' style='display:block;text-align:center;background:#1D4ED8;color:white;padding:12px 16px;border-radius:12px;text-decoration:none;font-weight:800;margin:10px 0;'>🗺️ {'गूगल मैप्स ऐप में सभी नज़दीकी अस्पताल खोलें ➔' if lang=='hi' else 'Open Full Hospital Directions in Google Maps ➔'}</a>", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class='hospital-card' style='background:linear-gradient(135deg,#EFF6FF 0%,#FFFFFF 100%);'>
                        <div style='font-weight:800;color:#1E3A8A;font-size:1.04rem;'>🤝 {ardsi_name}</div>
                        <div style='font-size:0.92rem;color:#0F172A;margin-top:5px;'>📞 <b>{'फोन नंबर' if lang=='hi' else 'Phone'}:</b> <a href='tel:{ardsi_phone}' style='color:#2563EB;font-weight:700;'>{ardsi_phone}</a>  |  <b>Govt Helpline:</b> <a href='tel:14416'>14416</a> / <a href='tel:14567'>14567</a></div>
                        <div style='font-size:0.9rem;color:#334155;margin-top:3px;'>📮 <b>{'पता और पिन कोड' if lang=='hi' else 'Address & PIN'}:</b> {ardsi_addr}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    for c in pin_data['clinics']:
                        sec_lbl = c['sector_hi'] if lang == 'hi' else c['sector']
                        st.markdown(f"""
                        <div class='hospital-card'>
                            <div style='display:flex;justify-content:space-between;align-items:flex-start;gap:8px;'>
                                <div>
                                    <div style='font-weight:800;font-size:1.05rem;color:#0F172A;'>🏥 {c['name']}</div>
                                    <span style='display:inline-block;background:#DBEAFE;color:#1E40AF;font-size:0.76rem;font-weight:800;padding:3px 10px;border-radius:999px;margin:4px 0;'>{sec_lbl}</span>
                                </div>
                                <a href='{c['maps_url']}' target='_blank' style='background:#1E40AF;color:white;padding:7px 14px;border-radius:10px;text-decoration:none;font-size:0.84rem;font-weight:800;white-space:nowrap;'>📍 {'मैप रास्ता' if lang=='hi' else 'Directions'} ➔</a>
                            </div>
                            <div style='font-size:0.92rem;color:#0F172A;margin-top:6px;'>📞 <b>{'फोन / हेल्पलाइन' if lang=='hi' else 'Phone / Helpline'}:</b> {c['phone']}</div>
                            <div style='font-size:0.9rem;color:#334155;margin-top:3px;'>📮 <b>{'पता और पिन कोड' if lang=='hi' else 'Address & PIN Code'}:</b> {c['address']} (PIN: <b>{c['pincode']}</b>)</div>
                        </div>
                        """, unsafe_allow_html=True)

        else:
            if report['checked_items']:
                st.subheader('ℹ️ ' + ('आपने जो 1 हल्का बदलाव चुना है उसका आसान मतलब' if lang == 'hi' else 'Simple Explanation of the 1 Mild Change You Selected'))
                for item in report['checked_items']:
                    t_lbl = item['label_hi'] if lang == 'hi' else item['label_en']
                    w_txt = item['why_hi'] if lang == 'hi' else item['why_en']
                    st.markdown(f"""
                    <div class='mild-symptom-card'>
                        <div style='font-size:1.08rem;font-weight:800;color:#92400E;margin-bottom:4px;'>✔️ {t_lbl}</div>
                        <div style='font-size:0.98rem;color:#78350F;line-height:1.6;'>{w_txt}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class='wellness-sheet'>
                <h2 style='color:#0F172A;font-weight:800;margin-top:0;margin-bottom:6px;'>
                    {'🥗 ग्रामीण और शहरी दिमागी पोषण एवं दैनिक व्यायाम चार्ट' if lang == 'hi' else '🥗 Personalized Rural & Urban Brain Nutrition & Exercise Guide'}
                </h2>
                <p style='color:#334155;font-size:1.02rem;margin-bottom:4px;font-weight:500;'>
                    {'यह चार्ट मरीज़ की उम्र (' + str(age) + ' वर्ष — ' + plan['band'] + ') और सामान्य स्वास्थ्य रिपोर्ट के अनुसार तैयार किया गया है:' if lang == 'hi' else f"Tailored specifically for Patient Age ({age} Years — {plan['band']}) and Normal Screening Report:"}
                </p>
            </div>
            """, unsafe_allow_html=True)

            w1, w2 = st.columns(2, gap='medium')
            with w1:
                st.markdown(f"""
                <div class='wellness-col-card'>
                    <h4 style='color:#047857;font-weight:800;margin-top:0;font-size:1.18rem;'>🌾 {'ग्रामीण खान-पान और सूखे मेवे (Rural Diet & Dry Fruits)' if lang=='hi' else 'Rural Home Diet & Daily Dry Fruits'}</h4>
                    <div style='line-height:1.7;color:#1E293B;font-size:0.98rem;margin-bottom:12px;'>{plan['dry_fruits_html']}</div>
                    <div style='line-height:1.7;color:#1E293B;font-size:0.98rem;'>{plan['rural_diet_html']}</div>
                </div>
                """, unsafe_allow_html=True)
            with w2:
                st.markdown(f"""
                <div class='wellness-col-card' style='border-top-color:#2563EB;'>
                    <h4 style='color:#1D4ED8;font-weight:800;margin-top:0;font-size:1.18rem;'>🏙️ {'शहरी आहार और रोज़ की कसरत (Urban Diet & Exercise)' if lang=='hi' else 'Urban Kitchen Diet & Daily Exercise'}</h4>
                    <div style='line-height:1.7;color:#1E293B;font-size:0.98rem;margin-bottom:12px;'>{plan['urban_diet_html']}</div>
                    <div style='line-height:1.7;color:#1E293B;font-size:0.98rem;'>🏃 <b>{'दैनिक व्यायाम (' + str(age) + ' वर्ष)' if lang=='hi' else f'Daily Exercise ({age} Years)'}:</b> {plan['exercise']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)
            st.download_button(
                download_btn_label,
                data=dossier_html,
                file_name=f'Doctor_Medical_Report_Age_{age}_{lang.upper()}.html',
                mime='text/html',
                type='primary',
                use_container_width=True
            )