from flask import Blueprint, request, jsonify
from models.symptom_analyzer import SymptomAnalyzer
from models.user import User
from functools import wraps
import jwt
from config import Config
import os

# Initialize blueprint and analyzer
bp = Blueprint('symptom_analysis', __name__)
analyzer = SymptomAnalyzer('data')  # Assumes 'data' folder in root

# JWT Authentication Decorator
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

@bp.route('/api/symptom-analysis', methods=['POST'])
@token_required
def analyze_symptoms(current_user):
    """
    API Endpoint: POST /api/symptom-analysis
    Headers: Authorization: Bearer <JWT_TOKEN>
    Body: {"symptoms": ["fever", "cough", "headache"]}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        if 'symptoms' not in data:
            return jsonify({"error": "'symptoms' field is required"}), 400
        if not isinstance(data['symptoms'], list):
            return jsonify({"error": "'symptoms' must be a list of strings"}), 400
        if len(data['symptoms']) == 0:
            return jsonify({"error": "At least one symptom is required"}), 400

        # Convert all symptoms to strings and strip whitespace
        symptoms = [str(s).strip() for s in data['symptoms'] if str(s).strip()]

        # Perform analysis
        result = analyzer.analyze(str(current_user['_id']), symptoms)
        
        return jsonify(result), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Unexpected error in symptom analysis: {str(e)}")
        return jsonify({"error": "Internal server error occurred"}), 500