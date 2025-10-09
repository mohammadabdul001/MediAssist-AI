from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import uuid

class LabTest:
    def __init__(self):
        self.collection = db.lab_tests
        self.users = db.users
        self.health_records = db.health_records
        self.appointments = db.appointments  # For linking to consultations

    def create_test_request(self, doctor_id, patient_id, test_name, priority="routine", 
                           notes="", sample_type="blood", home_collection=False, 
                           collection_address=None):
        """
        Doctor creates a lab test request for a patient.
        priority: "routine", "urgent", "stat"
        sample_type: "blood", "urine", "stool", "sputum", "tissue", "other"
        """
        if not ObjectId.is_valid(doctor_id) or not ObjectId.is_valid(patient_id):
            raise ValueError("Invalid user ID format")

        # Validate doctor exists and is a doctor
        doctor = self.users.find_one({"_id": ObjectId(doctor_id), "role": "doctor"})
        if not doctor:
            raise ValueError("Doctor not found or invalid role")

        # Validate patient exists
        patient = self.users.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            raise ValueError("Patient not found")

        # Validate test name
        if not test_name or not test_name.strip():
            raise ValueError("Test name is required")

        # Validate priority
        valid_priorities = ["routine", "urgent", "stat"]
        if priority not in valid_priorities:
            raise ValueError(f"Priority must be one of: {valid_priorities}")

        # Validate sample type
        valid_sample_types = ["blood", "urine", "stool", "sputum", "tissue", "other"]
        if sample_type not in valid_sample_types:
            raise ValueError(f"Sample type must be one of: {valid_sample_types}")

        lab_test = {
            "doctor_id": ObjectId(doctor_id),
            "patient_id": ObjectId(patient_id),
            "test_name": test_name.strip(),
            "priority": priority,
            "sample_type": sample_type,
            "home_collection": bool(home_collection),
            "collection_address": collection_address if home_collection else None,
            "status": "requested",  # "requested", "sample_collected", "in_progress", "completed", "cancelled"
            "notes": notes.strip(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "sample_collected_at": None,
            "completed_at": None,
            "results": {},
            "reference_ranges": {},
            "interpretation": "",
            "lab_technician_id": None,
            "test_id": str(uuid.uuid4())[:8].upper(),  # Short unique ID for lab use
            "notifications_sent": []
        }

        # Add reference ranges based on test type (in production, integrate with lab database)
        lab_test["reference_ranges"] = self._get_reference_ranges(test_name)

        result = self.collection.insert_one(lab_test)
        lab_test["_id"] = result.inserted_id
        
        # Log to health records
        self._log_to_health_record(patient_id, "lab_test_requested", lab_test)
        
        # In production: send notification to lab system
        self._send_notification(patient_id, "Lab test requested", 
                              f"Your doctor has requested a {test_name} test.")
        
        return self._serialize(lab_test)

    def get_test_by_id(self, test_id):
        """Get a single lab test by ID."""
        if not ObjectId.is_valid(test_id):
            raise ValueError("Invalid test ID")

        test = self.collection.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise ValueError("Lab test not found")

        return self._serialize(test)

    def get_patient_tests(self, patient_id, status=None):
        """Get all lab tests for a patient, optionally filtered by status."""
        if not ObjectId.is_valid(patient_id):
            raise ValueError("Invalid patient ID")

        query = {"patient_id": ObjectId(patient_id)}
        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status

        tests = self.collection.find(query).sort("created_at", -1)
        return [self._serialize(test) for test in tests]

    def get_doctor_tests(self, doctor_id, status=None):
        """Get all lab tests requested by a doctor, optionally filtered by status."""
        if not ObjectId.is_valid(doctor_id):
            raise ValueError("Invalid doctor ID")

        query = {"doctor_id": ObjectId(doctor_id)}
        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status

        tests = self.collection.find(query).sort("created_at", -1)
        return [self._serialize(test) for test in tests]

    def get_lab_technician_tests(self, technician_id, status=None):
        """Get all lab tests assigned to a lab technician, optionally filtered by status."""
        if not ObjectId.is_valid(technician_id):
            raise ValueError("Invalid technician ID")

        query = {"lab_technician_id": ObjectId(technician_id)}
        if status:
            if isinstance(status, list):
                query["status"] = {"$in": status}
            else:
                query["status"] = status

        tests = self.collection.find(query).sort("created_at", -1)
        return [self._serialize(test) for test in tests]

    def update_test_status(self, test_id, status, updated_by_id, notes=""):
        """Update the status of a lab test (e.g., sample collected, in progress, completed)."""
        if not ObjectId.is_valid(test_id) or not ObjectId.is_valid(updated_by_id):
            raise ValueError("Invalid ID format")

        test = self.collection.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise ValueError("Lab test not found")

        valid_statuses = ["requested", "sample_collected", "in_progress", "completed", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")

        update_fields = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        # Handle specific status transitions
        if status == "sample_collected" and not test.get("sample_collected_at"):
            update_fields["sample_collected_at"] = datetime.utcnow()
        elif status == "completed" and not test.get("completed_at"):
            update_fields["completed_at"] = datetime.utcnow()
            # Assign technician if not already assigned
            if not test.get("lab_technician_id"):
                update_fields["lab_technician_id"] = ObjectId(updated_by_id)

        # Add notes to history
        if notes:
            update_fields["$push"] = {
                "status_history": {
                    "status": status,
                    "changed_by": ObjectId(updated_by_id),
                    "notes": notes,
                    "changed_at": datetime.utcnow()
                }
            }

        result = self.collection.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": update_fields} if "status_history" not in update_fields else {
                "$set": {k: v for k, v in update_fields.items() if k != "$push"},
                "$push": update_fields["$push"]
            }
        )

        if result.modified_count == 0:
            raise ValueError("Lab test not updated")

        updated_test = self.collection.find_one({"_id": ObjectId(test_id)})
        
        # Log status change to health records
        self._log_to_health_record(str(updated_test["patient_id"]), "lab_test_status_updated", {
            "test_id": test_id,
            "status": status,
            "changed_by": str(updated_by_id),
            "notes": notes
        })
        
        # Send notification to patient if status is completed
        if status == "completed":
            patient = self.users.find_one({"_id": updated_test["patient_id"]})
            if patient:
                self._send_notification(str(updated_test["patient_id"]), 
                                      "Lab test results available", 
                                      f"Your {updated_test['test_name']} test results are now available.")

        return self._serialize(updated_test)

    def upload_test_results(self, test_id, technician_id, results, interpretation="", 
                           reference_ranges=None):
        """Lab technician uploads test results."""
        if not ObjectId.is_valid(test_id) or not ObjectId.is_valid(technician_id):
            raise ValueError("Invalid ID format")

        test = self.collection.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise ValueError("Lab test not found")

        # Verify technician is assigned or assign them
        if not test.get("lab_technician_id"):
            self.collection.update_one(
                {"_id": ObjectId(test_id)},
                {"$set": {"lab_technician_id": ObjectId(technician_id)}}
            )

        # Validate results format
        if not isinstance(results, dict):
            raise ValueError("Results must be a dictionary")

        update_fields = {
            "results": results,
            "interpretation": interpretation.strip(),
            "updated_at": datetime.utcnow()
        }

        if reference_ranges:
            update_fields["reference_ranges"] = reference_ranges

        result = self.collection.update_one(
            {"_id": ObjectId(test_id)},
            {"$set": update_fields}
        )

        if result.modified_count == 0:
            raise ValueError("Lab test results not updated")

        # Update status to completed if not already
        if test["status"] != "completed":
            self.update_test_status(test_id, "completed", technician_id, 
                                  "Results uploaded by lab technician")

        updated_test = self.collection.find_one({"_id": ObjectId(test_id)})
        
        # Create health record for test results
        health_record_data = {
            "test_name": updated_test["test_name"],
            "results": results,
            "interpretation": interpretation,
            "reference_ranges": reference_ranges or updated_test.get("reference_ranges", {}),
            "performed_at": datetime.utcnow(),
            "lab_technician_id": str(technician_id)
        }
        
        self.health_records.insert_one({
            "user_id": updated_test["patient_id"],
            "type": "lab_report",
            "data": health_record_data,
            "metadata": {
                "source": "lab_test",
                "test_id": str(updated_test["_id"]),
                "doctor_id": str(updated_test["doctor_id"])
            },
            "created_at": datetime.utcnow()
        })
        
        return self._serialize(updated_test)

    def cancel_test(self, test_id, cancelled_by_id, reason=""):
        """Cancel a lab test."""
        if not ObjectId.is_valid(test_id) or not ObjectId.is_valid(cancelled_by_id):
            raise ValueError("Invalid ID format")

        test = self.collection.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise ValueError("Lab test not found")

        if test["status"] in ["completed", "cancelled"]:
            raise ValueError("Cannot cancel completed or already cancelled test")

        result = self.collection.update_one(
            {"_id": ObjectId(test_id)},
            {
                "$set": {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow(),
                    "cancelled_by": ObjectId(cancelled_by_id),
                    "cancelled_reason": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count == 0:
            raise ValueError("Lab test not cancelled")

        # Log cancellation to health records
        self._log_to_health_record(str(test["patient_id"]), "lab_test_cancelled", {
            "test_id": test_id,
            "cancelled_by": str(cancelled_by_id),
            "reason": reason
        })
        
        # Send notification to patient
        self._send_notification(str(test["patient_id"]), "Lab test cancelled", 
                              f"Your {test['test_name']} test has been cancelled. Reason: {reason}")

        return {"success": True, "test_id": str(test_id)}

    def get_test_results_analysis(self, test_id):
        """Get AI-driven analysis of test results."""
        if not ObjectId.is_valid(test_id):
            raise ValueError("Invalid test ID")

        test = self.collection.find_one({"_id": ObjectId(test_id)})
        if not test:
            raise ValueError("Lab test not found")

        if test["status"] != "completed" or not test.get("results"):
            raise ValueError("Test results not available for analysis")

        # AI-driven analysis (in production, integrate with AI model)
        analysis = self._analyze_results(test["test_name"], test["results"], 
                                       test.get("reference_ranges", {}))

        return {
            "test_id": str(test["_id"]),
            "test_name": test["test_name"],
            "analysis": analysis,
            "generated_at": datetime.utcnow().isoformat(),
            "disclaimer": "This analysis is for informational purposes only and not a substitute for professional medical advice."
        }

    def _get_reference_ranges(self, test_name):
        """Get reference ranges for common tests (in production, integrate with lab database)."""
        reference_ranges = {
            "Complete Blood Count": {
                "hemoglobin": {"normal": "12.0-15.5 g/dL", "unit": "g/dL"},
                "wbc": {"normal": "4.5-11.0 K/uL", "unit": "K/uL"},
                "platelets": {"normal": "150-450 K/uL", "unit": "K/uL"}
            },
            "Blood Glucose": {
                "fasting_glucose": {"normal": "70-100 mg/dL", "unit": "mg/dL"},
                "postprandial_glucose": {"normal": "<140 mg/dL", "unit": "mg/dL"}
            },
            "Liver Function Test": {
                "alt": {"normal": "7-55 U/L", "unit": "U/L"},
                "ast": {"normal": "8-48 U/L", "unit": "U/L"},
                "bilirubin_total": {"normal": "0.1-1.2 mg/dL", "unit": "mg/dL"}
            },
            "Kidney Function Test": {
                "creatinine": {"normal": "0.6-1.2 mg/dL", "unit": "mg/dL"},
                "bun": {"normal": "7-20 mg/dL", "unit": "mg/dL"},
                "egfr": {"normal": ">90 mL/min/1.73m²", "unit": "mL/min/1.73m²"}
            },
            "Lipid Profile": {
                "total_cholesterol": {"normal": "<200 mg/dL", "unit": "mg/dL"},
                "hdl_cholesterol": {"normal": ">40 mg/dL", "unit": "mg/dL"},
                "ldl_cholesterol": {"normal": "<100 mg/dL", "unit": "mg/dL"},
                "triglycerides": {"normal": "<150 mg/dL", "unit": "mg/dL"}
            },
            "Thyroid Function Test": {
                "tsh": {"normal": "0.4-4.0 mIU/L", "unit": "mIU/L"},
                "free_t4": {"normal": "0.8-1.8 ng/dL", "unit": "ng/dL"},
                "free_t3": {"normal": "2.3-4.2 pg/mL", "unit": "pg/mL"}
            },
            "Urinalysis": {
                "protein": {"normal": "Negative", "unit": ""},
                "glucose": {"normal": "Negative", "unit": ""},
                "ketones": {"normal": "Negative", "unit": ""},
                "blood": {"normal": "Negative", "unit": ""}
            }
        }

        # Return reference ranges if test name matches (case-insensitive)
        for key in reference_ranges:
            if key.lower() in test_name.lower() or test_name.lower() in key.lower():
                return reference_ranges[key]

        return {}

    def _analyze_results(self, test_name, results, reference_ranges):
        """AI-driven analysis of test results (simplified for now, in production integrate with AI model)."""
        analysis = {
            "summary": "",
            "abnormal_values": [],
            "recommendations": [],
            "risk_assessment": "normal"
        }

        # Simple rule-based analysis
        if "Complete Blood Count" in test_name:
            if "hemoglobin" in results:
                value = float(str(results["hemoglobin"]).split()[0])
                if value < 12.0:
                    analysis["abnormal_values"].append({
                        "parameter": "hemoglobin",
                        "value": results["hemoglobin"],
                        "status": "low",
                        "interpretation": "Possible anemia"
                    })
                    analysis["recommendations"].append("Consult your doctor about possible iron deficiency or other causes of anemia.")
                    analysis["risk_assessment"] = "moderate"
                elif value > 15.5:
                    analysis["abnormal_values"].append({
                        "parameter": "hemoglobin",
                        "value": results["hemoglobin"],
                        "status": "high",
                        "interpretation": "Possible polycythemia"
                    })
                    analysis["recommendations"].append("Consult your doctor about possible causes of elevated hemoglobin.")
                    analysis["risk_assessment"] = "moderate"

        elif "Blood Glucose" in test_name:
            if "fasting_glucose" in results:
                value = float(str(results["fasting_glucose"]).split()[0])
                if value < 70:
                    analysis["abnormal_values"].append({
                        "parameter": "fasting_glucose",
                        "value": results["fasting_glucose"],
                        "status": "low",
                        "interpretation": "Hypoglycemia"
                    })
                    analysis["recommendations"].append("If experiencing symptoms, consume 15-20 grams of fast-acting carbohydrates and recheck blood sugar after 15 minutes.")
                    analysis["risk_assessment"] = "high"
                elif value > 100:
                    analysis["abnormal_values"].append({
                        "parameter": "fasting_glucose",
                        "value": results["fasting_glucose"],
                        "status": "high",
                        "interpretation": "Possible prediabetes or diabetes"
                    })
                    analysis["recommendations"].append("Consult your doctor for further evaluation and possible HbA1c test.")
                    analysis["risk_assessment"] = "moderate"

        # Generate summary
        if len(analysis["abnormal_values"]) == 0:
            analysis["summary"] = "All test results are within normal ranges."
            analysis["recommendations"].append("Continue with your current health regimen.")
        else:
            analysis["summary"] = f"Found {len(analysis['abnormal_values'])} abnormal value(s) in your test results."

        return analysis

    def _send_notification(self, user_id, title, message):
        """Send notification to user (stub for actual notification service)."""
        try:
            # In production: integrate with Firebase Cloud Messaging, Twilio, etc.
            notification = {
                "user_id": ObjectId(user_id),
                "title": title,
                "message": message,
                "type": "lab_test",
                "sent_at": datetime.utcnow(),
                "read": False
            }
            db.notifications.insert_one(notification)
            
            # Add to test notifications_sent array
            # This would be done in the calling function
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")

    def _log_to_health_record(self, user_id, event_type, data):
        """Log lab test events to health records."""
        try:
            record = {
                "user_id": ObjectId(user_id),
                "type": "lab_test_event",
                "event_type": event_type,
                "data": data,
                "created_at": datetime.utcnow()
            }
            self.health_records.insert_one(record)
        except Exception as e:
            print(f"Failed to log lab test event: {str(e)}")

    def _serialize(self, test):
        """Convert MongoDB document to JSON-serializable format."""
        if test:
            test["_id"] = str(test["_id"])
            test["doctor_id"] = str(test["doctor_id"])
            test["patient_id"] = str(test["patient_id"])
            if "lab_technician_id" in test and test["lab_technician_id"]:
                test["lab_technician_id"] = str(test["lab_technician_id"])
            if "cancelled_by" in test and test["cancelled_by"]:
                test["cancelled_by"] = str(test["cancelled_by"])
            test["created_at"] = test["created_at"].isoformat()
            test["updated_at"] = test["updated_at"].isoformat()
            if "sample_collected_at" in test and test["sample_collected_at"]:
                test["sample_collected_at"] = test["sample_collected_at"].isoformat()
            if "completed_at" in test and test["completed_at"]:
                test["completed_at"] = test["completed_at"].isoformat()
            if "cancelled_at" in test and test["cancelled_at"]:
                test["cancelled_at"] = test["cancelled_at"].isoformat()
            
            # Serialize status history
            if "status_history" in test:
                for status_change in test["status_history"]:
                    if "changed_by" in status_change:
                        status_change["changed_by"] = str(status_change["changed_by"])
                    if "changed_at" in status_change:
                        status_change["changed_at"] = status_change["changed_at"].isoformat()
        return test