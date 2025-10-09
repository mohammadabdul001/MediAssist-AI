from flask import Blueprint, request, jsonify
from models.medications import Medication
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('medications', __name__)
medication_manager = Medication()

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

@bp.route('/api/medications', methods=['POST'])
@token_required
def add_medication(current_user):
    """Add a new medication for the authenticated user."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'name' not in data  or 'dosage' not in data or 'frequency' not in data or 'start_date' not in data:
            return jsonify({"error": "Required fields: name, dosage, frequency, start_date"}), 400

        # Create medication
        medication = medication_manager.add_medication(
            user_id=str(current_user['_id']),
            name=data['name'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            start_date=data['start_date'],
            end_date=data.get('end_date'),
            reminders=data.get('reminders', []),
            notes=data.get('notes', ""),
            refill_enabled=data.get('refill_enabled', False),
            pharmacy_id=data.get('pharmacy_id')
        )

        return jsonify({
            "message": "Medication added successfully",
            "medication": medication
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error adding medication: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications', methods=['GET'])
@token_required
def get_user_medications(current_user):
    """Get all medications for the authenticated user."""
    try:
        status = request.args.get('status')
        if status:
            status = status.split(',')  # Allow multiple statuses

        medications = medication_manager.get_user_medications(
            user_id=str(current_user['_id']),
            status=status
        )

        return jsonify({
            "count": len(medications),
            "medications": medications
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching medications: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/<medication_id>', methods=['GET'])
@token_required
def get_medication(current_user, medication_id):
    """Get a single medication by ID."""
    try:
        medication = medication_manager.get_medication(medication_id)
        
        # Verify user owns this medication
        if str(current_user['_id']) != str(medication['user_id']):
            return jsonify({"error": "Access denied"}), 403

        return jsonify({
            "medication": medication
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error fetching medication: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/<medication_id>', methods=['PUT'])
@token_required
def update_medication(current_user, medication_id):
    """Update a medication."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # Verify user owns this medication
        medication = medication_manager.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            return jsonify({"error": "Medication not found"}), 404
        if str(current_user['_id']) != str(medication['user_id']):
            return jsonify({"error": "Access denied"}), 403

        updated_medication = medication_manager.update_medication(medication_id, data)

        return jsonify({
            "message": "Medication updated successfully",
            "medication": updated_medication
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error updating medication: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/<medication_id>/take', methods=['POST'])
@token_required
def log_dose_taken(current_user, medication_id):
    """Log that a dose was taken."""
    try:
        data = request.get_json()
        taken_at = data.get('taken_at') if data else None
        notes = data.get('notes', "") if data else ""

        # Verify user owns this medication
        medication = medication_manager.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            return jsonify({"error": "Medication not found"}), 404
        if str(current_user['_id']) != str(medication['user_id']):
            return jsonify({"error": "Access denied"}), 403

        result = medication_manager.log_dose_taken(medication_id, taken_at, notes)

        return jsonify({
            "message": "Dose logged successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error logging dose: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/<medication_id>/miss', methods=['POST'])
@token_required
def mark_missed_dose(current_user, medication_id):
    """Mark a dose as missed."""
    try:
        data = request.get_json()
        missed_at = data.get('missed_at') if data else None
        reason = data.get('reason', "") if data else ""

        # Verify user owns this medication
        medication = medication_manager.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            return jsonify({"error": "Medication not found"}), 404
        if str(current_user['_id']) != str(medication['user_id']):
            return jsonify({"error": "Access denied"}), 403

        result = medication_manager.mark_missed_dose(medication_id, missed_at, reason)

        return jsonify({
            "message": "Missed dose recorded successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error marking missed dose: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/<medication_id>/refill', methods=['POST'])
@token_required
def request_refill(current_user, medication_id):
    """Request a refill for medication."""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1) if data else 1
        pharmacy_id = data.get('pharmacy_id') if data else None

        # Verify user owns this medication
        medication = medication_manager.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            return jsonify({"error": "Medication not found"}), 404
        if str(current_user['_id']) != str(medication['user_id']):
            return jsonify({"error": "Access denied"}), 403

        result = medication_manager.request_refill(medication_id, quantity, pharmacy_id)

        return jsonify({
            "message": "Refill requested successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error requesting refill: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/<medication_id>/discontinue', methods=['POST'])
@token_required
def discontinue_medication(current_user, medication_id):
    """Discontinue a medication."""
    try:
        data = request.get_json()
        reason = data.get('reason', "") if data else ""
        discontinued_at = data.get('discontinued_at') if data else None

        # Verify user owns this medication
        medication = medication_manager.collection.find_one({"_id": ObjectId(medication_id)})
        if not medication:
            return jsonify({"error": "Medication not found"}), 404
        if str(current_user['_id']) != str(medication['user_id']):
            return jsonify({"error": "Access denied"}), 403

        result = medication_manager.discontinue_medication(medication_id, reason, discontinued_at)

        return jsonify({
            "message": "Medication discontinued successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error discontinuing medication: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/medications/reminders', methods=['GET'])
@token_required
def get_today_reminders(current_user):
    """Get medication reminders for today."""
    try:
        reminders = medication_manager.get_reminders_for_today(str(current_user['_id']))

        return jsonify({
            "count": len(reminders),
            "reminders": reminders,
            "current_time": datetime.utcnow().isoformat()
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching reminders: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500