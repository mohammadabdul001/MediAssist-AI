from flask import Blueprint, request, jsonify
from models.sos import EmergencySOS
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime, timedelta  # ✅ Added missing import

bp = Blueprint('sos', __name__)
sos_manager = EmergencySOS()

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

@bp.route('/api/emergency-sos', methods=['POST'])
@token_required
def trigger_emergency_sos(current_user):
    """Trigger an emergency SOS alert."""
    try:
        data = request.get_json()
        message = data.get('message', 'Emergency help needed') if data else 'Emergency help needed'
        location = data.get('location') if data else None

        sos_log = sos_manager.trigger_sos(
            user_id=str(current_user['_id']),
            message=message,
            location=location,
            auto_triggered=False
        )

        return jsonify({
            "message": "Emergency SOS alert triggered successfully",
            "sos_alert": sos_log,
            "contacts_notified": len(sos_log.get("contacts_notified", [])),
            "hospitals_notified": len(sos_log.get("hospitals_notified", []))
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error triggering emergency SOS: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/emergency-sos/history', methods=['GET'])
@token_required
def get_sos_history(current_user):
    """Get emergency SOS alert history for the user."""
    try:
        limit = int(request.args.get('limit', 10))
        if limit <= 0:
            return jsonify({"error": "Limit must be positive"}), 400

        history = sos_manager.get_sos_history(str(current_user['_id']), limit)

        return jsonify({
            "count": len(history),
            "sos_history": history
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching SOS history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/emergency-sos/<sos_id>', methods=['GET'])
@token_required
def get_sos_alert(current_user, sos_id):
    """Get a specific SOS alert by ID."""
    try:
        # Validate sos_id format
        if not ObjectId.is_valid(sos_id):
            return jsonify({"error": "Invalid SOS ID format"}), 400

        sos_log = sos_manager.get_sos_by_id(sos_id)
        if not sos_log:
            return jsonify({"error": "SOS alert not found"}), 404

        # Ensure user owns this alert
        if str(current_user['_id']) != str(sos_log.get('user_id')):
            return jsonify({"error": "Access denied"}), 403

        return jsonify({"sos_alert": sos_log}), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        print(f"Error fetching SOS alert: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/emergency-sos/auto-trigger', methods=['POST'])
@token_required
def auto_trigger_sos(current_user):
    """Auto-trigger SOS from wearable data (for testing purposes)."""
    try:
        data = request.get_json()
        if not data or 'abnormal_data' not in data:
            return jsonify({"error": "Abnormal data is required"}), 400

        sos_log = sos_manager.auto_trigger_sos_from_wearable(
            user_id=str(current_user['_id']),
            abnormal_data=data
        )

        return jsonify({
            "message": "Auto-triggered SOS alert successfully",
            "sos_alert": sos_log
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error auto-triggering SOS: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/emergency-sos/status', methods=['GET'])
@token_required
def get_emergency_status(current_user):
    """Get user's emergency configuration status."""
    try:
        # ✅ Use User model instead of sos_manager.users
        user = User.find_by_id(current_user['_id'])  # Assuming this method exists
        if not user:
            return jsonify({"error": "User not found"}), 404

        emergency_contacts = user.get("emergency_contacts", [])
        profile = user.get("profile", {})
        auto_sos_enabled = profile.get("auto_sos_enabled", False)
        location_sharing_enabled = profile.get("location_sharing_enabled", False)

        # Get recent SOS count
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sos_count = sos_manager.get_recent_sos_count(str(current_user['_id']), thirty_days_ago)

        return jsonify({
            "emergency_status": {
                "emergency_contacts_configured": len(emergency_contacts) > 0,
                "emergency_contacts_count": len(emergency_contacts),
                "auto_sos_enabled": auto_sos_enabled,
                "location_sharing_enabled": location_sharing_enabled,
                "recent_sos_alerts_count": recent_sos_count,
                "emergency_contacts": emergency_contacts
            }
        }), 200

    except Exception as e:
        print(f"Error fetching emergency status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/emergency-sos/test', methods=['POST'])
@token_required
def test_sos_system(current_user):
    """Test the SOS system without actually sending alerts (for development)."""
    try:
        data = request.get_json()
        message = data.get('message', 'Test emergency alert') if data else 'Test emergency alert'
        location = data.get('location', 'Test location') if data else 'Test location'

        # ✅ Use User model
        user = User.find_by_id(current_user['_id'])
        if not user:
            raise ValueError("User not found")

        emergency_contacts = user.get("emergency_contacts", [])
        health_status = sos_manager._get_user_health_status(str(current_user['_id']))
        first_aid_instructions = sos_manager._get_ai_first_aid_instructions(str(current_user['_id']), health_status)

        simulated_contacts = []
        for contact in emergency_contacts[:2]:
            contact_info = contact.get("phone") or contact.get("email") or str(contact)
            notification_type = "email" if "@" in contact_info else "sms" if contact_info.isdigit() else "in_app"
            simulated_contacts.append({
                "contact": contact,
                "notification_type": notification_type,
                "status": "simulated_success"
            })

        simulated_hospitals = [
            {"name": "City General Hospital", "status": "simulated_success"},
            {"name": "Mercy Medical Center", "status": "simulated_success"}
        ]

        test_result = {
            "test_mode": True,
            "message": "SOS system test completed successfully",
            "user_id": str(current_user['_id']),
            "username": user.get("username", "Unknown"),
            "message_sent": message,
            "location_used": location,
            "health_status": health_status,
            "first_aid_instructions": first_aid_instructions,
            "simulated_contacts_notified": simulated_contacts,
            "simulated_hospitals_notified": simulated_hospitals,
            "timestamp": datetime.utcnow().isoformat()
        }

        return jsonify(test_result), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error testing SOS system: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500