from flask import Blueprint, request, jsonify
from models.health_analytics import HealthAnalytics
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('health_analytics', __name__)
analytics_manager = HealthAnalytics()

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

@bp.route('/api/health-analytics/summary', methods=['GET'])
@token_required
def get_health_summary(current_user):
    """Get comprehensive health summary for the user."""
    try:
        days = int(request.args.get('days', 30))
        if days <= 0:
            return jsonify({"error": "Days must be positive"}), 400

        summary = analytics_manager.get_user_health_summary(str(current_user['_id']), days)

        return jsonify({
            "health_summary": summary
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching health summary: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-analytics/trend/<metric>', methods=['GET'])
@token_required
def get_health_trend(current_user, metric):
    """Get trend analysis for a specific health metric."""
    try:
        days = int(request.args.get('days', 90))
        if days <= 0:
            return jsonify({"error": "Days must be positive"}), 400

        trend_analysis = analytics_manager.get_health_trend_analysis(str(current_user['_id']), metric, days)

        return jsonify({
            "trend_analysis": trend_analysis
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching health trend: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-analytics/predictive', methods=['GET'])
@token_required
def get_predictive_insights(current_user):
    """Get predictive health insights for the user."""
    try:
        insights = analytics_manager.get_predictive_health_insights(str(current_user['_id']))

        return jsonify({
            "predictive_insights": insights
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching predictive insights: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-analytics/comparison/<metric>', methods=['GET'])
@token_required
def get_population_comparison(current_user, metric):
    """Compare user's health metric with population averages."""
    try:
        demographic_group = request.args.get('group', 'general')

        comparison = analytics_manager.compare_with_population(str(current_user['_id']), metric, demographic_group)

        return jsonify({
            "population_comparison": comparison
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching population comparison: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/health-analytics/wearable', methods=['GET'])
@token_required
def get_wearable_analysis(current_user):
    """Get analysis of data from wearable devices."""
    try:
        device_type = request.args.get('device_type', 'smartwatch')
        days = int(request.args.get('days', 30))
        if days <= 0:
            return jsonify({"error": "Days must be positive"}), 400

        wearable_analysis = analytics_manager.get_wearable_data_analysis(str(current_user['_id']), device_type, days)

        return jsonify({
            "wearable_analysis": wearable_analysis
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching wearable analysis: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500