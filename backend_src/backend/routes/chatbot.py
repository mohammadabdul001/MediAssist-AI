from flask import Blueprint, request, jsonify
from models.chatbot import Chatbot
from models.user import User
from models.symptom_analyzer import SymptomAnalyzer
from models.medications import Medication
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('chatbot', __name__)

# Initialize dependencies
symptom_analyzer = SymptomAnalyzer('data')
medication_manager = Medication()
chatbot = Chatbot(symptom_analyzer, medication_manager)

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

@bp.route('/api/chatbot', methods=['POST'])
@token_required
def chatbot_message(current_user):
    """Send a message to the chatbot and get a response."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'message' not in data or not data['message'].strip():
            return jsonify({"error": "Message is required"}), 400

        # Get context if provided
        context = data.get('context', {})

        # Process message
        response = chatbot.process_message(
            user_id=str(current_user['_id']),
            message=data['message'],
            context=context
        )

        return jsonify({
            "response": response
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error processing chatbot message: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/chatbot/history', methods=['GET'])
@token_required
def get_chatbot_history(current_user):
    """Get chatbot conversation history for the user."""
    try:
        limit = int(request.args.get('limit', 10))
        if limit <= 0:
            return jsonify({"error": "Limit must be positive"}), 400

        history = chatbot.get_conversation_history(str(current_user['_id']), limit)

        return jsonify({
            "count": len(history),
            "history": history
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching chatbot history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/chatbot/history', methods=['DELETE'])
@token_required
def clear_chatbot_history(current_user):
    """Clear chatbot conversation history for the user."""
    try:
        result = chatbot.clear_conversation_history(str(current_user['_id']))

        return jsonify({
            "message": "Chatbot history cleared successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error clearing chatbot history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/chatbot/languages', methods=['GET'])
@token_required
def get_supported_languages(current_user):
    """Get supported languages for chatbot."""
    # In production, this would be more comprehensive
    supported_languages = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "hi": "Hindi"
    }

    return jsonify({
        "supported_languages": supported_languages,
        "current_language": current_user.get("profile", {}).get("language", "en")
    }), 200

@bp.route('/api/chatbot/voice', methods=['POST'])
@token_required
def chatbot_voice_message(current_user):
    """Handle voice messages (stub for production implementation)."""
    try:
        # In production, this would process audio files and convert to text
        # For now, return error since we don't have voice processing
        return jsonify({
            "error": "Voice message processing is not yet implemented. Please use text messages."
        }), 501

    except Exception as e:
        print(f"Error processing voice message: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500