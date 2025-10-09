from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os
import pandas as pd
import joblib
import datetime
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-me")
jwt = JWTManager(app)

# Simple SQLite DB for users and appointments (file-based in backend folder)
DB_PATH = os.path.join(BASE_DIR, "mediassist.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT UNIQUE,
                    password TEXT,
                    phone TEXT,
                    role TEXT DEFAULT "user",
                    created_at TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    doctor TEXT,
                    disease TEXT,
                    datetime TEXT,
                    notes TEXT)''')
    con.commit()
    con.close()

init_db()

# Load symptom severity data if present
symptoms_csv = os.path.join(BASE_DIR, "data", "Symptom-severity.csv")
if os.path.exists(symptoms_csv):
    try:
        symptoms_df = pd.read_csv(symptoms_csv)
    except Exception:
        symptoms_df = None
else:
    symptoms_df = None

# Attempt to load a saved model if exists (models/symptom_model.pkl)
model_path = os.path.join(BASE_DIR, "models", "symptom_model.pkl")
MODEL = None
if os.path.exists(model_path):
    try:
        MODEL = joblib.load(model_path)
    except Exception:
        MODEL = None

def simple_symptom_predict(symptoms_list):
    """Fallback rule-based prediction: sum severity weights and map to disease percentiles."""
    if symptoms_df is None or len(symptoms_list) == 0:
        return {"disease": "unknown", "confidence": 0.0, "explanation": "insufficient data"}
    matched = symptoms_df[symptoms_df['Symptom'].str.lower().isin([s.lower() for s in symptoms_list])]
    score = float(matched['weight'].sum()) if ('weight' in matched.columns and not matched.empty) else float(len(matched))
    conf = 0.1
    if score > 15:
        disease = "high-risk-possible-disease"
        conf = min(0.95, 0.5 + score/40)
    elif score > 7:
        disease = "medium-risk-possible-disease"
        conf = min(0.8, 0.35 + score/30)
    elif score > 0:
        disease = "low-risk-possible-disease"
        conf = min(0.6, 0.2 + score/20)
    else:
        disease = "no-significant-symptoms"
        conf = 0.05
    return {"disease": disease, "confidence": float(conf), "score": float(score)}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "time": datetime.datetime.utcnow().isoformat()}), 200

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone', '')
    if not (name and email and password):
        return jsonify({"error": "name, email and password are required"}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute('INSERT INTO users (name,email,password,phone,created_at) VALUES (?,?,?,?,?)',
                    (name, email, password, phone, datetime.datetime.utcnow().isoformat()))
        con.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        con.close()
        return jsonify({"error": "email already registered"}), 409
    con.close()
    return jsonify({"message": "registered", "user_id": user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not (email and password):
        return jsonify({"error": "email and password required"}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT id, password, name FROM users WHERE email = ?', (email,))
    row = cur.fetchone()
    con.close()
    if not row or row[1] != password:
        return jsonify({"error": "invalid credentials"}), 401
    access_token = create_access_token(identity={'id': row[0], 'email': email, 'name': row[2]})
    return jsonify({"access_token": access_token, "user": {"id": row[0], "email": email, "name": row[2]}})

@app.route('/api/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    identity = get_jwt_identity()
    # allow users to fetch their own profile or admin (simple rule)
    if identity.get('id') != user_id and identity.get('email') != 'admin@example.com':
        return jsonify({"error": "forbidden"}), 403
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT id, name, email, phone, role, created_at FROM users WHERE id=?', (user_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": row[0], "name": row[1], "email": row[2], "phone": row[3], "role": row[4], "created_at": row[5]})

@app.route('/api/predict', methods=['POST'])
def predict_symptoms():
    payload = request.get_json() or {}
    symptoms = payload.get('symptoms') or []
    if not isinstance(symptoms, list):
        return jsonify({"error": "symptoms must be a list"}), 400

    # Use ML model if available
    if MODEL is not None:
        try:
            # This assumes the model accepts a single numeric feature as placeholder.
            features = [[len(symptoms)]]
            pred = MODEL.predict(features)[0]
            return jsonify({"disease": str(pred), "confidence": 0.75})
        except Exception:
            pass

    # fallback deterministic rule-based prediction
    result = simple_symptom_predict(symptoms)
    return jsonify(result)

@app.route('/api/image-predict', methods=['POST'])
def image_predict():
    # Accept file upload (multipart/form-data)
    if 'file' not in request.files:
        return jsonify({"error": "file required"}), 400
    f = request.files['file']
    safe_name = f.filename.replace('..','').replace('/','_')
    upload_dir = os.path.join(BASE_DIR, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, safe_name)
    f.save(path)
    # Placeholder response until a TF/PyTorch model is integrated
    return jsonify({"prediction": "no-model-provided", "file": safe_name}), 200

@app.route('/api/diet/<disease>', methods=['GET'])
def diet_for_disease(disease):
    diet_path = os.path.join(BASE_DIR, 'data', 'diet_recommendations.json')
    if os.path.exists(diet_path):
        try:
            with open(diet_path,'r') as fh:
                data = json.load(fh)
            return jsonify(data.get(disease, {"diet": [], "notes": "no data for disease"}))
        except Exception:
            pass
    return jsonify({"diet": [], "notes": "no diet data available"})

@app.route('/api/precautions/<disease>', methods=['GET'])
def precautions(disease):
    prec_path_csv = os.path.join(BASE_DIR, 'data', 'symptom_precaution.csv')
    if os.path.exists(prec_path_csv):
        try:
            df = pd.read_csv(prec_path_csv)
            if 'Disease' in df.columns:
                matched = df[df['Disease'].str.lower() == disease.lower()]
                if not matched.empty:
                    return jsonify(matched.to_dict(orient='records'))
        except Exception:
            pass
    return jsonify([])

@app.route('/api/medications/<disease>', methods=['GET'])
def medications(disease):
    meds_path = os.path.join(BASE_DIR, 'data', 'medications.json')
    if os.path.exists(meds_path):
        try:
            with open(meds_path,'r') as fh:
                data = json.load(fh)
            return jsonify(data.get(disease, []))
        except Exception:
            pass
    return jsonify([])

@app.route('/api/doctors/<disease>', methods=['GET'])
def doctors(disease):
    mapping = {
        'cancer': ['Oncologist - Dr. A (City Hospital)', 'Oncologist - Dr. B (Regional Clinic)'],
        'diabetes': ['Endocrinologist - Dr. C'],
        'fever': ['General Physician - Dr. D']
    }
    for k,v in mapping.items():
        if k in disease.lower():
            return jsonify(v)
    return jsonify(['General Physician - Local Clinic'])

@app.route('/api/appointments', methods=['POST'])
@jwt_required()
def book_appointment():
    identity = get_jwt_identity()
    payload = request.get_json() or {}
    doctor = payload.get('doctor')
    disease = payload.get('disease','')
    dt = payload.get('datetime')
    notes = payload.get('notes','')
    if not doctor or not dt:
        return jsonify({"error":"doctor and datetime required"}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('INSERT INTO appointments (user_id,doctor,disease,datetime,notes) VALUES (?,?,?,?,?)',
                (identity.get('id'), doctor, disease, dt, notes))
    con.commit()
    appt_id = cur.lastrowid
    con.close()
    return jsonify({"message":"booked","appointment_id": appt_id}), 201

@app.route('/api/chat', methods=['POST'])
def chat():
    payload = request.get_json() or {}
    message = payload.get('message','').lower()
    if 'fever' in message:
        return jsonify({"response":"It sounds like you have a fever. Monitor temperature and stay hydrated. Seek urgent care if >39C or severe symptoms."})
    if 'pain' in message:
        return jsonify({"response":"For pain management, consider rest and OTC analgesics. See a doctor for persistent pain."})
    return jsonify({"response":"Please provide more details about your symptoms (duration, severity, other signs)."})

@app.route('/api/sos', methods=['POST'])
def sos():
    payload = request.get_json() or {}
    contacts = payload.get('contacts', [])
    message = payload.get('message','Emergency! Please help.')
    # Placeholder: in production integrate with SMS/email provider
    return jsonify({"sent": len(contacts), "message": message})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
