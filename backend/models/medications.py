from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import pytz

class Medication:
    def __init__(self):
        self.collection = db.medications
        self.users = db.users
        self.health_records = db.health_records  # For logging
        self.pharmacy_integration = None  # Will integrate with pharmacy API later

    def add_medication(self, user_id, name, dosage, frequency, start_date, end_date=None, 
                      reminders=None, notes="", refill_enabled=False, pharmacy_id=None):
        """
        Add a new medication for a user.
        frequency: e.g., "once daily", "twice daily", "every 8 hours"
        reminders: list of times in "HH:MM" format, e.g., ["08:00", "20:00"]
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        # Validate user exists
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Validate dates
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date and isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if start_date < datetime.utcnow():
            raise ValueError("Start date cannot be in the past")

        # Validate reminders format
        validated_reminders = []
        if reminders:
            for reminder in reminders:
                try:
                    # Validate time format
                    datetime.strptime(reminder, "%H:%M")
                    validated_reminders.append(reminder)
                except ValueError:
                    raise ValueError(f"Invalid reminder time format: {reminder}. Use HH:MM format.")

        medication = {
            "user_id": ObjectId(user_id),
            "name": name.strip(),
            "dosage": dosage.strip(),
            "frequency": frequency.strip(),
            "start_date": start_date,
            "end_date": end_date,
            "reminders": validated_reminders,
            "notes": notes.strip(),
            "refill_enabled": bool(refill_enabled),
            "pharmacy_id": pharmacy_id,
            "status": "active",  # "active", "completed", "discontinued"
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_taken": None,
            "missed_doses": 0,
            "total_doses": 0,
            "side_effects": [],
            "interactions": []
        }

        # Add medication information (side effects, interactions) - in production, integrate with drug database
        med_info = self._get_medication_info(name)
        medication["side_effects"] = med_info.get("side_effects", [])
        medication["interactions"] = med_info.get("interactions", [])

        result = self.collection.insert_one(medication)
        medication["_id"] = result.inserted_id
        
        # Log to health records
        self._log_to_health_record(user_id, "medication_added", medication)
        
        return self._serialize(medication)

    def get_user_medications(self, user_id, status=None):
        """Get all medications for a user, optionally filtered by status."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        query = {"user_id": ObjectId(user_id)}
        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status

        medications = self.collection.find(query).sort("start_date", -1)
        return [self._serialize(med) for med in medications]

    def get_medication(self, medication_id):
        """Get a single medication by ID."""
        if not ObjectId.is_valid(medication_id):
            raise ValueError("Invalid medication ID")

        medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            raise ValueError("Medication not found")

        return self._serialize(medication)

    def update_medication(self, medication_id, updates):
        """Update medication details."""
        if not ObjectId.is_valid(medication_id):
            raise ValueError("Invalid medication ID")

        medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            raise ValueError("Medication not found")

        update_fields = {"updated_at": datetime.utcnow()}
        allowed_fields = ["name", "dosage", "frequency", "start_date", "end_date", 
                         "reminders", "notes", "refill_enabled", "pharmacy_id", "status"]

        for field in allowed_fields:
            if field in updates:
                if field in ["start_date", "end_date"]:
                    if isinstance(updates[field], str):
                        update_fields[field] = datetime.fromisoformat(updates[field].replace('Z', '+00:00'))
                    else:
                        update_fields[field] = updates[field]
                elif field == "reminders":
                    # Validate reminder times
                    validated_reminders = []
                    for reminder in updates[field]:
                        try:
                            datetime.strptime(reminder, "%H:%M")
                            validated_reminders.append(reminder)
                        except ValueError:
                            raise ValueError(f"Invalid reminder time format: {reminder}. Use HH:MM format.")
                    update_fields[field] = validated_reminders
                else:
                    update_fields[field] = updates[field]

        result = self.collection.update_one(
            {"_id": ObjectId(medication_id)},
            {"$set": update_fields}
        )

        if result.modified_count == 0:
            raise ValueError("Medication not updated")

        updated_medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        
        # Log update to health records
        self._log_to_health_record(str(updated_medication["user_id"]), "medication_updated", updated_medication)
        
        return self._serialize(updated_medication)

    def log_dose_taken(self, medication_id, taken_at=None, notes=""):
        """Log that a dose was taken."""
        if not ObjectId.is_valid(medication_id):
            raise ValueError("Invalid medication ID")

        taken_at = taken_at or datetime.utcnow()
        if isinstance(taken_at, str):
            taken_at = datetime.fromisoformat(taken_at.replace('Z', '+00:00'))

        result = self.collection.update_one(
            {"_id": ObjectId(medication_id)},
            {
                "$set": {
                    "last_taken": taken_at,
                    "updated_at": datetime.utcnow()
                },
                "$inc": {
                    "total_doses": 1,
                    "missed_doses": 0  # Reset missed doses when taken
                },
                "$push": {
                    "dose_history": {
                        "taken_at": taken_at,
                        "notes": notes,
                        "logged_at": datetime.utcnow()
                    }
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Medication not found or not updated")

        medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        
        # Log to health records
        self._log_to_health_record(str(medication["user_id"]), "dose_taken", {
            "medication_id": medication_id,
            "taken_at": taken_at,
            "notes": notes
        })
        
        return {"success": True, "medication_id": str(medication_id), "taken_at": taken_at.isoformat()}

    def mark_missed_dose(self, medication_id, missed_at=None, reason=""):
        """Mark a dose as missed."""
        if not ObjectId.is_valid(medication_id):
            raise ValueError("Invalid medication ID")

        missed_at = missed_at or datetime.utcnow()
        if isinstance(missed_at, str):
            missed_at = datetime.fromisoformat(missed_at.replace('Z', '+00:00'))

        result = self.collection.update_one(
            {"_id": ObjectId(medication_id)},
            {
                "$inc": {
                    "missed_doses": 1
                },
                "$push": {
                    "missed_dose_history": {
                        "missed_at": missed_at,
                        "reason": reason,
                        "logged_at": datetime.utcnow()
                    }
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Medication not found or not updated")

        medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        
        # Log to health records
        self._log_to_health_record(str(medication["user_id"]), "dose_missed", {
            "medication_id": medication_id,
            "missed_at": missed_at,
            "reason": reason
        })
        
        return {"success": True, "medication_id": str(medication_id), "missed_at": missed_at.isoformat()}

    def request_refill(self, medication_id, quantity=1, pharmacy_id=None):
        """Request a refill for medication (integrates with pharmacy system)."""
        if not ObjectId.is_valid(medication_id):
            raise ValueError("Invalid medication ID")

        medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            raise ValueError("Medication not found")

        if not medication.get("refill_enabled", False):
            raise ValueError("Refill is not enabled for this medication")

        # In production: integrate with pharmacy API
        # For now, simulate pharmacy integration
        pharmacy_response = {
            "status": "pending",  # "pending", "approved", "rejected"
            "pharmacy_id": pharmacy_id or medication.get("pharmacy_id"),
            "quantity": quantity,
            "requested_at": datetime.utcnow(),
            "estimated_fulfillment_time": datetime.utcnow() + timedelta(days=2)
        }

        # Update medication with refill request
        result = self.collection.update_one(
            {"_id": ObjectId(medication_id)},
            {
                "$push": {
                    "refill_requests": pharmacy_response
                },
                "$set": {
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Medication not updated")

        # Log to health records
        self._log_to_health_record(str(medication["user_id"]), "refill_requested", pharmacy_response)
        
        return {
            "success": True,
            "medication_id": str(medication_id),
            "refill_request": pharmacy_response
        }

    def discontinue_medication(self, medication_id, reason="", discontinued_at=None):
        """Discontinue a medication."""
        if not ObjectId.is_valid(medication_id):
            raise ValueError("Invalid medication ID")

        discontinued_at = discontinued_at or datetime.utcnow()
        if isinstance(discontinued_at, str):
            discontinued_at = datetime.fromisoformat(discontinued_at.replace('Z', '+00:00'))

        result = self.collection.update_one(
            {"_id": ObjectId(medication_id)},
            {
                "$set": {
                    "status": "discontinued",
                    "discontinued_at": discontinued_at,
                    "discontinued_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Medication not found or not updated")

        medication = self.collection.find_one({"_id": ObjectId(medication_id)})
        
        # Log to health records
        self._log_to_health_record(str(medication["user_id"]), "medication_discontinued", {
            "medication_id": medication_id,
            "reason": reason,
            "discontinued_at": discontinued_at
        })
        
        return {"success": True, "medication_id": str(medication_id)}

    def get_reminders_for_today(self, user_id):
        """Get all medication reminders for today for a user."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

        # Get current time and extract hour:minute
        now = datetime.utcnow()
        current_time_str = now.strftime("%H:%M")

        # Get active medications with reminders
        medications = self.collection.find({
            "user_id": ObjectId(user_id),
            "status": "active",
            "start_date": {"$lte": now},
            "$or": [
                {"end_date": {"$gte": now}},
                {"end_date": None}
            ],
            "reminders": {"$ne": []}
        })

        reminders = []
        for med in medications:
            for reminder_time in med.get("reminders", []):
                # Check if this reminder should trigger (within 5 minutes)
                reminder_hour, reminder_minute = map(int, reminder_time.split(":"))
                reminder_datetime = now.replace(hour=reminder_hour, minute=reminder_minute, second=0, microsecond=0)
                
                # Check if within 5 minutes of current time
                time_diff = abs((now - reminder_datetime).total_seconds())
                if time_diff <= 300:  # 5 minutes in seconds
                    reminders.append({
                        "medication_id": str(med["_id"]),
                        "name": med["name"],
                        "dosage": med["dosage"],
                        "reminder_time": reminder_time,
                        "scheduled_for": reminder_datetime.isoformat()
                    })

        return reminders

    def _get_medication_info(self, medication_name):
        """
        Get medication information (side effects, interactions).
        In production, integrate with drug database API (e.g., RxNorm, Drugs.com API).
        For now, return dummy data based on common medications.
        """
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

    def _log_to_health_record(self, user_id, event_type, data):
        """Log medication events to health records."""
        try:
            record = {
                "user_id": ObjectId(user_id),
                "type": "medication_event",
                "event_type": event_type,
                "data": data,
                "created_at": datetime.utcnow()
            }
            self.health_records.insert_one(record)
        except Exception as e:
            # Don't fail the main operation if logging fails
            print(f"Failed to log medication event: {str(e)}")

    def _serialize(self, medication):
        """Convert MongoDB document to JSON-serializable format."""
        if medication:
            medication["_id"] = str(medication["_id"])
            medication["user_id"] = str(medication["user_id"])
            medication["start_date"] = medication["start_date"].isoformat()
            if "end_date" in medication and medication["end_date"]:
                medication["end_date"] = medication["end_date"].isoformat()
            if "last_taken" in medication and medication["last_taken"]:
                medication["last_taken"] = medication["last_taken"].isoformat()
            if "discontinued_at" in medication and medication["discontinued_at"]:
                medication["discontinued_at"] = medication["discontinued_at"].isoformat()
            if "created_at" in medication:
                medication["created_at"] = medication["created_at"].isoformat()
            if "updated_at" in medication:
                medication["updated_at"] = medication["updated_at"].isoformat()
            
            # Serialize dose history
            if "dose_history" in medication:
                for dose in medication["dose_history"]:
                    if "taken_at" in dose:
                        dose["taken_at"] = dose["taken_at"].isoformat()
                    if "logged_at" in dose:
                        dose["logged_at"] = dose["logged_at"].isoformat()
            
            # Serialize missed dose history
            if "missed_dose_history" in medication:
                for missed in medication["missed_dose_history"]:
                    if "missed_at" in missed:
                        missed["missed_at"] = missed["missed_at"].isoformat()
                    if "logged_at" in missed:
                        missed["logged_at"] = missed["logged_at"].isoformat()
            
            # Serialize refill requests
            if "refill_requests" in medication:
                for refill in medication["refill_requests"]:
                    if "requested_at" in refill:
                        refill["requested_at"] = refill["requested_at"].isoformat()
                    if "estimated_fulfillment_time" in refill:
                        refill["estimated_fulfillment_time"] = refill["estimated_fulfillment_time"].isoformat()
        return medication