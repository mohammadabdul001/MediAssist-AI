from flask import Blueprint, request, jsonify, send_file
from models.health_record import HealthRecord
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
import io
import json

bp = Blueprint('health_records', __name__)
health_record_manager = HealthRecord()

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

def doctor_or_owner_required(f):
    """Decorator to allow access if user is owner OR doctor with permission"""
    @wraps(f)
    def decorated(current_user, record_id, *args, **kwargs):
        try:
            # Check if record exists
            record = health_record_manager.collection.find_one({"_id": ObjectId(record_id)})
            if not record:
                return jsonify({"error": "Record not found"}), 404

            # Allow if user is the owner
            if str(current_user['_id']) == str(record['user_id']):
                return f(current_user, record_id, *args, **kwargs)

            # Allow if user is doctor and has permission
            if current_user.get('role') == 'doctor':
                # Check if doctor has access to this record
                shared_record = health_record_manager.collection.find_one({
                    "_id": ObjectId(record_id),
                    "shared_with": {
                        "$elemMatch": {
                            "doctor_id": ObjectId(current_user['_id']),
                            "permissions": {"$in": ["view", "edit"]}
                        }
                    }
                })
                if shared_record:
                    return f(current_user, record_id, *args, **kwargs)

            return jsonify({"error": "Access denied"}), 403

        except Exception as e:
            return jsonify({"error": "Invalid record ID"}), 400
    return decorated

@bp.route('/api/health-records', methods=['POST'])
@token_required
def create_health_record(current_user):
    """Create a new health record for the authenticated user."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'type' not in data:
            return jsonify({"error": "'type' is required"}), 400
        if 'data' not in data:
            return jsonify({"error": "'data' is required"}), 400
        # Create record
        record = health_record_manager.create_record(
            user_id=str(current_user['_id']),
            record_type=data['type'],
            data=data['data'],
            metadata=data.get('metadata', {}),
            shared_with=data.get('shared_with', [])
        )

        return jsonify({
            "message": "Health record created successfully",
            "record": record
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error creating health record: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records', methods=['GET'])
@token_required
def get_user_health_records(current_user):
    """Get all health records for the authenticated user."""
    try:
        record_type = request.args.get('type')
        include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'

        records = health_record_manager.get_user_records(
            user_id=str(current_user['_id']),
            record_type=record_type,
            include_deleted=include_deleted
        )

        return jsonify({
            "count": len(records),
            "records": records
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching health records: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records/doctor', methods=['GET'])
@token_required
def get_doctor_shared_records(current_user):
    """Get all records shared with the authenticated doctor."""
    try:
        if current_user.get('role') != 'doctor':
            return jsonify({"error": "Only doctors can access this endpoint"}), 403

        records = health_record_manager.get_shared_records_for_doctor(str(current_user['_id']))

        return jsonify({
            "count": len(records),
            "records": records
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching shared records: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records/<record_id>/share', methods=['POST'])
@token_required
def share_record(current_user, record_id):
    """Share a record with a doctor."""
    try:
        data = request.get_json()
        if not data or 'doctor_id' not in data:
            return jsonify({"error": "'doctor_id' is required"}), 400

        permissions = data.get('permissions', ['view'])
        if not isinstance(permissions, list):
            permissions = [permissions]

        result = health_record_manager.share_record_with_doctor(
            record_id=record_id,
            doctor_id=data['doctor_id'],
            permissions=permissions
        )

        return jsonify({
            "message": "Record shared successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error sharing record: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records/<record_id>/revoke/<doctor_id>', methods=['POST'])
@token_required
def revoke_record_access(current_user, record_id, doctor_id):
    """Revoke a doctor's access to a record."""
    try:
        # Only record owner can revoke access
        record = health_record_manager.collection.find_one({"_id": ObjectId(record_id)})
        if not record:
            return jsonify({"error": "Record not found"}), 404
        if str(current_user['_id']) != str(record['user_id']):
            return jsonify({"error": "Only record owner can revoke access"}), 403

        result = health_record_manager.revoke_doctor_access(record_id, doctor_id)

        return jsonify({
            "message": "Doctor access revoked successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error revoking access: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records/<record_id>', methods=['PUT'])
@token_required
@doctor_or_owner_required
def update_health_record(current_user, record_id):
    """Update a health record (owner or doctor with edit permission)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # If doctor, check for edit permission
        if current_user.get('role') == 'doctor':
            record = health_record_manager.collection.find_one({"_id": ObjectId(record_id)})
            if record:
                # Check if doctor has edit permission
                has_edit_permission = False
                for share in record.get('shared_with', []):
                    if str(share.get('doctor_id')) == str(current_user['_id']) and 'edit' in share.get('permissions', []):
                        has_edit_permission = True
                        break
                if not has_edit_permission:
                    return jsonify({"error": "Doctor does not have edit permission"}), 403

        updated_record = health_record_manager.update_record(
            record_id=record_id,
            data=data.get('data'),
            metadata=data.get('metadata')
        )

        return jsonify({
            "message": "Health record updated successfully",
            "record": updated_record
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error updating health record: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records/<record_id>', methods=['DELETE'])
@token_required
def delete_health_record(current_user, record_id):
    """Soft delete a health record (only owner can delete)."""
    try:
        # Verify ownership
        record = health_record_manager.collection.find_one({"_id": ObjectId(record_id)})
        if not record:
            return jsonify({"error": "Record not found"}), 404
        if str(current_user['_id']) != str(record['user_id']):
            return jsonify({"error": "Only record owner can delete record"}), 403

        result = health_record_manager.soft_delete_record(record_id)

        return jsonify({
            "message": "Health record deleted successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error deleting health record: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-records/<record_id>/pdf', methods=['GET'])
@token_required
@doctor_or_owner_required
def generate_pdf_summary(current_user, record_id):
    """Generate a PDF summary of the health record."""
    try:
        summary = health_record_manager.generate_pdf_summary(record_id)

        # In production, convert this to actual PDF using ReportLab or similar
        # For now, return as JSON with PDF-ready structure
        return jsonify({
            "message": "PDF summary generated",
            "summary": summary,
            "note": "In production, this would return an actual PDF file"
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500