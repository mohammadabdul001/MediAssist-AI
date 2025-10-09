from flask import Blueprint, request, jsonify
from models.recommendations import PersonalizedRecommendations
from models.user import User
from functools import wraps
import jwt
from config import Config
from bson import ObjectId
from datetime import datetime

bp = Blueprint('recommendations', __name__)
recommendations_manager = PersonalizedRecommendations()

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

@bp.route('/api/recommendations/daily', methods=['GET'])
@token_required
def get_daily_recommendations(current_user):
    """Get personalized daily health recommendations for the user."""
    try:
        # Get recommendations for today
        recommendations = recommendations_manager.get_user_recommendations(str(current_user['_id']))

        return jsonify({
            "recommendations": recommendations
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching daily recommendations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/recommendations/history', methods=['GET'])
@token_required
def get_recommendations_history(current_user):
    """Get recommendation history for the user."""
    try:
        days = int(request.args.get('days', 30))
        if days <= 0:
            return jsonify({"error": "Days must be positive"}), 400

        history = recommendations_manager.get_recommendation_history(str(current_user['_id']), days)

        return jsonify({
            "count": len(history),
            "history": history
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching recommendations history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/recommendations/<date_str>', methods=['GET'])
@token_required
def get_recommendations_for_date(current_user, date_str):
    """Get personalized recommendations for a specific date."""
    try:
        recommendations = recommendations_manager.get_user_recommendations(str(current_user['_id']), date_str)

        return jsonify({
            "recommendations": recommendations,
            "date": date_str
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching recommendations for date: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/recommendations/generate', methods=['POST'])
@token_required
def generate_recommendations(current_user):
    """Generate new personalized recommendations for the user."""
    try:
        recommendations = recommendations_manager.generate_daily_recommendations(str(current_user['_id']))

        return jsonify({
            "message": "Recommendations generated successfully",
            "recommendations": recommendations
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/recommendations/weekly-summary', methods=['GET'])
@token_required
def get_weekly_summary(current_user):
    """Get a weekly summary of recommendations and adherence."""
    try:
        # Get last 7 days of recommendations
        history = recommendations_manager.get_recommendation_history(str(current_user['_id']), 7)
        
        if not history:
            return jsonify({
                "error": "No recommendation history found for the past week"
            }), 404

        # Calculate summary statistics
        summary = {
            "period_days": 7,
            "start_date": (datetime.utcnow().date() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "total_recommendations": 0,
            "categories": {
                "dietary": 0,
                "exercise": 0,
                "medication": 0,
                "health_tips": 0,
                "seasonal_alerts": 0,
                "vaccination_reminders": 0,
                "hydration_reminders": 0,
                "sleep_recommendations": 0
            },
            "most_common_recommendations": [],
            "adherence_rate": 0.0  # In production, this would track user adherence
        }

        # Count recommendations by category
        recommendation_counts = defaultdict(int)
        
        for day in history:
            for category in ["dietary_recommendations", "exercise_recommendations", "health_tips", "seasonal_alerts", "sleep_recommendations"]:
                if category in day and isinstance(day[category], list):
                    count = len(day[category])
                    summary["categories"][category.replace("_recommendations", "").replace("_reminders", "").replace("_alerts", "")] += count
                    summary["total_recommendations"] += count
                    
                    # Count individual recommendations
                    for rec in day[category]:
                        if isinstance(rec, str):
                            recommendation_counts[rec] += 1
            
            # Count medication reminders
            if "medication_reminders" in day and isinstance(day["medication_reminders"], list):
                count = len(day["medication_reminders"])
                summary["categories"]["medication"] += count
                summary["total_recommendations"] += count
            
            # Count vaccination reminders
            if "vaccination_reminders" in day and isinstance(day["vaccination_reminders"], list):
                count = len(day["vaccination_reminders"])
                summary["categories"]["vaccination_reminders"] += count
                summary["total_recommendations"] += count
            
            # Count hydration reminders
            if "hydration_reminders" in day and isinstance(day["hydration_reminders"], list):
                count = len(day["hydration_reminders"])
                summary["categories"]["hydration_reminders"] += count
                summary["total_recommendations"] += count

        # Get most common recommendations
        sorted_recommendations = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)
        summary["most_common_recommendations"] = [
            {"recommendation": rec[0], "frequency": rec[1]} for rec in sorted_recommendations[:5]
        ]

        # Calculate adherence rate (placeholder - in production, track actual user adherence)
        summary["adherence_rate"] = 75.0  # Placeholder value

        return jsonify({
            "weekly_summary": summary
        }), 200

    except Exception as e:
        print(f"Error fetching weekly summary: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bp.route('/api/recommendations/categories', methods=['GET'])
@token_required
def get_recommendation_categories(current_user):
    """Get available recommendation categories and their counts."""
    try:
        # Get recommendations for today
        recommendations = recommendations_manager.get_user_recommendations(str(current_user['_id']))
        
        categories = {}
        for key, value in recommendations.items():
            if key not in ["user_id", "date", "generated_at"] and isinstance(value, (list, dict)):
                if isinstance(value, list):
                    categories[key] = len(value)
                else:
                    categories[key] = 1

        return jsonify({
            "categories": categories,
            "total_categories": len(categories),
            "total_recommendations": sum(categories.values())
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error fetching recommendation categories: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500