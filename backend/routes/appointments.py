from flask import Blueprint, request, jsonify
from models.appointments import Appointment
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('appointments', __name__)
appointment_manager = Appointment()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if ' ' in auth_header:
                token = auth_header.split(" ")[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = User.find_by_username(data['username'])
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def patient_or_doctor_required(f):
    """Decorator to allow access if user is patient (owner) or doctor"""
    @wraps(f)
    def decorated(current_user, appointment_id, *args, **kwargs):
        try:
            appointment = appointment_manager.collection.find_one({"_id": ObjectId(appointment_id)})
            if not appointment:
                return jsonify({"error": "Appointment not found"}), 404

            # Allow if user is the patient
            if str(current_user['_id']) == str(appointment['patient_id']):
                return f(current_user, appointment_id, *args, **kwargs)

            # Allow if user is the doctor
            if str(current_user['_id']) == str(appointment['doctor_id']):
                return f(current_user, appointment_id, *args, **kwargs)

            return jsonify({"error": "Access denied"}), 403

        except Exception as e:
            return jsonify({"error": "Invalid appointment ID"}), 400
    return decorated

@bp.route('/api/appointments', methods=['POST'])
@token_required
def create_appointment(current_user):
    """Create a new appointment (patient initiates)."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'doctor_id' not in data:
            return jsonify({"error": "'doctor_id' is required"}), 400
        if 'start_time' not in data or 'end_time' not in data:
            return jsonify({"error": "'start_time' and 'end_time' are required (ISO format)"}), 400

        # Parse datetime
        try:
            start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid datetime format. Use ISO format (e.g., 2025-04-01T09:00:00Z)"}), 400

        # Create appointment
        appointment = appointment_manager.create_appointment(
            patient_id=str(current_user['_id']),
            doctor_id=data['doctor_id'],
            start_time=start_time,
            end_time=end_time,
            appointment_type=data.get('type', 'in_person'),
            fee=float(data.get('fee', 0.0)),
            notes=data.get('notes', '')
        )

        return jsonify({
            "message": "Appointment created successfully",
            "appointment": appointment
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error creating appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/<appointment_id>', methods=['GET'])
@token_required
@patient_or_doctor_required
def get_appointment(current_user, appointment_id):
    """Get a single appointment by ID."""
    try:
        appointment = appointment_manager.get_appointment(appointment_id)
        return jsonify({
            "appointment": appointment
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error fetching appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments', methods=['GET'])
@token_required
def get_user_appointments(current_user):
    """Get all appointments for the current user (as patient or doctor)."""
    try:
        role = request.args.get('role', 'patient')
        status = request.args.get('status')
        
        if status:
            status = status.split(',')  # Allow multiple statuses

        appointments = appointment_manager.get_user_appointments(
            user_id=str(current_user['_id']),
            role=role,
            status=status
        )

        return jsonify({
            "count": len(appointments),
            "appointments": appointments
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching user appointments: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/doctor/<doctor_id>/availability', methods=['GET'])
@token_required
def get_doctor_availability(current_user, doctor_id):
    """Get available time slots for a doctor on a specific date."""
    try:
        date_str = request.args.get('date')
        if not date_str:
            return jsonify({"error": "Date parameter is required (YYYY-MM-DD)"}), 400

        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        available_slots = appointment_manager.get_doctor_availability(doctor_id, date)

        return jsonify({
            "doctor_id": doctor_id,
            "date": date_str,
            "available_slots": available_slots
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching doctor availability: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/<appointment_id>', methods=['PUT'])
@token_required
@patient_or_doctor_required
def update_appointment(current_user, appointment_id):
    """Update an appointment (reschedule, change type, etc.)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Parse datetime if provided
        updates = {}
        for key in ['start_time', 'end_time', 'type', 'fee', 'notes', 'status']:
            if key in data:
                if key in ['start_time', 'end_time']:
                    try:
                        updates[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": f"Invalid {key} format"}), 400
                else:
                    updates[key] = data[key]

        updated_appointment = appointment_manager.update_appointment(appointment_id, updates)

        return jsonify({
            "message": "Appointment updated successfully",
            "appointment": updated_appointment
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error updating appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/<appointment_id>/cancel', methods=['POST'])
@token_required
@patient_or_doctor_required
def cancel_appointment(current_user, appointment_id):
    """Cancel an appointment."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'User cancelled') if data else 'User cancelled'

        result = appointment_manager.cancel_appointment(appointment_id, reason)

        return jsonify({
            "message": "Appointment cancelled successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error cancelling appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/<appointment_id>/confirm', methods=['POST'])
@token_required
def confirm_appointment(current_user, appointment_id):
    """Confirm an appointment (typically done by doctor)."""
    try:
        # Only doctor can confirm
        appointment = appointment_manager.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        if str(current_user['_id']) != str(appointment['doctor_id']):
            return jsonify({"error": "Only the doctor can confirm this appointment"}), 403

        result = appointment_manager.confirm_appointment(appointment_id)

        return jsonify({
            "message": "Appointment confirmed successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error confirming appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/<appointment_id>/complete', methods=['POST'])
@token_required
def complete_appointment(current_user, appointment_id):
    """Mark appointment as completed (typically done by doctor)."""
    try:
        # Only doctor can mark as completed
        appointment = appointment_manager.collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404
        if str(current_user['_id']) != str(appointment['doctor_id']):
            return jsonify({"error": "Only the doctor can complete this appointment"}), 403

        data = request.get_json()
        notes = data.get('notes', '') if data else ''

        result = appointment_manager.mark_completed(appointment_id, notes)

        return jsonify({
            "message": "Appointment marked as completed",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error completing appointment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/appointments/<appointment_id>/reminder', methods=['POST'])
@token_required
@patient_or_doctor_required
def send_reminder(current_user, appointment_id):
    """Send a reminder for the appointment."""
    try:
        data = request.get_json()
        reminder_type = data.get('type', 'email') if data else 'email'

        result = appointment_manager.send_reminder(appointment_id, reminder_type)

        return jsonify({
            "message": "Reminder sent successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error sending reminder: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500