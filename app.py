# app.py - with lightweight session handling for follow-up profile & suggestions
from flask import Flask, render_template, request, jsonify, g
import sqlite3
import re
from datetime import datetime
import os
import uuid

DB_PATH = 'data/salon.db'
app = Flask(__name__, static_folder='static', template_folder='templates')

# simple in-memory sessions (keeps state while server runs)
SESSIONS = {}

# --- INDEX ROUTE ---
@app.route('/')
def index():
    services = [
        {'name': 'Haircut', 'desc': 'Precision cuts', 'price': '₹799'},
        {'name': 'Hair Color', 'desc': 'Balayage & full color', 'price': '₹2499'},
        {'name': 'Facial', 'desc': 'Luxury facials', 'price': '₹1299'},
        {'name': 'Nails', 'desc': 'Manicure & pedicure', 'price': '₹699'},
    ]
    locations = ['Mumbai', 'Hyderabad', 'Kolkata', 'Pune', 'Indore']
    reviews = [
        {'name': 'Ritu Mishra', 'text': 'Absolutely LOVE the services here.'},
        {'name': 'Aanchal Wadhwani', 'text': 'Fantastic experience, highly recommended!'}
    ]
    return render_template('index.html', services=services, locations=locations, reviews=reviews)

# ------------------ DB helpers ------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        os.makedirs(os.path.dirname(DB_PATH) or '.', exist_ok=True)
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        gender TEXT,
        age INTEGER,
        service TEXT,
        date TEXT,
        time TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'tentative'
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        gender TEXT,
        age INTEGER,
        skin_tone TEXT,
        face_shape TEXT,
        created_at TEXT
    )
    ''')
    db.commit()

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, '_database', None)
    if db:
        db.close()

# ------------------ rules & helpers (same as before) ------------------
PRODUCT_RULES = {
    'male': {
        'dry': ['Hydrating shampoo', 'Leave-in conditioner'],
        'oily': ['Clarifying shampoo', 'Lightweight mattifying cream'],
        'normal': ['Balanced shampoo', 'Light styling cream']
    },
    'female': {
        'dry': ['Moisture-rich shampoo', 'Hair oil'],
        'oily': ['Purifying shampoo', 'Scalp scrub'],
        'normal': ['Sulfate-free shampoo', 'heat protectant']
    }
}

def generate_suggestion(face_shape, skin_tone, age, gender, service_intent=None):
    face = (face_shape or '').lower()
    skin = (skin_tone or '').lower()
    age = int(age) if age else None
    gender = (gender or '').lower()

    if face in ['oval','oval-shaped']:
        haircut = "Layered bob or long waves — oval faces suit most styles."
    elif face in ['round']:
        haircut = "Long layers and side parting to add angles and length."
    elif face in ['square']:
        haircut = "Soft waves or textured fringe to soften the jawline."
    elif face in ['heart']:
        haircut = "Chin-length bobs or side swept bangs."
    elif face in ['long','oblong']:
        haircut = "Bangs or chin-length layers to shorten the face."
    else:
        haircut = "Classic layered cuts or textured ends usually work well."

    if 'dark' in skin or 'deep' in skin:
        color = "Warm browns, caramel highlights, or rich chestnut."
    elif 'olive' in skin:
        color = "Warm honey browns or soft balayage pieces."
    elif 'fair' in skin:
        color = "Ash browns, cool blondes, or soft pastels."
    else:
        color = "Neutral browns and honey tones are versatile."

    age_note = ""
    if age:
        if age < 25:
            age_note = "Younger clients can try bolder colors and trendier cuts."
        elif age < 45:
            age_note = "Mid-age clients benefit from low-maintenance layers and dimension."
        else:
            age_note = "Consider softer, face-framing layers and nourishing treatments."

    gender_note = ""
    if gender in ('male','m'):
        gender_note = "For men: short textured crops, fades, or classic taper cuts are popular."
    elif gender in ('female','f'):
        gender_note = "For women: long layers, soft waves, or textured lobs are flattering."

    hair_texture = 'normal'
    if 'dry' in skin or 'dry' in (skin_tone or ''):
        hair_texture = 'dry'
    elif 'oily' in (skin_tone or ''):
        hair_texture = 'oily'

    products = PRODUCT_RULES.get('male' if gender.startswith('m') else 'female', PRODUCT_RULES['female']).get(hair_texture, [])
    products_text = ', '.join(products) if products else 'Sulfate-free shampoo and a heat protectant.'

    service_hint = f"For {service_intent}, consider scheduling a consultation for exact pricing and timing." if service_intent else ""

    suggestion_text = f"{haircut} {color} {age_note} {gender_note} {service_hint} Product suggestions: {products_text}"
    return suggestion_text

# date/time normalization helpers (same as previous version)
def normalize_date_str(s):
    s = s.strip()
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.date().isoformat()
    except:
        pass
    try:
        dt = datetime.strptime(s, "%d-%m-%Y")
        return dt.date().isoformat()
    except:
        pass
    try:
        dt = datetime.strptime(s, "%d/%m/%Y")
        return dt.date().isoformat()
    except:
        pass
    return None

def normalize_time_str(s):
    s = s.strip().lower().replace('.', ':').replace(' ', '')
    m = re.match(r'^(\d{1,2}):(\d{2})$', s)
    if m:
        h = int(m.group(1)); mm = int(m.group(2))
        if 0 <= h < 24 and 0 <= mm < 60:
            return f"{h:02d}:{mm:02d}"
    m2 = re.match(r'^(\d{1,2}):?(\d{2})?(am|pm)$', s)
    if m2:
        h = int(m2.group(1))
        mm = int(m2.group(2)) if m2.group(2) else 0
        ampm = m2.group(3)
        if ampm == 'pm' and h != 12:
            h += 12
        if ampm == 'am' and h == 12:
            h = 0
        if 0 <= h < 24 and 0 <= mm < 60:
            return f"{h:02d}:{mm:02d}"
    m3 = re.match(r'^(\d{1,2})$', s)
    if m3:
        h = int(m3.group(1))
        if 0 <= h < 24:
            return f"{h:02d}:00"
    return None

def detect_booking_intent(text):
    kws = ['book','appointment','reserve','schedule','slot','booked','booking']
    return any(k in text.lower() for k in kws)

def extract_booking_info(text):
    text_norm = text.strip()
    date = None
    for dt_pat in [r'(\d{4}-\d{2}-\d{2})', r'(\d{1,2}-\d{1,2}-\d{4})', r'(\d{1,2}/\d{1,2}/\d{4})']:
        m = re.search(dt_pat, text_norm)
        if m:
            dnorm = normalize_date_str(m.group(1))
            if dnorm:
                date = dnorm
                break
    time = None
    time_candidates = re.findall(r'(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)?)', text_norm, flags=re.I)
    for cand in time_candidates:
        tnorm = normalize_time_str(cand)
        if tnorm:
            time = tnorm
            break
    services = ['haircut','hair color','color','facial','nails','manicure','pedicure','spa','groom','shave','trim']
    service = None
    for s in services:
        if re.search(r'\b'+re.escape(s)+r'\b', text_norm, flags=re.I):
            service = s
            break
    phone = None
    mphone = re.search(r'(\+?\d[\d\s\-]{8,}\d)', text_norm)
    if mphone:
        phone_raw = re.sub(r'[\s\-]', '', mphone.group(1))
        if 8 <= len(phone_raw) <= 15:
            phone = phone_raw
    name = None
    mname = re.search(r'(?:for|my name is|i am|i\'m|im)\s+([A-Za-z][a-zA-Z]+(?:\s[A-Za-z][a-zA-Z]+)?)', text_norm, flags=re.I)
    if mname:
        name = mname.group(1).strip()
    gender = None
    if re.search(r'\b(male|man|mr|m)\b', text_norm, flags=re.I):
        gender = 'male'
    if re.search(r'\b(female|woman|mrs|ms|miss|f)\b', text_norm, flags=re.I):
        gender = 'female'
    age = None
    mage = re.search(r'\b(\d{2})\b', text_norm)
    if mage:
        a = int(mage.group(1))
        if 10 <= a <= 99:
            age = str(a)
    return {'date': date, 'time': time, 'service': service, 'phone': phone, 'name': name, 'gender': gender, 'age': age}

# ------------------ Chat endpoint with session handling ------------------
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        payload = request.json or {}
        message = (payload.get('message') or '').strip()
        # session_id: either provided by frontend or 'anon'
        session_id = payload.get('session_id') or 'anon'
        # ensure session exists
        session = SESSIONS.setdefault(session_id, {})

        # standardize message
        lower = message.lower().strip()
        if not message:
            return jsonify({'ok': False, 'reply': 'Please type something so I can help.'})

        # If session expects profile details (after a previous booking or 'yes')
        if session.get('expecting_profile'):
            # parse face/skin/gender/age from this message and produce suggestion
            # reuse suggestion extraction logic
            face = None
            for f in ['oval','round','square','heart','long','diamond','oblong']:
                if re.search(r'\b'+f+r'\b', message, flags=re.I):
                    face = f
                    break
            skin = None
            for s in ['fair','medium','olive','dark','deep','light','oily','dry','normal']:
                if re.search(r'\b'+s+r'\b', message, flags=re.I):
                    skin = s
                    break
            gender = None
            if re.search(r'\b(male|man|mr|m)\b', message, flags=re.I):
                gender = 'male'
            if re.search(r'\b(female|woman|mrs|ms|miss|f)\b', message, flags=re.I):
                gender = 'female'
            age = None
            mage = re.search(r'\b(\d{2})\b', message)
            if mage:
                a = int(mage.group(1))
                if 10 <= a <= 99:
                    age = str(a)

            # if insufficient info ask again
            missing = []
            if not face: missing.append('face shape')
            if not skin: missing.append('skin tone or hair condition')
            if not gender: missing.append('gender')
            if not age: missing.append('age')

            if missing:
                return jsonify({'ok': True, 'reply': "Please provide: " + ", ".join(missing) + ". Example: 'round face, fair skin, female, 28'."})

            # got profile — generate suggestion
            suggestion = generate_suggestion(face, skin, age, gender, service_intent=None)
            # optionally link suggestion to booking (if booking id present)
            if session.get('last_booking_id'):
                # here we could save profile into customers table or update booking; keep simple
                pass
            # clear expecting flag
            session['expecting_profile'] = False
            return jsonify({'ok': True, 'reply': suggestion})

        # handle simple affirmative response to previous booking question
        if lower in ('yes','y','yeah','sure','ok','please'):
            if session.get('asked_profile_after_booking'):
                session['expecting_profile'] = True
                session['asked_profile_after_booking'] = False
                return jsonify({'ok': True, 'reply': "Great — please tell me your face shape, skin tone (or hair condition), gender and age. Example: 'round face, fair skin, female, 28'."})

        # Booking flow (detect booking intent)
        if detect_booking_intent(message):
            info = extract_booking_info(message)
            missing = []
            if not info['service']: missing.append('service (e.g., haircut)')
            if not info['date']: missing.append('date (YYYY-MM-DD or DD-MM-YYYY)')
            if not info['time']: missing.append('time (e.g., 15:30 or 3pm)')
            if not info['name']: missing.append('your name')
            if not info['phone']: missing.append('phone number')
            if missing:
                ask = "I can book that — I still need: " + ", ".join(missing) + "."
                ask += " Example: 'Book haircut on 2025-12-20 at 15:00 for Rahul 9876543210 (male, 28)'."
                return jsonify({'ok': True, 'reply': ask})

            # create tentative booking
            db = get_db()
            cur = db.cursor()
            cur.execute('''
                INSERT INTO bookings (name, phone, gender, age, service, date, time, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                info['name'],
                info['phone'],
                info.get('gender'),
                int(info['age']) if info.get('age') else None,
                info['service'],
                info['date'],
                info['time'],
                datetime.utcnow().isoformat(),
                'tentative'
            ))
            db.commit()
            booking_id = cur.lastrowid
            # set session state: we asked to add profile
            session['last_booking_id'] = booking_id
            session['asked_profile_after_booking'] = True
            # reply asks to add profile; next user can say 'yes' or give profile directly
            return jsonify({'ok': True, 'reply': f"Done — tentative booking created (ID {booking_id}). We'll confirm once you verify. Would you like to add face shape & skin tone for hairstyle suggestions?"})

        # Suggestions intent (user may proactively ask without booking)
        if any(k in message.lower() for k in ['hairstyle','haircut','hair color','color','groom','grooming','product','products','face','skin','suggest','recommend']):
            face = None
            for f in ['oval','round','square','heart','long','diamond','oblong']:
                if re.search(r'\b'+f+r'\b', message, flags=re.I):
                    face = f
                    break
            skin = None
            for s in ['fair','medium','olive','dark','deep','light','oily','dry','normal']:
                if re.search(r'\b'+s+r'\b', message, flags=re.I):
                    skin = s
                    break
            gender = None
            if re.search(r'\b(male|man|mr|m)\b', message, flags=re.I):
                gender = 'male'
            if re.search(r'\b(female|woman|mrs|ms|miss|f)\b', message, flags=re.I):
                gender = 'female'
            age = None
            mage = re.search(r'\b(\d{2})\b', message)
            if mage:
                a = int(mage.group(1))
                if 10 <= a <= 99:
                    age = str(a)

            missing = []
            if not face: missing.append('face shape (oval/round/square/heart/long)')
            if not skin: missing.append('skin tone (fair/medium/olive/dark) or hair condition (dry/oily/normal)')
            if not gender: missing.append('gender (male/female)')
            if not age: missing.append('age (number)')

            if missing:
                return jsonify({'ok': True, 'reply': "To recommend precisely I need: " + ", ".join(missing) + ". Example: 'round face, fair skin, female, 28'."})

            suggestion = generate_suggestion(face, skin, age, gender, service_intent=None)
            return jsonify({'ok': True, 'reply': suggestion})

        # Save profile flow
        if message.lower().startswith('profile') or 'my name' in message.lower():
            info = extract_booking_info(message)
            face = None
            skin = None
            for f in ['oval','round','square','heart','long','diamond']:
                if re.search(r'\b'+f+r'\b', message, flags=re.I):
                    face = f
                    break
            for s in ['fair','medium','olive','dark','dry','oily','normal']:
                if re.search(r'\b'+s+r'\b', message, flags=re.I):
                    skin = s
                    break
            name = info.get('name') or None
            phone = info.get('phone') or None
            gender = info.get('gender') or None
            age = int(info['age']) if info.get('age') else None

            if not (name and phone):
                return jsonify({'ok': False, 'reply': "To save profile I need at least your name and phone. Example: 'My name is Rahul 9876543210, male, 28, round face, fair skin'."})

            db = get_db()
            cur = db.cursor()
            cur.execute('''
                INSERT INTO customers (name, phone, gender, age, skin_tone, face_shape, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, gender, age, skin, face, datetime.utcnow().isoformat()))
            db.commit()
            return jsonify({'ok': True, 'reply': f"Profile saved for {name}. You can now ask 'Recommend hairstyle for me'."})

        return jsonify({'ok': True, 'reply': "I can help with bookings and personalized hairstyle/product suggestions. Try: 'Book haircut on 2025-12-20 at 15:00 for Rahul 9876543210 male 28' or 'Recommend hairstyle for round face fair skin female 28'."})

    except Exception as e:
        print("Chat handler error:", str(e))
        return jsonify({'ok': False, 'reply': 'Sorry — something went wrong on the server. Try rephrasing or try again.'})

# ------------------ Start server ------------------
if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    with app.app_context():
        init_db()
    app.run(debug=True, port=5000)
