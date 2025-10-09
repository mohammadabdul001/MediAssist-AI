from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import uuid
import hashlib
import secrets

class Telemedicine:
    def __init__(self):
        self.collection = db.telemedicine_sessions
        self.appointments = db.appointments
        self.users = db.users
        self.health_records = db.health_records
        self.medications = db.medications
        self.prescriptions = db.prescriptions  # For digital prescriptions

    def create_session(self, appointment_id, patient_id, doctor_id):
        """
        Create a telemedicine session for an appointment.
        This generates a secure meeting link and initializes the session.
        """
        if not ObjectId.is_valid(appointment_id) or not ObjectId.is_valid(patient_id) or not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid ID format")

        # Validate appointment exists and is for video consultation
        appointment = self.appointments.find_one({
            "_id": ObjectId(appointment_id),
            "patient_id": ObjectId(patient_id),
            "doctor_id": ObjectId(doctor_id),
            "type": "video",
            "status": {"$in": ["scheduled", "confirmed"]}
        })
        if not appointment:
            raise ValueError("Appointment not found or not eligible for telemedicine")

        # Validate users exist
        patient = self.users.find_one({"_id": ObjectId(patient_id)})
        doctor = self.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor"})
        if not patient or not doctor:
            raise ValueError("Patient or doctor not found")

        # Generate secure session ID and meeting link
        session_id = str(uuid.uuid4())
        # Create a secure, unique meeting code (8 characters)
        meeting_code = self._generate_meeting_code()
        meeting_link = f"https://mediassist.ai/meet/{meeting_code}"

        # Create session record
        session = {
            "appointment_id": ObjectId(appointment_id),
            "patient_id": ObjectId(patient_id),
            "doctor_id": ObjectId(doctor_id),
            "session_id": session_id,
            "meeting_code": meeting_code,
            "meeting_link": meeting_link,
            "status": "scheduled",  # "scheduled", "active", "completed", "cancelled"
            "created_at": datetime.utcnow(),
            "scheduled_start_time": appointment.get("start_time"),
            "started_at": None,
            "ended_at": None,
            "duration_minutes": 0,
            "participants": {
                "patient_joined_at": None,
                "doctor_joined_at": None,
                "patient_left_at": None,
                "doctor_left_at": None
            },
            "chat_messages": [],
            "shared_files": [],
            "prescriptions_issued": [],
            "consultation_summary": "",
            "vitals_recorded": {},
            "ai_assistance_enabled": True,
            "recording_enabled": False,
            "recording_url": None,
            "transcript": None
        }

        result = self.collection.insert_one(session)
        session["_id"] = result.inserted_id

        # Update appointment status to "in_progress" when session is created
        self.appointments.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"status": "in_progress"}}
        )

        return self._serialize(session)

    def get_session(self, session_id):
        """Get a telemedicine session by ID."""
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        return self._serialize(session)

    def get_user_sessions(self, user_id, role="patient", status=None):
        """Get all telemedicine sessions for a user (as patient or doctor)."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        query = {}
        if role == "patient":
            query["patient_id"] = ObjectId(user_id)
        elif role == "doctor":
            query["doctor_id"] = ObjectId(user_id)
        else:
            raise ValueError("Role must be 'patient' or 'doctor'")

        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status

        sessions = self.collection.find(query).sort("created_at", -1)
        return [self._serialize(session) for session in sessions]

    def start_session(self, session_id, user_id):
        """Start a telemedicine session (called when user joins the meeting)."""
        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(user_id):
            raise ValueError("Invalid ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        # Verify user is either patient or doctor for this session
        if str(user_id) != str(session["patient_id"]) and str(user_id) != str(session["doctor_id"]):
            raise ValueError("User not authorized for this session")

        update_fields = {
            "status": "active",
            "started_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        # Record who joined
        if str(user_id) == str(session["patient_id"]):
            update_fields["participants.patient_joined_at"] = datetime.utcnow()
        else:
            update_fields["participants.doctor_joined_at"] = datetime.utcnow()

        result = self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_fields}
        )

        if result.modified_count == 0:
            raise ValueError("Session not updated")

        updated_session = self.collection.find_one({"_id": ObjectId(session_id)})
        return self._serialize(updated_session)

    def end_session(self, session_id, summary="", prescriptions=None, vitals=None):
        """End a telemedicine session and generate consultation summary."""
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        if session["status"] != "active":
            raise ValueError("Session is not active")

        # Calculate duration
        started_at = session.get("started_at")
        ended_at = datetime.utcnow()
        duration_minutes = 0
        if started_at:
            duration = ended_at - started_at
            duration_minutes = int(duration.total_seconds() / 60)

        update_fields = {
            "status": "completed",
            "ended_at": ended_at,
            "duration_minutes": duration_minutes,
            "consultation_summary": summary.strip(),
            "updated_at": datetime.utcnow()
        }

        # Record who left
        update_fields["participants.patient_left_at"] = ended_at
        update_fields["participants.doctor_left_at"] = ended_at

        # Add prescriptions if provided
        if prescriptions and isinstance(prescriptions, list):
            prescription_ids = []
            for prescription in prescriptions:
                presc_id = self._create_prescription(
                    patient_id=str(session["patient_id"]),
                    doctor_id=str(session["doctor_id"]),
                    session_id=str(session["_id"]),
                    medication_name=prescription.get("name"),
                    dosage=prescription.get("dosage"),
                    frequency=prescription.get("frequency"),
                    duration_days=prescription.get("duration_days"),
                    notes=prescription.get("notes", "")
                )
                if presc_id:
                    prescription_ids.append(presc_id)
                    update_fields["$push"] = {"prescriptions_issued": presc_id}

        # Add vitals if provided
        if vitals and isinstance(vitals, dict):
            update_fields["vitals_recorded"] = vitals

        # Update session
        result = self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_fields} if "$push" not in update_fields else {
                "$set": {k: v for k, v in update_fields.items() if k != "$push"},
                "$push": update_fields["$push"]
            }
        )

        if result.modified_count == 0:
            raise ValueError("Session not updated")

        # Update appointment status to "completed"
        self.appointments.update_one(
            {"_id": session["appointment_id"]},
            {"$set": {"status": "completed", "completed_at": ended_at}}
        )

        # Create health record for consultation
        self._create_consultation_record(session_id, summary, prescriptions, vitals)

        updated_session = self.collection.find_one({"_id": ObjectId(session_id)})
        return self._serialize(updated_session)

    def send_chat_message(self, session_id, sender_id, message, message_type="text"):
        """Send a chat message during a telemedicine session."""
        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(sender_id):
            raise ValueError("Invalid ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        # Verify sender is participant in session
        if str(sender_id) != str(session["patient_id"]) and str(sender_id) != str(session["doctor_id"]):
            raise ValueError("Sender not authorized for this session")

        # Get sender role
        sender_role = "patient" if str(sender_id) == str(session["patient_id"]) else "doctor"

        # Get sender name
        sender = self.users.find_one({"_id": ObjectId(sender_id)})
        sender_name = sender.get("username", "Unknown") if sender else "Unknown"

        chat_message = {
            "message_id": str(uuid.uuid4()),
            "sender_id": str(sender_id),
            "sender_name": sender_name,
            "sender_role": sender_role,
            "message": message.strip(),
            "message_type": message_type,  # "text", "image", "file"
            "timestamp": datetime.utcnow()
        }

        result = self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {"chat_messages": chat_message},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        if result.modified_count == 0:
            raise ValueError("Message not sent")

        return chat_message

    def share_file(self, session_id, sender_id, file_name, file_url, file_type="document"):
        """Share a file during a telemedicine session."""
        if not ObjectId.is_valid(session_id) or not ObjectId.is_valid(sender_id):
            raise ValueError("Invalid ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        # Verify sender is participant in session
        if str(sender_id) != str(session["patient_id"]) and str(sender_id) != str(session["doctor_id"]):
            raise ValueError("Sender not authorized for this session")

        # Get sender role
        sender_role = "patient" if str(sender_id) == str(session["patient_id"]) else "doctor"

        # Get sender name
        sender = self.users.find_one({"_id": ObjectId(sender_id)})
        sender_name = sender.get("username", "Unknown") if sender else "Unknown"

        shared_file = {
            "file_id": str(uuid.uuid4()),
            "sender_id": str(sender_id),
            "sender_name": sender_name,
            "sender_role": sender_role,
            "file_name": file_name.strip(),
            "file_url": file_url.strip(),
            "file_type": file_type,  # "document", "image", "video", "audio"
            "uploaded_at": datetime.utcnow()
        }

        result = self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {"shared_files": shared_file},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        if result.modified_count == 0:
            raise ValueError("File not shared")

        return shared_file

    def get_session_chat_history(self, session_id):
        """Get chat history for a telemedicine session."""
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        return session.get("chat_messages", [])

    def get_session_shared_files(self, session_id):
        """Get shared files for a telemedicine session."""
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        return session.get("shared_files", [])

    def cancel_session(self, session_id, reason="Session cancelled"):
        """Cancel a telemedicine session."""
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID format")

        session = self.collection.find_one({"_id": ObjectId(session_id)})
        if not session:
            raise ValueError("Telemedicine session not found")

        if session["status"] in ["completed", "cancelled"]:
            raise ValueError("Session already completed or cancelled")

        result = self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "cancelled_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Session not cancelled")

        # Update appointment status to "cancelled"
        self.appointments.update_one(
            {"_id": session["appointment_id"]},
            {"$set": {"status": "cancelled", "cancelled_at": datetime.utcnow()}}
        )

        return {"success": True, "session_id": str(session_id)}

    def enable_recording(self, session_id, enabled=True):
        """Enable/disable session recording."""
        if not ObjectId.is_valid(session_id):
            raise ValueError("Invalid session ID format")

        result = self.collection.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "recording_enabled": bool(enabled),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Session not updated")

        return {"success": True, "recording_enabled": bool(enabled)}

    def _create_prescription(self, patient_id, doctor_id, session_id, medication_name, dosage, frequency, duration_days, notes=""):
        """Create a digital prescription."""
        if not ObjectId.is_valid(patient_id) or not ObjectId.is_valid(doctor_id):
            return None

        prescription = {
            "patient_id": ObjectId(patient_id),
            "doctor_id": ObjectId(doctor_id),
            "session_id": ObjectId(session_id),
            "medication_name": medication_name.strip(),
            "dosage": dosage.strip(),
            "frequency": frequency.strip(),
            "duration_days": int(duration_days) if duration_days else 0,
            "notes": notes.strip(),
            "status": "active",  # "active", "fulfilled", "cancelled"
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "pharmacy_id": None,
            "refill_count": 0,
            "max_refills": 0
        }

        result = self.prescriptions.insert_one(prescription)
        prescription_id = result.inserted_id

        # Also add to patient's medications
        try:
            medication = {
                "user_id": ObjectId(patient_id),
                "name": medication_name.strip(),
                "dosage": dosage.strip(),
                "frequency": frequency.strip(),
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=int(duration_days)) if duration_days else None,
                "reminders": [],
                "notes": notes.strip(),
                "refill_enabled": True if int(duration_days) > 30 else False,
                "status": "active",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "prescription_id": prescription_id
            }

            # Add medication information (side effects, interactions)
            med_info = self._get_medication_info(medication_name)
            medication["side_effects"] = med_info.get("side_effects", [])
            medication["interactions"] = med_info.get("interactions", [])

            self.medications.insert_one(medication)
        except Exception as e:
            print(f"Error adding medication: {str(e)}")

        return str(prescription_id)

    def _create_consultation_record(self, session_id, summary, prescriptions, vitals):
        """Create a health record for the consultation."""
        try:
            session = self.collection.find_one({"_id": ObjectId(session_id)})
            if not session:
                return

            consultation_record = {
                "user_id": session["patient_id"],
                "type": "consultation_summary",
                "data": {
                    "session_id": str(session_id),
                    "doctor_id": str(session["doctor_id"]),
                    "summary": summary,
                    "prescriptions": prescriptions or [],
                    "vitals": vitals or {},
                    "duration_minutes": session.get("duration_minutes", 0)
                },
                "metadata": {
                    "source": "telemedicine",
                    "appointment_id": str(session["appointment_id"])
                },
                "created_at": datetime.utcnow()
            }

            self.health_records.insert_one(consultation_record)
        except Exception as e:
            print(f"Error creating consultation record: {str(e)}")

    def _get_medication_info(self, medication_name):
        """Get medication information (side effects, interactions)."""
        # Dummy data for common medications
        medication_db = {
            "Aspirin": {
                "side_effects": ["Upset stomach", "Heartburn", "Drowsiness", "Mild headache"],
                "interactions": ["Warfarin", "Ibuprofen", "Corticosteroids", "Alcohol"]
            },
            "Ibuprofen": {
                "side_effects": ["Stomach pain", "Heartburn", "Nausea", "Dizziness"],
                "interactions": ["Aspirin", "Warfarin", "Lithium", "Blood pressure medications"]
            },
            "Paracetamol": {
                "side_effects": ["Rare: Allergic reactions", "Liver damage (overdose)"],
                "interactions": ["Alcohol", "Warfarin", "Phenytoin", "Carbamazepine"]
            },
            "Amoxicillin": {
                "side_effects": ["Nausea", "Vomiting", "Diarrhea", "Rash"],
                "interactions": ["Oral contraceptives", "Probenecid", "Allopurinol", "Warfarin"]
            },
            "Metformin": {
                "side_effects": ["Nausea", "Vomiting", "Diarrhea", "Stomach pain", "Metallic taste"],
                "interactions": ["Contrast dye", "Alcohol", "Corticosteroids", "Diuretics"]
            },
            "Lisinopril": {
                "side_effects": ["Dizziness", "Cough", "Headache", "High potassium levels"],
                "interactions": ["Potassium supplements", "NSAIDs", "Diuretics", "Lithium"]
            },
            "Atorvastatin": {
                "side_effects": ["Muscle pain", "Joint pain", "Diarrhea", "Nausea"],
                "interactions": ["Grapefruit juice", "Antifungals", "Antibiotics", "Warfarin"]
            },
            "Omeprazole": {
                "side_effects": ["Headache", "Stomach pain", "Nausea", "Diarrhea"],
                "interactions": ["Clopidogrel", "Diazepam", "Warfarin", "Methotrexate"]
            },
            "Levothyroxine": {
                "side_effects": ["Weight loss", "Heat intolerance", "Nervousness", "Insomnia"],
                "interactions": ["Calcium supplements", "Iron supplements", "Antacids", "Cholestyramine"]
            },
            "Insulin": {
                "side_effects": ["Low blood sugar", "Weight gain", "Injection site reactions"],
                "interactions": ["Beta-blockers", "ACE inhibitors", "Alcohol", "Sulfonylureas"]
            }
        }

        # Return info if medication name matches (case-insensitive)
        for key in medication_db:
            if key.lower() in medication_name.lower() or medication_name.lower() in key.lower():
                return medication_db[key]

        # Default for unknown medications
        return {
            "side_effects": ["Consult your doctor or pharmacist for side effects information"],
            "interactions": ["Consult your doctor or pharmacist for interaction information"]
        }

    def _generate_meeting_code(self):
        """Generate a secure, unique 8-character meeting code."""
        # Use a combination of letters and numbers
        characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"  # Base32 characters for readability
        code = ''.join(secrets.choice(characters) for _ in range(8))
        
        # Ensure uniqueness (check if code already exists)
        max_attempts = 10
        attempts = 0
        while self.collection.find_one({"meeting_code": code}) and attempts < max_attempts:
            code = ''.join(secrets.choice(characters) for _ in range(8))
            attempts += 1
            
        return code

    def _serialize(self, session):
        """Convert MongoDB document to JSON-serializable format."""
        if session:
            session["_id"] = str(session["_id"])
            session["appointment_id"] = str(session["appointment_id"])
            session["patient_id"] = str(session["patient_id"])
            session["doctor_id"] = str(session["doctor_id"])
            if "prescriptions_issued" in session:
                session["prescriptions_issued"] = [str(pid) for pid in session["prescriptions_issued"]]
            session["created_at"] = session["created_at"].isoformat()
            if "scheduled_start_time" in session and session["scheduled_start_time"]:
                session["scheduled_start_time"] = session["scheduled_start_time"].isoformat()
            if "started_at" in session and session["started_at"]:
                session["started_at"] = session["started_at"].isoformat()
            if "ended_at" in session and session["ended_at"]:
                session["ended_at"] = session["ended_at"].isoformat()
            if "cancelled_at" in session and session["cancelled_at"]:
                session["cancelled_at"] = session["cancelled_at"].isoformat()
            if "updated_at" in session and session["updated_at"]:
                session["updated_at"] = session["updated_at"].isoformat()
            
            # Serialize participants
            if "participants" in session:
                for key in ["patient_joined_at", "doctor_joined_at", "patient_left_at", "doctor_left_at"]:
                    if key in session["participants"] and session["participants"][key]:
                        session["participants"][key] = session["participants"][key].isoformat()
            
            # Serialize chat messages
            if "chat_messages" in session:
                for message in session["chat_messages"]:
                    if "timestamp" in message:
                        message["timestamp"] = message["timestamp"].isoformat()
            
            # Serialize shared files
            if "shared_files" in session:
                for file in session["shared_files"]:
                    if "uploaded_at" in file:
                        file["uploaded_at"] = file["uploaded_at"].isoformat()
        return session