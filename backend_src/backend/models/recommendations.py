from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import random
from collections import defaultdict

class PersonalizedRecommendations:
    def __init__(self):
        self.collection = db.health_recommendations
        self.users = db.users
        self.health_records = db.health_records
        self.symptom_analyses = db.health_records  # Symptom analyses are stored as health_records with type="symptom_analysis"
        self.lab_tests = db.lab_tests
        self.medications = db.medications
        self.appointments = db.appointments

    def generate_daily_recommendations(self, user_id):
        """
        Generate personalized health recommendations for a user for the current day.
        This includes diet, exercise, medication reminders, and health tips.
        """
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        # Get user profile and health data
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Get user's health context
        health_context = self._get_user_health_context(user_id)

        # Generate recommendations based on health context
        recommendations = {
            "user_id": str(user_id),
            "date": datetime.utcnow().date().isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "dietary_recommendations": self._generate_dietary_recommendations(user, health_context),
            "exercise_recommendations": self._generate_exercise_recommendations(user, health_context),
            "medication_reminders": self._generate_medication_reminders(user_id, health_context),
            "health_tips": self._generate_health_tips(user, health_context),
            "seasonal_alerts": self._generate_seasonal_alerts(user, health_context),
            "vaccination_reminders": self._generate_vaccination_reminders(user, health_context),
            "hydration_reminders": self._generate_hydration_reminders(user, health_context),
            "sleep_recommendations": self._generate_sleep_recommendations(user, health_context)
        }

        # Save to database
        recommendation_record = {
            "user_id": ObjectId(user_id),
            "date": datetime.utcnow().date(),
            "recommendations": recommendations,
            "health_context": health_context,
            "created_at": datetime.utcnow()
        }
        self.collection.insert_one(recommendation_record)

        return recommendations

    def get_user_recommendations(self, user_id, date=None):
        """Get personalized recommendations for a user for a specific date."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        query = {"user_id": ObjectId(user_id)}
        if date:
            try:
                if isinstance(date, str):
                    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                else:
                    date_obj = date
                query["date"] = date_obj
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        else:
            query["date"] = datetime.utcnow().date()

        recommendation = self.collection.find_one(query, sort=[("created_at", -1)])
        if not recommendation:
            # Generate new recommendations if none exist for this date
            return self.generate_daily_recommendations(user_id)

        return recommendation["recommendations"]

    def get_recommendation_history(self, user_id, days=30):
        """Get recommendation history for a user."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        start_date = datetime.utcnow().date() - timedelta(days=days)
        recommendations = self.collection.find({
            "user_id": ObjectId(user_id),
            "date": {"$gte": start_date}
        }).sort("date", -1)

        return [rec["recommendations"] for rec in recommendations]

    def _get_user_health_context(self, user_id):
        """Get comprehensive health context for a user."""
        health_context = {
            "chronic_conditions": [],
            "recent_symptoms": [],
            "active_medications": [],
            "recent_lab_results": [],
            "vital_signs": {},
            "allergies": [],
            "dietary_preferences": [],
            "activity_level": "moderate",
            "age": None,
            "gender": None,
            "weight": None,
            "height": None,
            "bmi": None,
            "season": self._get_current_season(),
            "location": "general"
        }

        # Get user profile data
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if user:
            profile = user.get("profile", {})
            health_data = user.get("health_data", {})
            
            health_context["chronic_conditions"] = health_data.get("chronic_conditions", [])
            health_context["allergies"] = health_data.get("allergies", [])
            health_context["dietary_preferences"] = profile.get("dietary_preferences", [])
            health_context["activity_level"] = profile.get("activity_level", "moderate")
            health_context["age"] = profile.get("age")
            health_context["gender"] = profile.get("gender")
            health_context["weight"] = profile.get("weight")
            health_context["height"] = profile.get("height")
            
            # Calculate BMI
            if health_context["weight"] and health_context["height"]:
                try:
                    weight_kg = float(health_context["weight"])
                    height_m = float(health_context["height"]) / 100  # Convert cm to m
                    if height_m > 0:
                        health_context["bmi"] = round(weight_kg / (height_m * height_m), 2)
                except:
                    pass
            
            health_context["location"] = profile.get("address", "general")

        # Get recent symptom analyses (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_symptoms = list(self.symptom_analyses.find({
            "user_id": ObjectId(user_id),
            "type": "symptom_analysis",
            "created_at": {"$gte": seven_days_ago}
        }).sort("created_at", -1).limit(3))

        for analysis in recent_symptoms:
            if analysis.get("predictions"):
                top_prediction = analysis["predictions"][0]
                health_context["recent_symptoms"].append({
                    "disease": top_prediction["disease"],
                    "probability": top_prediction["probability"],
                    "risk_percentage": analysis.get("risk_percentage", 0),
                    "symptoms": analysis.get("symptoms_analyzed", [])
                })

        # Get active medications
        active_meds = list(self.medications.find({
            "user_id": ObjectId(user_id),
            "status": "active",
            "$or": [
                {"end_date": {"$gte": datetime.utcnow()}},
                {"end_date": None}
            ]
        }).limit(10))

        for med in active_meds:
            health_context["active_medications"].append({
                "name": med["name"],
                "dosage": med["dosage"],
                "frequency": med["frequency"],
                "side_effects": med.get("side_effects", []),
                "interactions": med.get("interactions", [])
            })

        # Get recent lab tests (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_lab_tests = list(self.lab_tests.find({
            "patient_id": ObjectId(user_id),
            "completed_at": {"$gte": thirty_days_ago},
            "status": "completed"
        }).sort("completed_at", -1).limit(5))

        for test in recent_lab_tests:
            health_context["recent_lab_results"].append({
                "test_name": test["test_name"],
                "results": test.get("results", {}),
                "interpretation": test.get("interpretation", ""),
                "completed_at": test.get("completed_at")
            })

        # Get recent vital signs (last 7 days)
        recent_vitals = self.health_records.find_one({
            "user_id": ObjectId(user_id),
            "type": "vitals",
            "created_at": {"$gte": seven_days_ago}
        }, sort=[("created_at", -1)])

        if recent_vitals:
            health_context["vital_signs"] = recent_vitals.get("data", {})

        return health_context

    def _generate_dietary_recommendations(self, user, health_context):
        """Generate personalized dietary recommendations."""
        recommendations = []
        
        # General healthy eating tips
        recommendations.extend([
            "Eat a variety of fruits and vegetables (aim for 5 servings per day)",
            "Choose whole grains over refined grains",
            "Include lean protein sources in your meals",
            "Limit added sugars and processed foods",
            "Stay hydrated by drinking plenty of water throughout the day"
        ])
        
        # Condition-specific recommendations
        for condition in health_context["chronic_conditions"]:
            if "diabetes" in condition.lower():
                recommendations.extend([
                    "Monitor carbohydrate intake and choose low-glycemic foods",
                    "Eat regular meals and snacks to maintain stable blood sugar",
                    "Include fiber-rich foods to help control blood sugar levels"
                ])
            elif "hypertension" in condition.lower():
                recommendations.extend([
                    "Reduce sodium intake to less than 2,300 mg per day",
                    "Increase potassium-rich foods like bananas, spinach, and sweet potatoes",
                    "Limit processed and packaged foods high in sodium"
                ])
            elif "heart disease" in condition.lower() or "cholesterol" in condition.lower():
                recommendations.extend([
                    "Choose heart-healthy fats (olive oil, avocados, nuts)",
                    "Limit saturated and trans fats",
                    "Include omega-3 rich foods like fatty fish, flaxseeds, and walnuts"
                ])
            elif "kidney" in condition.lower():
                recommendations.extend([
                    "Limit protein intake as recommended by your doctor",
                    "Monitor sodium, potassium, and phosphorus levels",
                    "Stay hydrated but don't overconsume fluids"
                ])
        
        # Medication-specific dietary advice
        for med in health_context["active_medications"]:
            if "metformin" in med["name"].lower():
                recommendations.append("Take metformin with meals to reduce stomach upset")
            elif "levothyroxine" in med["name"].lower():
                recommendations.append("Take levothyroxine on an empty stomach, at least 30 minutes before breakfast")
            elif "warfarin" in med["name"].lower():
                recommendations.append("Maintain consistent vitamin K intake (found in leafy greens) when taking warfarin")
        
        # Allergy-specific recommendations
        for allergy in health_context["allergies"]:
            recommendations.append(f"Avoid foods containing {allergy} and always check food labels")
        
        # BMI-based recommendations
        if health_context["bmi"]:
            if health_context["bmi"] < 18.5:
                recommendations.append("Consider increasing calorie intake with nutrient-dense foods to maintain a healthy weight")
            elif health_context["bmi"] >= 25 and health_context["bmi"] < 30:
                recommendations.append("Focus on portion control and regular physical activity to maintain a healthy weight")
            elif health_context["bmi"] >= 30:
                recommendations.append("Consider consulting a nutritionist for a personalized weight management plan")
        
        # Seasonal recommendations
        if health_context["season"] == "winter":
            recommendations.append("Include vitamin D rich foods or consider supplementation during winter months")
        elif health_context["season"] == "summer":
            recommendations.append("Increase fluid intake and include water-rich foods like watermelon and cucumber during hot weather")
        
        # Remove duplicates and limit to 8 recommendations
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:8]

    def _generate_exercise_recommendations(self, user, health_context):
        """Generate personalized exercise recommendations."""
        recommendations = []
        
        # General exercise guidelines
        recommendations.extend([
            "Aim for at least 150 minutes of moderate aerobic activity per week",
            "Include strength training exercises at least 2 days per week",
            "Incorporate flexibility and balance exercises into your routine",
            "Start slowly and gradually increase intensity and duration"
        ])
        
        # Condition-specific exercise recommendations
        for condition in health_context["chronic_conditions"]:
            if "arthritis" in condition.lower():
                recommendations.extend([
                    "Choose low-impact exercises like swimming, cycling, or walking",
                    "Include range-of-motion exercises to maintain joint flexibility",
                    "Apply heat before exercise and ice after to reduce pain and inflammation"
                ])
            elif "osteoporosis" in condition.lower():
                recommendations.extend([
                    "Include weight-bearing exercises like walking or dancing",
                    "Add resistance training to build bone density",
                    "Practice balance exercises to prevent falls"
                ])
            elif "heart disease" in condition.lower():
                recommendations.extend([
                    "Start with low-intensity exercises and gradually increase",
                    "Monitor your heart rate during exercise",
                    "Stop and rest if you experience chest pain, dizziness, or severe shortness of breath"
                ])
            elif "diabetes" in condition.lower():
                recommendations.extend([
                    "Exercise regularly to help control blood sugar levels",
                    "Check blood sugar before and after exercise",
                    "Carry a fast-acting carbohydrate source during exercise in case of hypoglycemia"
                ])
        
        # Age-based recommendations
        if health_context["age"]:
            if health_context["age"] < 18:
                recommendations.append("Include at least 60 minutes of physical activity daily for children and adolescents")
            elif health_context["age"] >= 65:
                recommendations.append("Focus on balance and flexibility exercises to prevent falls in older adults")
        
        # Activity level-based recommendations
        if health_context["activity_level"] == "sedentary":
            recommendations.append("Start with short 10-15 minute walks and gradually increase duration and frequency")
        elif health_context["activity_level"] == "active":
            recommendations.append("Consider cross-training to prevent overuse injuries and maintain motivation")
        
        # Recent symptom-based recommendations
        for symptom in health_context["recent_symptoms"]:
            if symptom["disease"] == "Muscle strain" or "pain" in symptom["disease"].lower():
                recommendations.append("Rest the affected area and apply ice for the first 48 hours, then heat")
            elif symptom["disease"] == "Vertigo" or "dizziness" in symptom["disease"].lower():
                recommendations.append("Avoid sudden movements and exercises that require rapid head position changes")
        
        # Remove duplicates and limit to 6 recommendations
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:6]

    def _generate_medication_reminders(self, user_id, health_context):
        """Generate medication reminders for the day."""
        reminders = []
        
        # Get today's date for scheduling
        today = datetime.utcnow().date()
        
        for med in health_context["active_medications"]:
            # Parse frequency to determine reminders
            frequency = med["frequency"].lower()
            reminder_times = []
            
            if "once daily" in frequency or "once a day" in frequency:
                reminder_times = ["08:00"]  # Morning
            elif "twice daily" in frequency or "two times" in frequency or "bid" in frequency:
                reminder_times = ["08:00", "20:00"]  # Morning and evening
            elif "three times" in frequency or "thrice" in frequency or "tid" in frequency:
                reminder_times = ["08:00", "12:00", "20:00"]  # Morning, noon, evening
            elif "four times" in frequency or "qid" in frequency:
                reminder_times = ["08:00", "12:00", "16:00", "20:00"]  # Every 4-6 hours
            elif "every 6 hours" in frequency:
                reminder_times = ["06:00", "12:00", "18:00", "00:00"]
            elif "every 8 hours" in frequency:
                reminder_times = ["08:00", "16:00", "00:00"]
            elif "every 12 hours" in frequency:
                reminder_times = ["08:00", "20:00"]
            elif "as needed" in frequency or "prn" in frequency:
                reminder_times = ["08:00"]  # Just one reminder to have available
            else:
                reminder_times = ["08:00"]  # Default to morning
            
            for time_str in reminder_times:
                reminders.append({
                    "medication": med["name"],
                    "dosage": med["dosage"],
                    "time": time_str,
                    "instructions": f"Take {med['dosage']} as prescribed",
                    "status": "pending"
                })
        
        # Sort reminders by time
        reminders.sort(key=lambda x: x["time"])
        return reminders

    def _generate_health_tips(self, user, health_context):
        """Generate general health tips based on user's health context."""
        tips = []
        
        # General wellness tips
        tips.extend([
            "Practice stress management techniques like meditation or deep breathing",
            "Maintain social connections for mental well-being",
            "Get regular health screenings appropriate for your age and gender",
            "Practice good sleep hygiene for better rest"
        ])
        
        # Condition-specific tips
        for condition in health_context["chronic_conditions"]:
            if "anxiety" in condition.lower() or "depression" in condition.lower():
                tips.extend([
                    "Practice mindfulness or meditation for 10-15 minutes daily",
                    "Maintain a consistent daily routine",
                    "Reach out to friends or family when feeling down",
                    "Consider talking to a mental health professional"
                ])
            elif "asthma" in condition.lower():
                tips.extend([
                    "Always carry your rescue inhaler",
                    "Avoid known triggers like smoke, dust, or pollen",
                    "Use a peak flow meter to monitor your lung function",
                    "Follow your asthma action plan"
                ])
            elif "migraine" in condition.lower():
                tips.extend([
                    "Identify and avoid your migraine triggers",
                    "Maintain a consistent sleep schedule",
                    "Stay hydrated and don't skip meals",
                    "Practice relaxation techniques to reduce stress"
                ])
        
        # Recent lab result-based tips
        for lab in health_context["recent_lab_results"]:
            if "cholesterol" in lab["test_name"].lower():
                for param, value in lab["results"].items():
                    if "ldl" in param.lower() and isinstance(value, str) and "mg/dl" in value:
                        try:
                            ldl_value = float(value.split()[0])
                            if ldl_value > 130:
                                tips.append("Your LDL cholesterol is elevated. Consider dietary changes and consult your doctor about management options")
                        except:
                            pass
            elif "blood glucose" in lab["test_name"].lower():
                for param, value in lab["results"].items():
                    if "fasting" in param.lower() and isinstance(value, str) and "mg/dl" in value:
                        try:
                            glucose_value = float(value.split()[0])
                            if glucose_value > 100:
                                tips.append("Your fasting blood glucose is elevated. Monitor your diet and consult your doctor about diabetes prevention")
                        except:
                            pass
        
        # Vital sign-based tips
        if "blood_pressure" in health_context["vital_signs"]:
            bp_str = health_context["vital_signs"]["blood_pressure"]
            try:
                systolic = int(bp_str.split("/")[0])
                if systolic > 130:
                    tips.append("Your blood pressure is elevated. Consider reducing sodium intake, increasing physical activity, and managing stress")
            except:
                pass
        
        # Remove duplicates and limit to 5 tips
        unique_tips = list(dict.fromkeys(tips))
        return unique_tips[:5]

    def _generate_seasonal_alerts(self, user, health_context):
        """Generate seasonal health alerts based on current season and location."""
        alerts = []
        season = health_context["season"]
        location = health_context["location"]
        
        if season == "winter":
            alerts.extend([
                "❄️ Winter Alert: Cold weather can exacerbate respiratory conditions. Dress warmly and limit outdoor exposure during extreme cold",
                "❄️ Flu Season: Consider getting a flu vaccine if you haven't already this season",
                "❄️ Indoor Air Quality: Use a humidifier to prevent dry air from irritating your respiratory system",
                "❄️ Vitamin D: Consider vitamin D supplementation during winter months when sunlight exposure is limited"
            ])
        elif season == "spring":
            alerts.extend([
                "🌸 Spring Alert: Pollen counts are high. If you have allergies, keep windows closed and shower after being outdoors",
                "🌸 Seasonal Cleaning: Spring cleaning can stir up dust and mold. Wear a mask if you're sensitive to allergens",
                "🌸 Outdoor Activities: Take advantage of milder weather to increase physical activity"
            ])
        elif season == "summer":
            alerts.extend([
                "☀️ Summer Alert: High temperatures can lead to heat exhaustion. Stay hydrated and avoid strenuous activity during peak heat",
                "☀️ Sun Protection: Use sunscreen with SPF 30+ and wear protective clothing when outdoors",
                "☀️ Food Safety: Be cautious with food at picnics and barbecues to prevent foodborne illness",
                "☀️ Hydration: Increase fluid intake, especially if you're active outdoors"
            ])
        elif season == "fall":
            alerts.extend([
                "🍂 Fall Alert: Temperature fluctuations can trigger respiratory issues. Dress in layers to adjust to changing temperatures",
                "🍂 Cold and Flu Season: Start preparing for cold and flu season by getting adequate sleep and nutrition",
                "🍂 Allergy Season: Ragweed and mold spores can trigger allergies. Keep windows closed and use air purifiers"
            ])
        
        # Location-specific alerts (simplified)
        if "city" in location.lower():
            alerts.append("🏙️ Urban Alert: Air pollution can affect respiratory health. Check air quality forecasts and limit outdoor activity on poor air quality days")
        elif "rural" in location.lower():
            alerts.append("🌾 Rural Alert: Be aware of agricultural chemicals and pesticides that may affect air quality")
        
        # Remove duplicates and limit to 4 alerts
        unique_alerts = list(dict.fromkeys(alerts))
        return unique_alerts[:4]

    def _generate_vaccination_reminders(self, user, health_context):
        """Generate vaccination reminders based on age, health conditions, and season."""
        reminders = []
        
        age = health_context["age"]
        current_year = datetime.utcnow().year
        
        # Annual flu vaccine
        reminders.append({
            "vaccine": "Influenza (Flu)",
            "recommended_for": "Everyone 6 months and older",
            "frequency": "Annual",
            "priority": "high",
            "reason": "Recommended annually for all individuals to prevent seasonal influenza"
        })
        
        # Age-based recommendations
        if age:
            if age >= 65:
                reminders.append({
                    "vaccine": "Pneumococcal",
                    "recommended_for": "Adults 65+",
                    "frequency": "One-time (PCV15/PCV20) or Two-dose series (PCV13 followed by PPSV23)",
                    "priority": "high",
                    "reason": "Recommended for adults 65+ to prevent pneumococcal disease"
                })
                reminders.append({
                    "vaccine": "Shingles (Herpes Zoster)",
                    "recommended_for": "Adults 50+",
                    "frequency": "Two-dose series",
                    "priority": "medium",
                    "reason": "Recommended for adults 50+ to prevent shingles and complications"
                })
            elif age >= 19 and age <= 26:
                reminders.append({
                    "vaccine": "HPV (Human Papillomavirus)",
                    "recommended_for": "Adults up to age 26",
                    "frequency": "Two or three-dose series",
                    "priority": "medium",
                    "reason": "Recommended for adults up to age 26 if not adequately vaccinated previously"
                })
            elif age >= 19 and age <= 59:
                reminders.append({
                    "vaccine": "Hepatitis B",
                    "recommended_for": "Adults 19-59",
                    "frequency": "Three-dose series",
                    "priority": "medium",
                    "reason": "Recommended for all adults 19-59 years old"
                })
        
        # Condition-based recommendations
        for condition in health_context["chronic_conditions"]:
            if "diabetes" in condition.lower():
                reminders.append({
                    "vaccine": "Hepatitis B",
                    "recommended_for": "People with diabetes",
                    "frequency": "Three-dose series",
                    "priority": "high",
                    "reason": "People with diabetes are at increased risk for hepatitis B infection"
                })
            elif "heart disease" in condition.lower() or "lung disease" in condition.lower():
                reminders.append({
                    "vaccine": "Pneumococcal",
                    "recommended_for": "People with chronic heart or lung disease",
                    "frequency": "As recommended by your doctor",
                    "priority": "high",
                    "reason": "People with chronic heart or lung disease are at increased risk for pneumococcal disease"
                })
        
        # Remove duplicates based on vaccine name
        unique_reminders = []
        seen_vaccines = set()
        for reminder in reminders:
            if reminder["vaccine"] not in seen_vaccines:
                unique_reminders.append(reminder)
                seen_vaccines.add(reminder["vaccine"])
        
        return unique_reminders

    def _generate_hydration_reminders(self, user, health_context):
        """Generate hydration reminders based on user's profile and conditions."""
        reminders = []
        
        # Calculate recommended daily water intake
        recommended_intake = "8 glasses (about 2 liters)"  # Default
        
        if health_context["weight"]:
            try:
                weight_kg = float(health_context["weight"])
                # General rule: 30-35 ml per kg of body weight
                ml_per_day = weight_kg * 35
                liters_per_day = ml_per_day / 1000
                recommended_intake = f"{round(liters_per_day, 1)} liters"
            except:
                pass
        
        # Condition-specific hydration advice
        conditions_affecting_hydration = []
        for condition in health_context["chronic_conditions"]:
            if "kidney" in condition.lower():
                conditions_affecting_hydration.append("kidney disease (follow your doctor's specific fluid recommendations)")
            elif "heart" in condition.lower():
                conditions_affecting_hydration.append("heart disease (may need to limit fluids)")
            elif "diabetes" in condition.lower():
                conditions_affecting_hydration.append("diabetes (increased risk of dehydration)")
        
        reminders.append({
            "message": f"💧 Aim to drink {recommended_intake} of water today",
            "frequency": "hourly",
            "times": ["09:00", "11:00", "13:00", "15:00", "17:00", "19:00"],
            "priority": "medium"
        })
        
        if conditions_affecting_hydration:
            reminders.append({
                "message": f"⚠️ Special hydration considerations: {', '.join(conditions_affecting_hydration)}",
                "frequency": "daily",
                "times": ["08:00"],
                "priority": "high"
            })
        
        # Seasonal hydration advice
        if health_context["season"] == "summer":
            reminders.append({
                "message": "☀️ Increase fluid intake during hot weather, especially if you're active outdoors",
                "frequency": "daily",
                "times": ["08:00"],
                "priority": "high"
            })
        elif health_context["season"] == "winter":
            reminders.append({
                "message": "❄️ Don't forget to stay hydrated in winter - cold air can be dehydrating",
                "frequency": "daily",
                "times": ["08:00"],
                "priority": "medium"
            })
        
        return reminders

    def _generate_sleep_recommendations(self, user, health_context):
        """Generate sleep recommendations based on user's profile and health context."""
        recommendations = []
        
        # General sleep hygiene tips
        recommendations.extend([
            "Maintain a consistent sleep schedule, even on weekends",
            "Create a relaxing bedtime routine",
            "Keep your bedroom cool, dark, and quiet",
            "Avoid screens (phones, tablets, computers) for at least 1 hour before bed",
            "Limit caffeine and alcohol, especially in the evening"
        ])
        
        # Age-based recommendations
        if health_context["age"]:
            if health_context["age"] < 18:
                recommendations.append("Teenagers need 8-10 hours of sleep per night for optimal health and development")
            elif health_context["age"] >= 65:
                recommendations.append("Older adults may experience changes in sleep patterns but still need 7-8 hours of sleep per night")
            else:
                recommendations.append("Adults need 7-9 hours of sleep per night for optimal health")
        
        # Condition-specific sleep recommendations
        for condition in health_context["chronic_conditions"]:
            if "insomnia" in condition.lower():
                recommendations.extend([
                    "Practice stimulus control: Use your bed only for sleep and sex",
                    "If you can't sleep after 20 minutes, get out of bed and do a relaxing activity",
                    "Consider cognitive behavioral therapy for insomnia (CBT-I)"
                ])
            elif "sleep apnea" in condition.lower():
                recommendations.extend([
                    "Use your CPAP machine consistently as prescribed",
                    "Sleep on your side rather than your back",
                    "Avoid alcohol and sedatives that can worsen sleep apnea"
                ])
            elif "anxiety" in condition.lower() or "depression" in condition.lower():
                recommendations.extend([
                    "Practice relaxation techniques before bed, such as deep breathing or progressive muscle relaxation",
                    "Write down worries or to-do lists before bed to clear your mind",
                    "Consider mindfulness meditation to reduce racing thoughts at night"
                ])
        
        # Medication-specific sleep advice
        for med in health_context["active_medications"]:
            if "stimulant" in med["name"].lower() or "add" in med["name"].lower():
                recommendations.append(f"Take {med['name']} early in the day to avoid interference with sleep")
            elif "diuretic" in med["name"].lower():
                recommendations.append(f"Take {med['name']} in the morning to avoid nighttime trips to the bathroom")
        
        # Remove duplicates and limit to 6 recommendations
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:6]

    def _get_current_season(self):
        """Get current season based on month."""
        month = datetime.utcnow().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def _serialize(self, obj):
        """Helper method to serialize MongoDB objects."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, ObjectId):
                    obj[key] = str(value)
                elif isinstance(value, datetime):
                    obj[key] = value.isoformat()
                elif isinstance(value, list):
                    obj[key] = [self._serialize(item) for item in value]
                elif isinstance(value, dict):
                    obj[key] = self._serialize(value)
        return obj