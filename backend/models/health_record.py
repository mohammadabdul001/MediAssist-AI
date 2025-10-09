from datetime import datetime
from bson import ObjectId
from .db import db
import json

class HealthRecord:
    def __init__(self):
        self.collection = db.health_records
        self.users = db.users

    def create_record(self, user_id, record_type, data, metadata=None, shared_with=None):
        """
        Create a new health record for a user.
        record_type: 'lab_report', 'diagnosis', 'prescription', 'vitals', 'medical_history', 'allergy', 'vaccination'
        data: dict containing actual health data
        metadata: optional dict (source, device, etc.)
        shared_with: list of doctor user IDs with permissions
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        record = {
            "user_id": ObjectId(user_id),
            "type": record_type,
            "data": data,
            "metadata": metadata or {},
            "shared_with": shared_with or [],  # [{"doctor_id": ObjectId, "permissions": ["view"], "shared_at": datetime}]
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_deleted": False
        }

        result = self.collection.insert_one(record)
        record["_id"] = result.inserted_id
        return self._serialize(record)

    def get_user_records(self, user_id, record_type=None, include_deleted=False):
        """Get all health records for a user, optionally filtered by type."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        query = {"user_id": ObjectId(user_id)}
        if not include_deleted:
            query["is_deleted"] = False
        if record_type:
            query["type"] = record_type

        records = self.collection.find(query).sort("created_at", -1)
        return [self._serialize(record) for record in records]

    def get_shared_records_for_doctor(self, doctor_id):
        """Get all records shared with this doctor."""
        if not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid doctor ID format")

        # Find records where this doctor is in shared_with list
        query = {
            "shared_with": {
                "$elemMatch": {
                    "doctor_id": ObjectId(doctor_id),
                    "permissions": {"$in": ["view", "edit"]}
                }
            },
            "is_deleted": False
        }

        records = self.collection.find(query).sort("created_at", -1)
        return [self._serialize(record) for record in records]

    def share_record_with_doctor(self, record_id, doctor_id, permissions=None):
        """Share a record with a doctor."""
        if not ObjectId.is_valid(record_id) or not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid ID format")

        permissions = permissions or ["view"]
        if not isinstance(permissions, list):
            permissions = [permissions]

        # Validate doctor exists and is a doctor
        doctor = self.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor"})
        if not doctor:
            raise ValueError("Doctor not found or invalid role")

        update = {
            "$addToSet": {
                "shared_with": {
                    "doctor_id": ObjectId(doctor_id),
                    "permissions": permissions,
                    "shared_at": datetime.utcnow()
                }
            },
            "$set": {"updated_at": datetime.utcnow()}
        }

        result = self.collection.update_one(
            {"_id": ObjectId(record_id), "is_deleted": False},
            update
        )

        if result.modified_count == 0:
            raise ValueError("Record not found or already shared")

        return {"success": True, "record_id": str(record_id), "doctor_id": str(doctor_id)}

    def revoke_doctor_access(self, record_id, doctor_id):
        """Remove doctor's access to a record."""
        if not ObjectId.is_valid(record_id) or not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid ID format")

        result = self.collection.update_one(
            {"_id": ObjectId(record_id)},
            {
                "$pull": {"shared_with": {"doctor_id": ObjectId(doctor_id)}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )

        return {"success": True, "records_modified": result.modified_count}

    def update_record(self, record_id, data=None, metadata=None):
        """Update record data or metadata."""
        if not ObjectId.is_valid(record_id):
            raise ValueError("Invalid record ID")

        update_fields = {"updated_at": datetime.utcnow()}
        if data is not None:
            update_fields["data"] = data
        if metadata is not None:
            update_fields["metadata"] = metadata

        result = self.collection.update_one(
            {"_id": ObjectId(record_id), "is_deleted": False},
            {"$set": update_fields}
        )

        if result.modified_count == 0:
            raise ValueError("Record not found or not updated")

        updated_record = self.collection.find_one({"_id": ObjectId(record_id)})
        return self._serialize(updated_record)

    def soft_delete_record(self, record_id):
        """Soft delete a record (mark as deleted)."""
        if not ObjectId.is_valid(record_id):
            raise ValueError("Invalid record ID")

        result = self.collection.update_one(
            {"_id": ObjectId(record_id)},
            {"$set": {"is_deleted": True, "deleted_at": datetime.utcnow()}}
        )

        if result.modified_count == 0:
            raise ValueError("Record not found")

        return {"success": True, "record_id": str(record_id)}

    def hard_delete_record(self, record_id):
        """Permanently delete a record (for compliance/GDPR)."""
        if not ObjectId.is_valid(record_id):
            raise ValueError("Invalid record ID")

        result = self.collection.delete_one({"_id": ObjectId(record_id)})
        return {"success": True, "deleted_count": result.deleted_count}

    def generate_pdf_summary(self, record_id):
        """
        Generate a printable PDF summary of the record.
        In production, use libraries like ReportLab or WeasyPrint.
        For now, return structured JSON that can be converted to PDF.
        """
        if not ObjectId.is_valid(record_id):
            raise ValueError("Invalid record ID")

        record = self.collection.find_one({"_id": ObjectId(record_id), "is_deleted": False})
        if not record:
            raise ValueError("Record not found")

        # Get user info
        user = self.users.find_one({"_id": record["user_id"]}, {"username": 1, "profile": 1})

        summary = {
            "record_id": str(record["_id"]),
            "patient_name": user.get("username", "Unknown") if user else "Unknown",
            "patient_contact": user.get("profile", {}).get("phone", "") if user else "",
            "record_type": record["type"],
            "created_at": record["created_at"].isoformat(),
            "data": record["data"],
            "metadata": record["metadata"],
            "generated_at": datetime.utcnow().isoformat(),
            "disclaimer": "This is a summary of health record. Not a substitute for professional medical advice."
        }

        return summary

    def _serialize(self, record):
        """Convert MongoDB document to JSON-serializable format."""
        if record:
            record["_id"] = str(record["_id"])
            record["user_id"] = str(record["user_id"])
            # Serialize doctor IDs in shared_with
            if "shared_with" in record:
                for item in record["shared_with"]:
                    if "doctor_id" in item:
                        item["doctor_id"] = str(item["doctor_id"])
                    if "shared_at" in item:
                        item["shared_at"] = item["shared_at"].isoformat()
            if "created_at" in record:
                record["created_at"] = record["created_at"].isoformat()
            if "updated_at" in record:
                record["updated_at"] = record["updated_at"].isoformat()
            if "deleted_at" in record:
                record["deleted_at"] = record["deleted_at"].isoformat()
        return record