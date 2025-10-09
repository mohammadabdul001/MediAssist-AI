from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json

class EmergencySOS:
    def __init__(self):
        self.collection = db.emergency_logs
        self.users = db.users
        self.health_records = db.health_records
        self.chatbot = db.chatbot_conversations
        self.telemedicine = db.telemedicine_sessions

    def trigger_sos(self, user_id, message="Emergency help needed", location=None, auto_triggered=False):
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        emergency_contacts = user.get("emergency_contacts", [])
        if not emergency_contacts:
            raise ValueError("No emergency contacts configured. Please add contacts in your profile.")

        health_status = self._get_user_health_status(user_id)

        if not location:
            location = user.get("profile", {}).get("address", "Location not available")
            if location == "Location not available":
                last_location = self._get_last_known_location(user_id)
                if last_location:
                    location = last_location

        sos_log = {
            "user_id": ObjectId(user_id),
            "username": user.get("username", "Unknown"),
            "message": message,
            "location": location,
            "health_status": health_status,
            "auto_triggered": bool(auto_triggered),
            "triggered_at": datetime.utcnow(),
            "contacts_notified": [],
            "hospitals_notified": [],
            "status": "triggered",
            "first_aid_instructions": [],
            "telemedicine_session_id": None
        }

        first_aid_instructions = self._get_ai_first_aid_instructions(user_id, health_status)
        sos_log["first_aid_instructions"] = first_aid_instructions

        active_session = self.telemedicine.find_one({
            "patient_id": ObjectId(user_id),
            "status": "active"
        })
        if active_session:
            sos_log["telemedicine_session_id"] = active_session["_id"]
            self._notify_doctor_in_session(active_session, sos_log)

        for contact in emergency_contacts:
            try:
                self._send_alert_to_contact(contact, user, sos_log)
                sos_log["contacts_notified"].append(contact)
            except Exception as e:
                print(f"Failed to notify contact {contact}: {str(e)}")

        nearby_hospitals = self._get_nearby_hospitals(location)
        for hospital in nearby_hospitals[:3]:
            try:
                self._send_alert_to_hospital(hospital, user, sos_log)
                sos_log["hospitals_notified"].append(hospital)
            except Exception as e:
                print(f"Failed to notify hospital {hospital}: {str(e)}")

        sos_log["status"] = "notified" if (sos_log["contacts_notified"] or sos_log["hospitals_notified"]) else "failed"

        result = self.collection.insert_one(sos_log)
        sos_log["_id"] = result.inserted_id

        return self._serialize(sos_log)

    def get_sos_history(self, user_id, limit=10):
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        sos_logs = self.collection.find({
            "user_id": ObjectId(user_id)
        }).sort("triggered_at", -1).limit(limit)

        return [self._serialize(log) for log in sos_logs]

    def get_sos_by_id(self, sos_id):
        if not ObjectId.is_valid(sos_id):
            raise ValueError("Invalid SOS ID format")

        sos_log = self.collection.find_one({"_id": ObjectId(sos_id)})
        if not sos_log:
            raise ValueError("SOS alert not found")

        return self._serialize(sos_log)

    def _get_user_health_status(self, user_id):
        health_status = {
            "vital_signs": {},
            "recent_symptoms": [],
            "active_conditions": [],
            "medications": []
        }

        one_day_ago = datetime.utcnow() - timedelta(days=1)
        recent_vitals = self.health_records.find_one({
            "user_id": ObjectId(user_id),
            "type": "vitals",
            "created_at": {"$gte": one_day_ago}
        }, sort=[("created_at", -1)])

        if recent_vitals:
            health_status["vital_signs"] = recent_vitals.get("data", {})

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_symptoms = self.health_records.find({
            "user_id": ObjectId(user_id),
            "type": "symptom_analysis",
            "created_at": {"$gte": seven_days_ago}
        }, sort=[("created_at", -1)]).limit(3)

        for analysis in recent_symptoms:
            predictions = analysis.get("predictions")
            if predictions and isinstance(predictions, list) and len(predictions) > 0:
                top_prediction = predictions[0]
                health_status["recent_symptoms"].append({
                    "disease": top_prediction.get("disease", "Unknown"),
                    "probability": top_prediction.get("probability", 0),
                    "risk_percentage": analysis.get("risk_percentage", 0)
                })

        user = self.users.find_one({"_id": ObjectId(user_id)})
        if user:
            health_status["active_conditions"] = user.get("health_data", {}).get("chronic_conditions", [])

        active_meds = self.health_records.find({
            "user_id": ObjectId(user_id),
            "type": "medication_event",
            "event_type": "medication_added",
            "data.status": "active"
        }).sort("created_at", -1).limit(5)

        for med in active_meds:
            data = med.get("data", {})
            health_status["medications"].append({
                "name": data.get("name", ""),
                "dosage": data.get("dosage", ""),
                "frequency": data.get("frequency", "")
            })

        return health_status

    def _get_ai_first_aid_instructions(self, user_id, health_status):
        instructions = [
            "Stay calm and try to remain still",
            "If you're having trouble breathing, sit in a comfortable position",
            "If you're bleeding, apply pressure to the wound",
            "If you're experiencing chest pain, chew an aspirin (if not allergic)",
            "Do not eat or drink anything until help arrives"
        ]

        vitals = health_status.get("vital_signs", {})
        
        # Blood pressure check
        if "blood_pressure" in vitals:
            bp_str = vitals["blood_pressure"]
            try:
                systolic = int(str(bp_str).split("/")[0])
                if systolic > 180:
                    instructions.append("You have extremely high blood pressure. Sit down, relax, and avoid any physical exertion.")
            except (ValueError, IndexError):
                pass

        # Blood glucose check
        if "blood_glucose" in vitals:
            glucose_str = vitals["blood_glucose"]
            try:
                glucose = float(str(glucose_str).split()[0])
                if glucose < 70:
                    instructions.append("Your blood sugar is low. If you're conscious, consume 15-20 grams of fast-acting carbohydrates (like juice or glucose tablets).")
            except (ValueError, IndexError):
                pass

        # Symptom-based instructions
        for symptom in health_status.get("recent_symptoms", []):
            disease = symptom.get("disease", "")
            risk = symptom.get("risk_percentage", 0)
            if disease == "Heart attack" and risk > 70:
                instructions.append("⚠️ HEART ATTACK SUSPECTED: Call emergency services immediately. Chew and swallow an aspirin if not allergic. Sit down and stay calm.")
            elif disease == "Stroke" and risk > 70:
                instructions.append("⚠️ STROKE SUSPECTED: Remember FAST - Face drooping, Arm weakness, Speech difficulty, Time to call emergency services.")
            elif disease == "Severe allergic reaction" and risk > 70:
                instructions.append("⚠️ SEVERE ALLERGIC REACTION: Use epinephrine auto-injector if available. Lie down and elevate legs if feeling faint.")

        # Medication-based instructions
        for med in health_status.get("medications", []):
            name = med.get("name", "").lower()
            if "insulin" in name:
                instructions.append("If you take insulin, inform responders about your diabetes and recent insulin doses.")
            elif "warfarin" in name or "blood thinner" in name:
                instructions.append("You take blood thinners. Inform responders to be careful with any procedures that might cause bleeding.")

        return instructions[:10]

    def _get_last_known_location(self, user_id):
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        wearable_data = self.health_records.find_one({
            "user_id": ObjectId(user_id),
            "type": "wearable_data",
            "data.location": {"$exists": True},
            "created_at": {"$gte": seven_days_ago}
        }, sort=[("created_at", -1)])

        if wearable_data:
            return wearable_data.get("data", {}).get("location")
        return None

    def _get_nearby_hospitals(self, location):
        return [
            {"name": "City General Hospital", "address": "123 Main St", "phone": "555-1234", "distance": "2.3 miles"},
            {"name": "Mercy Medical Center", "address": "456 Oak Ave", "phone": "555-5678", "distance": "3.1 miles"},
            {"name": "Community Health Clinic", "address": "789 Pine Rd", "phone": "555-9012", "distance": "1.8 miles"}
        ]

    def _send_alert_to_contact(self, contact, user, sos_log):
        if "@" in contact:
            self._send_email_alert(contact, user, sos_log)
        elif contact.isdigit() and len(contact) >= 10:
            self._send_sms_alert(contact, user, sos_log)
        else:
            self._send_in_app_notification(contact, user, sos_log)

    def _send_email_alert(self, email, user, sos_log):
        try:
            subject = f"EMERGENCY ALERT: {user.get('username', 'User')} needs help!"
            body = f"""
EMERGENCY SOS ALERT

User: {user.get('username', 'Unknown')}
Message: {sos_log['message']}
Location: {sos_log['location']}
Triggered at: {sos_log['triggered_at'].strftime('%Y-%m-%d %H:%M:%S')} UTC

Health Status:
{json.dumps(sos_log['health_status'], indent=2)}

First Aid Instructions:
{chr(10).join(['• ' + instruction for instruction in sos_log['first_aid_instructions']])}

Please respond immediately!
"""
            print(f"EMERGENCY EMAIL SENT TO {email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
        except Exception as e:
            print(f"Failed to send email to {email}: {str(e)}")
            raise

    def _send_sms_alert(self, phone, user, sos_log):
        try:
            message = f"EMERGENCY: {user.get('username', 'User')} needs help! Location: {sos_log['location']}. Respond immediately!"
            print(f"EMERGENCY SMS SENT TO {phone}")
            print(f"Message: {message}")
        except Exception as e:
            print(f"Failed to send SMS to {phone}: {str(e)}")
            raise

    def _send_in_app_notification(self, username, user, sos_log):
        try:
            contact_user = self.users.find_one({"username": username})
            if not contact_user:
                raise ValueError(f"User {username} not found")

            notification = {
                "user_id": contact_user["_id"],
                "type": "emergency_sos",
                "title": "Emergency SOS Alert",
                "message": f"{user.get('username', 'User')} has triggered an emergency SOS alert. Location: {sos_log['location']}. Please respond immediately!",
                "data": {
                    "sos_id": str(sos_log["_id"]),
                    "patient_id": str(user["_id"]),
                    "patient_username": user.get('username', 'Unknown'),
                    "location": sos_log['location'],
                    "health_status": sos_log['health_status'],
                    "first_aid_instructions": sos_log['first_aid_instructions']
                },
                "created_at": datetime.utcnow(),
                "read": False
            }

            if hasattr(db, 'notifications'):
                db.notifications.insert_one(notification)
            else:
                # Fallback: create collection if missing
                db.create_collection('notifications')
                db.notifications.insert_one(notification)

            print(f"IN-APP EMERGENCY NOTIFICATION SENT TO {username}")

        except Exception as e:
            print(f"Failed to send in-app notification to {username}: {str(e)}")
            raise

    def _send_alert_to_hospital(self, hospital, user, sos_log):
        try:
            hospital_email = f"emergency@{hospital['name'].lower().replace(' ', '')}.com"
            subject = f"HOSPITAL EMERGENCY ALERT: Patient needs immediate assistance"
            body = f"""
HOSPITAL EMERGENCY ALERT

Patient: {user.get('username', 'Unknown')}
Contact: {user.get('profile', {}).get('phone', 'Not available')}
Message: {sos_log['message']}
Location: {sos_log['location']} ({hospital['distance']})
Triggered at: {sos_log['triggered_at'].strftime('%Y-%m-%d %H:%M:%S')} UTC

Patient Health Status:
{json.dumps(sos_log['health_status'], indent=2)}

First Aid Instructions Provided to Patient:
{chr(10).join(['• ' + instruction for instruction in sos_log['first_aid_instructions']])}

Please dispatch emergency services immediately!
"""
            print(f"EMERGENCY ALERT SENT TO HOSPITAL: {hospital['name']}")
            print(f"Email: {hospital_email}")
            print(f"Subject: {subject}")
        except Exception as e:
            print(f"Failed to send alert to hospital {hospital['name']}: {str(e)}")
            raise

    def _notify_doctor_in_session(self, session, sos_log):
        try:
            doctor_id = session.get("doctor_id")
            if not doctor_id:
                return

            doctor = self.users.find_one({"_id": doctor_id})
            if not doctor:
                return

            notification = {
                "user_id": doctor_id,
                "type": "emergency_sos_during_session",
                "title": "Emergency During Telemedicine Session",
                "message": f"Your patient {sos_log['username']} has triggered an emergency SOS during your active session. Location: {sos_log['location']}. Please provide immediate guidance.",
                "data": {
                    "sos_id": str(sos_log["_id"]),
                    "session_id": str(session["_id"]),
                    "patient_id": str(sos_log["user_id"]),
                    "patient_username": sos_log['username'],
                    "location": sos_log['location'],
                    "health_status": sos_log['health_status'],
                    "first_aid_instructions": sos_log['first_aid_instructions']
                },
                "created_at": datetime.utcnow(),
                "read": False
            }

            if hasattr(db, 'notifications'):
                db.notifications.insert_one(notification)
            else:
                db.create_collection('notifications')
                db.notifications.insert_one(notification)

            print(f"EMERGENCY NOTIFICATION SENT TO DOCTOR IN SESSION: {doctor.get('username', 'Unknown')}")

        except Exception as e:
            print(f"Failed to notify doctor in session: {str(e)}")
            raise

    def auto_trigger_sos_from_wearable(self, user_id, abnormal_data):
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        if not isinstance(abnormal_data, dict):
            raise ValueError("Abnormal data must be a dictionary")

        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        auto_trigger_enabled = user.get("profile", {}).get("auto_sos_enabled", False)
        if not auto_trigger_enabled:
            raise ValueError("Auto-trigger SOS is not enabled for this user")

        message = "Auto-triggered emergency alert from wearable device"
        # ✅ FIXED: was 'abnormal_' → now 'abnormal_data'
        if "heart_rate" in abnormal_data:
            message = f"Abnormal heart rate detected: {abnormal_data['heart_rate']} bpm"
        elif abnormal_data.get("fall_detected"):
            message = "Fall detected by wearable device"
        elif "oxygen_saturation" in abnormal_data:
            message = f"Low oxygen saturation detected: {abnormal_data['oxygen_saturation']}%"

        sos_log = self.trigger_sos(
            user_id=user_id,
            message=message,
            location=abnormal_data.get("location"),
            auto_triggered=True
        )

        return sos_log

    def _serialize(self, sos_log):
        if sos_log:
            sos_log["_id"] = str(sos_log["_id"])
            sos_log["user_id"] = str(sos_log["user_id"])
            if sos_log.get("telemedicine_session_id"):
                sos_log["telemedicine_session_id"] = str(sos_log["telemedicine_session_id"])
            sos_log["triggered_at"] = sos_log["triggered_at"].isoformat()
        return sos_log