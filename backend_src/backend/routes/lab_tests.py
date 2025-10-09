from flask import Blueprint, request, jsonify
from models.lab_test import LabTest
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('lab_tests', __name__)
lab_test_manager = LabTest()

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

def doctor_or_technician_or_patient_required(f):
    """Decorator to allow access if user is doctor, technician, or patient related to test"""
    @wraps(f)
    def decorated(current_user, test_id, *args, **kwargs):
        try:
            test = lab_test_manager.collection.find_one({"_id": ObjectId(test_id)})
            if not test:
                return jsonify({"error": "Lab test not found"}), 404

            # Allow if user is the doctor who requested
            if str(current_user['_id']) == str(test['doctor_id']):
                return f(current_user, test_id, *args, **kwargs)

            # Allow if user is the lab technician assigned
            if current_user.get('role') == 'lab_technician' and test.get('lab_technician_id') and str(current_user['_id']) == str(test['lab_technician_id']):
                return f(current_user, test_id, *args, **kwargs)

            # Allow if user is the patient
            if str(current_user['_id']) == str(test['patient_id']):
                return f(current_user, test_id, *args, **kwargs)

            return jsonify({"error": "Access denied"}), 403

        except Exception as e:
            return jsonify({"error": "Invalid test ID"}), 400
    return decorated

@bp.route('/api/lab-tests', methods=['POST'])
@token_required
def create_lab_test_request(current_user):
    """Create a new lab test request (only doctors can create)."""
    try:
        if current_user.get('role') != 'doctor':
            return jsonify({"error": "Only doctors can create lab test requests"}), 403

        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'patient_id' not in data or 'test_name' not in data:
            return jsonify({"error": "Required fields: patient_id, test_name"}), 400

        # Create lab test request
        lab_test = lab_test_manager.create_test_request(
            doctor_id=str(current_user['_id']),
            patient_id=data['patient_id'],
            test_name=data['test_name'],
            priority=data.get('priority', 'routine'),
            notes=data.get('notes', ''),
            sample_type=data.get('sample_type', 'blood'),
            home_collection=data.get('home_collection', False),
            collection_address=data.get('collection_address') if data.get('home_collection') else None
        )

        return jsonify({
            "message": "Lab test request created successfully",
            "lab_test": lab_test
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error creating lab test request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/<test_id>', methods=['GET'])
@token_required
@doctor_or_technician_or_patient_required
def get_lab_test(current_user, test_id):
    """Get a single lab test by ID."""
    try:
        lab_test = lab_test_manager.get_test_by_id(test_id)
        return jsonify({
            "lab_test": lab_test
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error fetching lab test: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/patient/<patient_id>', methods=['GET'])
@token_required
def get_patient_lab_tests(current_user, patient_id):
    """Get all lab tests for a patient."""
    try:
        # Verify access (patient can only access their own tests, doctors can access their patients' tests)
        if str(current_user['_id']) != patient_id:
            if current_user.get('role') != 'doctor':
                return jsonify({"error": "Access denied"}), 403
            # Check if doctor has access to this patient (in production, check appointment history or explicit sharing)
            # For now, allow any doctor to access any patient's tests (in production, implement proper access control)
        
        status = request.args.get('status')
        if status:
            status = status.split(',')  # Allow multiple statuses

        tests = lab_test_manager.get_patient_tests(patient_id, status)

        return jsonify({
            "count": len(tests),
            "lab_tests": tests
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching patient lab tests: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/doctor/<doctor_id>', methods=['GET'])
@token_required
def get_doctor_lab_tests(current_user, doctor_id):
    """Get all lab tests requested by a doctor."""
    try:
        # Verify access (doctor can only access their own tests)
        if str(current_user['_id']) != doctor_id and current_user.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403

        status = request.args.get('status')
        if status:
            status = status.split(',')  # Allow multiple statuses

        tests = lab_test_manager.get_doctor_tests(doctor_id, status)

        return jsonify({
            "count": len(tests),
            "lab_tests": tests
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching doctor lab tests: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/technician/<technician_id>', methods=['GET'])
@token_required
def get_technician_lab_tests(current_user, technician_id):
    """Get all lab tests for a lab technician."""
    try:
        # Verify access (technician can only access their own tests)
        if str(current_user['_id']) != technician_id and current_user.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403

        status = request.args.get('status')
        if status:
            status = status.split(',')  # Allow multiple statuses

        tests = lab_test_manager.get_lab_technician_tests(technician_id, status)

        return jsonify({
            "count": len(tests),
            "lab_tests": tests
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching technician lab tests: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/<test_id>/status', methods=['PUT'])
@token_required
@doctor_or_technician_or_patient_required
def update_lab_test_status(current_user, test_id):
    """Update the status of a lab test."""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        # Only lab technicians can mark as "sample_collected", "in_progress", "completed"
        # Doctors and patients can only cancel
        if data['status'] in ["sample_collected", "in_progress", "completed"] and current_user.get('role') != 'lab_technician':
            return jsonify({"error": "Only lab technicians can update to this status"}), 403

        notes = data.get('notes', '')

        updated_test = lab_test_manager.update_test_status(
            test_id=test_id,
            status=data['status'],
            updated_by_id=str(current_user['_id']),
            notes=notes
        )

        return jsonify({
            "message": "Lab test status updated successfully",
            "lab_test": updated_test
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error updating lab test status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/<test_id>/results', methods=['POST'])
@token_required
def upload_lab_test_results(current_user, test_id):
    """Upload lab test results (only lab technicians can upload)."""
    try:
        if current_user.get('role') != 'lab_technician':
            return jsonify({"error": "Only lab technicians can upload results"}), 403

        data = request.get_json()
        if not data or 'results' not in data:
            return jsonify({"error": "Results are required"}), 400

        interpretation = data.get('interpretation', '')
        reference_ranges = data.get('reference_ranges', None)

        updated_test = lab_test_manager.upload_test_results(
            test_id=test_id,
            technician_id=str(current_user['_id']),
            results=data['results'],
            interpretation=interpretation,
            reference_ranges=reference_ranges
        )

        return jsonify({
            "message": "Lab test results uploaded successfully",
            "lab_test": updated_test
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error uploading lab test results: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/<test_id>/cancel', methods=['POST'])
@token_required
@doctor_or_technician_or_patient_required
def cancel_lab_test(current_user, test_id):
    """Cancel a lab test."""
    try:
        data = request.get_json()
        reason = data.get('reason', '') if data else ''

        # Only doctor who requested or patient can cancel (technician can only mark as cancelled if instructed)
        test = lab_test_manager.collection.find_one({"_id": ObjectId(test_id)})
        if not test:
            return jsonify({"error": "Lab test not found"}), 404

        if current_user.get('role') == 'lab_technician' and str(current_user['_id']) != str(test.get('lab_technician_id', '')):
            return jsonify({"error": "Lab technician not assigned to this test"}), 403

        result = lab_test_manager.cancel_test(
            test_id=test_id,
            cancelled_by_id=str(current_user['_id']),
            reason=reason
        )

        return jsonify({
            "message": "Lab test cancelled successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error cancelling lab test: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/lab-tests/<test_id>/analysis', methods=['GET'])
@token_required
@doctor_or_technician_or_patient_required
def get_test_results_analysis(current_user, test_id):
    """Get AI-driven analysis of test results."""
    try:
        analysis = lab_test_manager.get_test_results_analysis(test_id)

        return jsonify({
            "analysis": analysis
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error getting test results analysis: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500