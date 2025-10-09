from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import pytz

class Appointment:
    def __init__(self):
        self.collection = db.appointments
        self.users = db.users
        self.telemedicine = db.telemedicine_sessions  # For future integration

    def create_appointment(self, patient_id, doctor_id, start_time, end_time, appointment_type="in_person", fee=0.0, notes=""):
        """
        Create a new appointment.
        appointment_type: "in_person" or "video"
        """
        if not ObjectId.is_valid(patient_id) or not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid user ID format")

        # Validate doctor exists and is a doctor
        doctor = self.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor"})
        if not doctor:
            raise ValueError("Doctor not found or invalid role")

        # Validate patient exists
        patient = self.users.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            raise ValueError("Patient not found")

        # Validate time format and logic
        if start_time >= end_time:
            raise ValueError("End time must be after start time")
        if (end_time - start_time).total_seconds() < 600:  # Minimum 10 minutes
            raise ValueError("Appointment must be at least 10 minutes long")
        if start_time < datetime.utcnow():
            raise ValueError("Cannot schedule appointment in the past")

        # Check for time conflicts for doctor
        conflict = self.collection.find_one({
            "doctor_id": ObjectId(doctor_id),
            "status": {"$in": ["scheduled", "confirmed", "in_progress"]},
            "$or": [
                {"start_time": {"$lt": end_time, "$gte": start_time}},
                {"end_time": {"$gt": start_time, "$lte": end_time}},
                {"start_time": {"$lte": start_time}, "end_time": {"$gte": end_time}}
            ]
        })
        if conflict:
            raise ValueError("Doctor is not available at this time")

        appointment = {
            "patient_id": ObjectId(patient_id),
            "doctor_id": ObjectId(doctor_id),
            "start_time": start_time,
            "end_time": end_time,
            "type": appointment_type,  # "in_person" or "video"
            "fee": float(fee),
            "payment_status": "pending",  # "pending", "paid", "refunded"
            "status": "scheduled",  # "scheduled", "confirmed", "cancelled", "completed", "no_show"
            "notes": notes,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "reminders_sent": [],
            "telemedicine_session_id": None  # Will be populated if video
        }

        result = self.collection.insert_one(appointment)
        appointment["_id"] = result.inserted_id
        return self._serialize(appointment)

    def get_appointment(self, appointment_id):
        """Get a single appointment by ID."""
        if not ObjectId.is_valid(appointment_id):
            raise ValueError("Invalid appointment ID")

        appointment = self.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise ValueError("Appointment not found")

        return self._serialize(appointment)

    def get_user_appointments(self, user_id, role="patient", status=None):
        """Get appointments for a user (as patient or doctor)."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID")

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

        appointments = self.collection.find(query).sort("start_time", 1)
        return [self._serialize(app) for app in appointments]

    def get_doctor_availability(self, doctor_id, date):
        """Get available time slots for a doctor on a specific date."""
        if not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid doctor ID")

        # Validate doctor exists
        doctor = self.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor"})
        if not doctor:
            raise ValueError("Doctor not found")

        # Define working hours (9 AM to 5 PM)
        start_of_day = datetime.combine(date, datetime.min.time()) + timedelta(hours=9)
        end_of_day = datetime.combine(date, datetime.min.time()) + timedelta(hours=17)

        # Get all booked appointments for that day
        booked = self.collection.find({
            "doctor_id": ObjectId(doctor_id),
            "start_time": {"$gte": start_of_day, "$lt": end_of_day},
            "status": {"$in": ["scheduled", "confirmed"]}
        })

        booked_slots = []
        for appt in booked:
            booked_slots.append({
                "start": appt["start_time"],
                "end": appt["end_time"]
            })

        # Generate 30-minute slots
        available_slots = []
        current = start_of_day
        while current < end_of_day:
            slot_end = current + timedelta(minutes=30)
            if slot_end > end_of_day:
                break

            # Check for conflicts
            is_available = True
            for booked in booked_slots:
                if not (slot_end <= booked["start"] or current >= booked["end"]):
                    is_available = False
                    break

            if is_available:
                available_slots.append({
                    "start_time": current.isoformat(),
                    "end_time": slot_end.isoformat()
                })

            current = slot_end

        return available_slots

    def update_appointment(self, appointment_id, updates):
        """Update appointment (reschedule, change type, etc.)."""
        if not ObjectId.is_valid(appointment_id):
            raise ValueError("Invalid appointment ID")

        appointment = self.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise ValueError("Appointment not found")

        # Prevent updating completed/cancelled appointments
        if appointment["status"] in ["completed", "cancelled", "no_show"]:
            raise ValueError("Cannot update completed or cancelled appointment")

        update_fields = {"updated_at": datetime.utcnow()}
        allowed_fields = ["start_time", "end_time", "type", "fee", "notes", "status"]

        for field in allowed_fields:
            if field in updates:
                if field in ["start_time", "end_time"]:
                    update_fields[field] = updates[field]
                else:
                    update_fields[field] = updates[field]

        # If rescheduling, check for conflicts
        if "start_time" in update_fields or "end_time" in update_fields:
            start = update_fields.get("start_time", appointment["start_time"])
            end = update_fields.get("end_time", appointment["end_time"])
            
            if start >= end:
                raise ValueError("End time must be after start time")
            if start < datetime.utcnow():
                raise ValueError("Cannot reschedule to a past time")

            # Check for conflicts
            conflict = self.collection.find_one({
                "doctor_id": appointment["doctor_id"],
                "_id": {"$ne": ObjectId(appointment_id)},  # Exclude self
                "status": {"$in": ["scheduled", "confirmed", "in_progress"]},
                "$or": [
                    {"start_time": {"$lt": end, "$gte": start}},
                    {"end_time": {"$gt": start, "$lte": end}},
                    {"start_time": {"$lte": start}, "end_time": {"$gte": end}}
                ]
            })
            if conflict:
                raise ValueError("Doctor is not available at the new time")

        result = self.collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": update_fields}
        )

        if result.modified_count == 0:
            raise ValueError("Appointment not updated")

        updated_appointment = self.collection.find_one({"_id": ObjectId(appointment_id)})
        return self._serialize(updated_appointment)

    def cancel_appointment(self, appointment_id, reason="User cancelled"):
        """Cancel an appointment."""
        if not ObjectId.is_valid(appointment_id):
            raise ValueError("Invalid appointment ID")

        appointment = self.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise ValueError("Appointment not found")

        if appointment["status"] in ["completed", "cancelled", "no_show"]:
            raise ValueError("Cannot cancel completed or already cancelled appointment")

        result = self.collection.update_one(
            {"_id": ObjectId(appointment_id)},
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
            raise ValueError("Appointment not cancelled")

        return {"success": True, "appointment_id": str(appointment_id)}

    def confirm_appointment(self, appointment_id):
        """Confirm an appointment (usually done by doctor or system)."""
        if not ObjectId.is_valid(appointment_id):
            raise ValueError("Invalid appointment ID")

        appointment = self.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise ValueError("Appointment not found")

        if appointment["status"] != "scheduled":
            raise ValueError("Only scheduled appointments can be confirmed")

        result = self.collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$set": {
                    "status": "confirmed",
                    "confirmed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Appointment not confirmed")

        # If video appointment, create telemedicine session
        if appointment["type"] == "video":
            tele_session = {
                "appointment_id": ObjectId(appointment_id),
                "patient_id": appointment["patient_id"],
                "doctor_id": appointment["doctor_id"],
                "session_id": str(ObjectId()),
                "meeting_link": f"https://mediassist.ai/meet/{str(ObjectId())[:8]}",
                "status": "scheduled",
                "created_at": datetime.utcnow()
            }
            self.telemedicine.insert_one(tele_session)

        return {"success": True, "appointment_id": str(appointment_id)}

    def mark_completed(self, appointment_id, notes=""):
        """Mark appointment as completed."""
        if not ObjectId.is_valid(appointment_id):
            raise ValueError("Invalid appointment ID")

        result = self.collection.update_one(
            {"_id": ObjectId(appointment_id), "status": {"$in": ["scheduled", "confirmed", "in_progress"]}},
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "completion_notes": notes,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Appointment not found or cannot be completed")

        return {"success": True, "appointment_id": str(appointment_id)}

    def send_reminder(self, appointment_id, reminder_type="email"):
        """Send reminder for appointment (stub for actual email/SMS service)."""
        if not ObjectId.is_valid(appointment_id):
            raise ValueError("Invalid appointment ID")

        appointment = self.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            raise ValueError("Appointment not found")

        if appointment["status"] not in ["scheduled", "confirmed"]:
            raise ValueError("Cannot send reminder for non-active appointment")

        # In production: integrate with SendGrid, Twilio, etc.
        reminder_data = {
            "type": reminder_type,
            "sent_at": datetime.utcnow(),
            "message": f"Reminder: Your appointment with Dr. [NAME] is scheduled for {appointment['start_time'].strftime('%Y-%m-%d %H:%M')}"
        }

        result = self.collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {
                "$push": {"reminders_sent": reminder_data},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return {"success": True, "reminder_sent": reminder_data}

    def _serialize(self, appointment):
        """Convert MongoDB document to JSON-serializable format."""
        if appointment:
            appointment["_id"] = str(appointment["_id"])
            appointment["patient_id"] = str(appointment["patient_id"])
            appointment["doctor_id"] = str(appointment["doctor_id"])
            appointment["start_time"] = appointment["start_time"].isoformat()
            appointment["end_time"] = appointment["end_time"].isoformat()
            appointment["created_at"] = appointment["created_at"].isoformat()
            appointment["updated_at"] = appointment["updated_at"].isoformat()
            if "cancelled_at" in appointment:
                appointment["cancelled_at"] = appointment["cancelled_at"].isoformat()
            if "confirmed_at" in appointment:
                appointment["confirmed_at"] = appointment["confirmed_at"].isoformat()
            if "completed_at" in appointment:
                appointment["completed_at"] = appointment["completed_at"].isoformat()
        return appointment