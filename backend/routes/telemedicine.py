from flask import Blueprint, request, jsonify
from models.telemedicine import Telemedicine
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('telemedicine', __name__)
telemedicine_manager = Telemedicine()

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

def session_participant_required(f):
    """Decorator to allow access if user is participant in the session"""
    @wraps(f)
    def decorated(current_user, session_id, *args, **kwargs):
        try:
            session = telemedicine_manager.collection.find_one({"_id": ObjectId(session_id)})
            if not session:
                return jsonify({"error": "Telemedicine session not found"}), 404

            # Allow if user is the patient or doctor
            if str(current_user['_id']) == str(session['patient_id']) or str(current_user['_id']) == str(session['doctor_id']):
                return f(current_user, session_id, *args, **kwargs)

            return jsonify({"error": "Access denied"}), 403

        except Exception as e:
            return jsonify({"error": "Invalid session ID"}), 400
    return decorated

@bp.route('/api/telemedicine/session', methods=['POST'])
@token_required
def create_telemedicine_session(current_user):
    """Create a telemedicine session for an appointment."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'appointment_id' not in data:
            return jsonify({"error": "Appointment ID is required"}), 400

        # Verify user is either patient or doctor for this appointment
        appointment = telemedicine_manager.appointments.find_one({"_id": ObjectId(data['appointment_id'])})
        if not appointment:
            return jsonify({"error": "Appointment not found"}), 404

        if str(current_user['_id']) != str(appointment['patient_id']) and str(current_user['_id']) != str(appointment['doctor_id']):
            return jsonify({"error": "User not authorized for this appointment"}), 403

        # Create session
        session = telemedicine_manager.create_session(
            appointment_id=data['appointment_id'],
            patient_id=str(appointment['patient_id']),
            doctor_id=str(appointment['doctor_id'])
        )

        return jsonify({
            "message": "Telemedicine session created successfully",
            "session": session
        }), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error creating telemedicine session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>', methods=['GET'])
@token_required
@session_participant_required
def get_telemedicine_session(current_user, session_id):
    """Get a telemedicine session by ID."""
    try:
        session = telemedicine_manager.get_session(session_id)
        return jsonify({
            "session": session
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error fetching telemedicine session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/user-sessions', methods=['GET'])
@token_required
def get_user_telemedicine_sessions(current_user):
    """Get all telemedicine sessions for the current user."""
    try:
        role = request.args.get('role', 'patient')
        status = request.args.get('status')
        
        if status:
            status = status.split(',')  # Allow multiple statuses

        sessions = telemedicine_manager.get_user_sessions(
            user_id=str(current_user['_id']),
            role=role,
            status=status
        )

        return jsonify({
            "count": len(sessions),
            "sessions": sessions
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching user telemedicine sessions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/start', methods=['POST'])
@token_required
@session_participant_required
def start_telemedicine_session(current_user, session_id):
    """Start a telemedicine session (called when user joins the meeting)."""
    try:
        session = telemedicine_manager.start_session(session_id, str(current_user['_id']))

        return jsonify({
            "message": "Telemedicine session started successfully",
            "session": session
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error starting telemedicine session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/end', methods=['POST'])
@token_required
@session_participant_required
def end_telemedicine_session(current_user, session_id):
    """End a telemedicine session and generate consultation summary."""
    try:
        data = request.get_json()
        summary = data.get('summary', '') if data else ''
        prescriptions = data.get('prescriptions', []) if data else []
        vitals = data.get('vitals', {}) if data else {}

        session = telemedicine_manager.end_session(session_id, summary, prescriptions, vitals)

        return jsonify({
            "message": "Telemedicine session ended successfully",
            "session": session
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error ending telemedicine session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/chat', methods=['POST'])
@token_required
@session_participant_required
def send_chat_message(current_user, session_id):
    """Send a chat message during a telemedicine session."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400

        message_type = data.get('message_type', 'text')
        message = telemedicine_manager.send_chat_message(
            session_id=session_id,
            sender_id=str(current_user['_id']),
            message=data['message'],
            message_type=message_type
        )

        return jsonify({
            "message": "Chat message sent successfully",
            "chat_message": message
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error sending chat message: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/chat', methods=['GET'])
@token_required
@session_participant_required
def get_chat_history(current_user, session_id):
    """Get chat history for a telemedicine session."""
    try:
        chat_history = telemedicine_manager.get_session_chat_history(session_id)

        return jsonify({
            "count": len(chat_history),
            "chat_history": chat_history
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching chat history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/file', methods=['POST'])
@token_required
@session_participant_required
def share_file(current_user, session_id):
    """Share a file during a telemedicine session."""
    try:
        data = request.get_json()
        if not data or 'file_name' not in data or 'file_url' not in data:
            return jsonify({"error": "File name and URL are required"}), 400

        file_type = data.get('file_type', 'document')
        shared_file = telemedicine_manager.share_file(
            session_id=session_id,
            sender_id=str(current_user['_id']),
            file_name=data['file_name'],
            file_url=data['file_url'],
            file_type=file_type
        )

        return jsonify({
            "message": "File shared successfully",
            "shared_file": shared_file
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error sharing file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/files', methods=['GET'])
@token_required
@session_participant_required
def get_shared_files(current_user, session_id):
    """Get shared files for a telemedicine session."""
    try:
        shared_files = telemedicine_manager.get_session_shared_files(session_id)

        return jsonify({
            "count": len(shared_files),
            "shared_files": shared_files
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching shared files: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/cancel', methods=['POST'])
@token_required
@session_participant_required
def cancel_telemedicine_session(current_user, session_id):
    """Cancel a telemedicine session."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'Session cancelled') if data else 'Session cancelled'

        result = telemedicine_manager.cancel_session(session_id, reason)

        return jsonify({
            "message": "Telemedicine session cancelled successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error cancelling telemedicine session: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/telemedicine/session/<session_id>/recording', methods=['POST'])
@token_required
@session_participant_required
def toggle_recording(current_user, session_id):
    """Enable/disable session recording."""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True) if data else True

        result = telemedicine_manager.enable_recording(session_id, enabled)

        return jsonify({
            "message": f"Recording {'enabled' if enabled else 'disabled'} successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error toggling recording: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500