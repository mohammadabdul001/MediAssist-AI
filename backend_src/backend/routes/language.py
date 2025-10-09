from flask import Blueprint, request, jsonify, send_file
from models.language import LanguageSupport
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime
import json
import io

bp = Blueprint('language', __name__)
language_manager = LanguageSupport()

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

@bp.route('/api/language/supported', methods=['GET'])
def get_supported_languages():
    """Get all supported languages."""
    try:
        languages = language_manager.supported_languages
        
        return jsonify({
            "supported_languages": languages,
            "total_languages": len(languages),
            "indian_languages": len(languages) - 1  # Excluding English
        }), 200

    except Exception as e:
        print(f"Error fetching supported languages: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/user', methods=['GET'])
@token_required
def get_user_language(current_user):
    """Get user's preferred language."""
    try:
        language_code = language_manager.get_user_language(str(current_user['_id']))
        language_info = language_manager.supported_languages.get(language_code, {})
        
        return jsonify({
            "user_id": str(current_user['_id']),
            "language_code": language_code,
            "language_name": language_info.get("name", "Unknown"),
            "native_name": language_info.get("native_name", "Unknown"),
            "region": language_info.get("region", "Unknown")
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching user language: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/user', methods=['PUT'])
@token_required
def set_user_language(current_user):
    """Set user's preferred language."""
    try:
        data = request.get_json()
        if not data or 'language_code' not in data:
            return jsonify({"error": "Language code is required"}), 400

        result = language_manager.set_user_language(str(current_user['_id']), data['language_code'])

        return jsonify({
            "message": "User language updated successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error setting user language: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/translate', methods=['POST'])
@token_required
def translate_text(current_user):
    """Translate text from one language to another."""
    try:
        data = request.get_json()
        if not data or 'text' not in data or not data['text'].strip():
            return jsonify({"error": "Text is required"}), 400

        source_language = data.get('source_language', 'en')
        target_language = data.get('target_language', language_manager.get_user_language(str(current_user['_id'])))

        translated_text = language_manager.translate_text(data['text'], source_language, target_language)

        return jsonify({
            "original_text": data['text'],
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": translated_text
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error translating text: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/translations/<language_code>', methods=['GET'])
@token_required
def get_translations_for_language(current_user, language_code):
    """Get all translations for a specific language."""
    try:
        if language_code not in language_manager.supported_languages:
            return jsonify({"error": f"Unsupported language code: {language_code}"}), 400

        translations = language_manager.get_all_translations_for_language(language_code)
        
        return jsonify({
            "language_code": language_code,
            "language_name": language_manager.supported_languages[language_code]["name"],
            "native_name": language_manager.supported_languages[language_code]["native_name"],
            "translations": translations,
            "total_categories": len(translations),
            "total_translations": sum(len(cat) for cat in translations.values())
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching translations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/translation', methods=['POST'])
@token_required
def add_or_update_translation(current_user):
    """Add or update a translation (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({"error": "Only administrators can update translations"}), 403

        data = request.get_json()
        if not data or 'language_code' not in  data or 'category' not in data or 'key' not in data or 'value' not in data:
            return jsonify({"error": "Required fields: language_code, category, key, value"}), 400

        result = language_manager.add_or_update_translation(
            language_code=data['language_code'],
            category=data['category'],
            key=data['key'],
            value=data['value'],
            updated_by=str(current_user['_id'])
        )

        return jsonify({
            "message": "Translation updated successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error updating translation: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/bulk-update', methods=['POST'])
@token_required
def bulk_update_translations(current_user):
    """Bulk update translations for a language (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({"error": "Only administrators can update translations"}), 403

        data = request.get_json()
        if not data or 'language_code' not in data or 'translations' not in data:
            return jsonify({"error": "Required fields: language_code, translations"}), 400

        result = language_manager.bulk_update_translations(
            language_code=data['language_code'],
            translations_data=data['translations'],
            updated_by=str(current_user['_id'])
        )

        return jsonify({
            "message": "Translations updated successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error bulk updating translations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/stats', methods=['GET'])
@token_required
def get_language_stats(current_user):
    """Get language statistics (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({"error": "Only administrators can access language statistics"}), 403

        stats = language_manager.get_language_stats()

        return jsonify({
            "language_stats": stats
        }), 200

    except Exception as e:
        print(f"Error fetching language stats: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/missing/<language_code>', methods=['GET'])
@token_required
def get_missing_translations(current_user, language_code):
    """Get missing translations for a language (compared to English) (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({"error": "Only administrators can access missing translations"}), 403

        if language_code not in language_manager.supported_languages:
            return jsonify({"error": f"Unsupported language code: {language_code}"}), 400

        missing = language_manager.get_missing_translations(language_code)

        return jsonify({
            "language_code": language_code,
            "missing_translations": missing,
            "total_missing": sum(len(keys) for keys in missing.values())
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching missing translations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/export/<language_code>', methods=['GET'])
@token_required
def export_translations(current_user, language_code):
    """Export translations for a language as JSON (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({"error": "Only administrators can export translations"}), 403

        if language_code not in language_manager.supported_languages:
            return jsonify({"error": f"Unsupported language code: {language_code}"}), 400

        export_data = language_manager.export_translations(language_code)

        # Return as JSON response
        return jsonify(export_data), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error exporting translations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/language/import/<language_code>', methods=['POST'])
@token_required
def import_translations(current_user, language_code):
    """Import translations from JSON data (admin only)."""
    try:
        # Check if user is admin
        if current_user.get('role') != 'admin':
            return jsonify({"error": "Only administrators can import translations"}), 403

        if language_code not in language_manager.supported_languages:
            return jsonify({"error": f"Unsupported language code: {language_code}"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "Import data is required"}), 400

        result = language_manager.import_translations(language_code, data, str(current_user['_id']))

        return jsonify({
            "message": "Translations imported successfully",
            "result": result
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error importing translations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500