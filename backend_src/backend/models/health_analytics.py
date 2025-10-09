from datetime import datetime, timedelta
from bson import ObjectId
from .db import db
import numpy as np
import pandas as pd
from collections import defaultdict

class HealthAnalytics:
    def __init__(self):
        self.db = db
        self.health_records = db.health_records
        self.symptom_analyses = db.health_records  # Symptom analyses are stored as health_records with type="symptom_analysis"
        self.lab_tests = db.lab_tests
        self.medications = db.medications
        self.users = db.users

    def get_user_health_summary(self, user_id, days=30):
        """Get comprehensive health summary for a user over specified days."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")
        start_date = datetime.utcnow() - timedelta(days=days)
        # Get recent health records
        recent_records = list(self.health_records.find({
            "user_id": ObjectId(user_id),
            "created_at": {"$gte": start_date}
        }).sort("created_at", -1))
        # Get recent symptom analyses
        recent_symptoms = list(self.symptom_analyses.find({
            "user_id": ObjectId(user_id),
            "type": "symptom_analysis",
            "created_at": {"$gte": start_date}
        }).sort("created_at", -1))
        # Get recent lab tests
        recent_lab_tests = list(self.lab_tests.find({
            "patient_id": ObjectId(user_id),
            "completed_at": {"$gte": start_date}
        }).sort("completed_at", -1))
        # Get active medications
        active_medications = list(self.medications.find({
            "user_id": ObjectId(user_id),
            "status": "active",
            "$or": [
                {"end_date": {"$gte": datetime.utcnow()}},
                {"end_date": None}
            ]
        }))
        # Calculate key metrics
        summary = {
            "user_id": str(user_id),
            "period_days": days,
            "period_start": start_date.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "total_health_records": len(recent_records),
            "total_symptom_analyses": len(recent_symptoms),
            "total_completed_lab_tests": len(recent_lab_tests),
            "active_medications_count": len(active_medications),
            "health_trends": self._calculate_health_trends(user_id, days),
            "risk_factors": self._identify_risk_factors(user_id, recent_symptoms, recent_lab_tests, active_medications),
            "recommendations": self._generate_recommendations(user_id, recent_symptoms, recent_lab_tests, active_medications),
            "generated_at": datetime.utcnow().isoformat()
        }
        return summary

    def get_health_trend_analysis(self, user_id, metric, days=90):
        """Get trend analysis for a specific health metric over time."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")
        start_date = datetime.utcnow() - timedelta(days=days)
        # Different metrics require different data sources
        if metric in ["blood_pressure", "heart_rate", "blood_glucose", "weight", "temperature"]:
            # Get from vitals records
            pipeline = [
                {"$match": {
                    "user_id": ObjectId(user_id),
                    "type": "vitals",
                    "created_at": {"$gte": start_date},
                    f"data.{metric}": {"$exists": True}
                }},
                {"$sort": {"created_at": 1}},
                {"$project": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "value": f"$data.{metric}",
                    "created_at": 1
                }}
            ]
            data = list(self.health_records.aggregate(pipeline))
        elif metric == "symptom_severity":
            # Get from symptom analyses
            pipeline = [
                {"$match": {
                    "user_id": ObjectId(user_id),
                    "type": "symptom_analysis",
                    "created_at": {"$gte": start_date}
                }},
                {"$sort": {"created_at": 1}},
                {"$project": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                    "value": "$risk_percentage",
                    "created_at": 1
                }}
            ]
            data = list(self.symptom_analyses.aggregate(pipeline))
        elif metric == "medication_adherence":
            # Calculate adherence rate over time
            data = self._calculate_medication_adherence_trend(user_id, days)
        else:
            raise ValueError(f"Unsupported metric: {metric}")

        if not data:
            return {
                "user_id": str(user_id),
                "metric": metric,
                "days": days,
                "data_points": 0,
                "trend_data": [],
                "summary": "No data available for this metric",
                "trend_direction": "neutral"
            }

        # Calculate trend statistics
        values = [d["value"] for d in data if d["value"] is not None]
        if not values:
            avg_value = 0
            min_value = 0
            max_value = 0
            trend_direction = "neutral"
        else:
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            # Simple trend calculation (compare first and last 20% of values)
            if len(values) > 1:
                first_quintile = int(len(values) * 0.2)
                last_quintile = int(len(values) * 0.8)
                if first_quintile == 0:
                    first_quintile = 1
                if last_quintile >= len(values):
                    last_quintile = len(values) - 1
                early_avg = sum(values[:first_quintile]) / first_quintile if first_quintile > 0 else 0
                late_avg = sum(values[last_quintile:]) / (len(values) - last_quintile) if len(values) - last_quintile > 0 else 0
                if late_avg > early_avg * 1.1:
                    trend_direction = "increasing"
                elif late_avg < early_avg * 0.9:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "neutral"

        return {
            "user_id": str(user_id),
            "metric": metric,
            "days": days,
            "data_points": len(data),
            "trend_data": data,
            "statistics": {
                "average": round(avg_value, 2),
                "minimum": min_value,
                "maximum": max_value,
                "trend_direction": trend_direction
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_predictive_health_insights(self, user_id):
        """Generate predictive health insights based on user's health history."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")
        # Get user's health history
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")
        # Get recent symptom analyses (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent_symptoms = list(self.symptom_analyses.find({
            "user_id": ObjectId(user_id),
            "type": "symptom_analysis",
            "created_at": {"$gte": six_months_ago}
        }).sort("created_at", -1))
        # Get recent lab tests (last 6 months)
        recent_lab_tests = list(self.lab_tests.find({
            "patient_id": ObjectId(user_id),
            "completed_at": {"$gte": six_months_ago}
        }).sort("completed_at", -1))
        # Get chronic conditions from user profile
        chronic_conditions = user.get("health_data", {}).get("chronic_conditions", [])
        # Get medication history
        medications = list(self.medications.find({
            "user_id": ObjectId(user_id)
        }).sort("start_date", -1))
        # Generate predictive insights
        insights = []
        # Check for recurring symptoms
        symptom_frequency = defaultdict(int)
        for analysis in recent_symptoms:
            for symptom in analysis.get("symptoms", []):
                symptom_frequency[symptom] += 1
        for symptom, count in symptom_frequency.items():
            if count >= 3:  # Recurring symptom
                insights.append({
                    "type": "recurring_symptom",
                    "symptom": symptom,
                    "frequency": count,
                    "severity": "high" if count >= 5 else "medium",
                    "recommendation": f"Consider consulting a specialist about recurring {symptom}. Track frequency and triggers."
                })
        # Check for abnormal lab trends
        lab_trends = self._analyze_lab_trends(recent_lab_tests)
        insights.extend(lab_trends)
        # Check for medication interactions or adherence issues
        med_insights = self._analyze_medication_patterns(medications)
        insights.extend(med_insights)
        # Check for chronic condition management
        chronic_insights = self._analyze_chronic_conditions(chronic_conditions, recent_symptoms, recent_lab_tests)
        insights.extend(chronic_insights)
        # Generate risk scores
        risk_scores = self._calculate_risk_scores(user, recent_symptoms, recent_lab_tests, medications)
        return {
            "user_id": str(user_id),
            "insights": insights,
            "risk_scores": risk_scores,
            "recommendations": self._generate_preventive_recommendations(insights, risk_scores),
            "generated_at": datetime.utcnow().isoformat(),
            "disclaimer": "These insights are predictive and not a substitute for professional medical advice."
        }

    def compare_with_population(self, user_id, metric, demographic_group="general"):
        """Compare user's health metric with population averages."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")
        # Get user's data
        user_data = self.get_health_trend_analysis(user_id, metric, days=30)
        if not user_data["trend_data"]:
            raise ValueError("No data available for comparison")
        user_avg = user_data["statistics"]["average"]
        # Population benchmarks (in production, these would come from actual population studies)
        population_benchmarks = {
            "blood_pressure": {
                "general": {"systolic": 120, "diastolic": 80, "unit": "mmHg"},
                "age_18-30": {"systolic": 115, "diastolic": 75, "unit": "mmHg"},
                "age_31-50": {"systolic": 125, "diastolic": 80, "unit": "mmHg"},
                "age_51+": {"systolic": 130, "diastolic": 85, "unit": "mmHg"}
            },
            "heart_rate": {
                "general": {"average": 72, "unit": "bpm"},
                "age_18-30": {"average": 70, "unit": "bpm"},
                "age_31-50": {"average": 75, "unit": "bpm"},
                "age_51+": {"average": 78, "unit": "bpm"}
            },
            "blood_glucose": {
                "general": {"fasting": 90, "unit": "mg/dL"},
                "diabetic": {"fasting": 130, "unit": "mg/dL"},
                "prediabetic": {"fasting": 110, "unit": "mg/dL"}
            },
            "weight": {
                "male": {"average": 80, "unit": "kg"},
                "female": {"average": 65, "unit": "kg"},
                "age_18-30": {"average": 70, "unit": "kg"},
                "age_31-50": {"average": 75, "unit": "kg"}
            },
            "symptom_severity": {
                "general": {"average": 35, "unit": "%"},
                "chronic_illness": {"average": 55, "unit": "%"}
            }
        }
        # Get user's demographic info
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            demographic_group = "general"
        # Select appropriate benchmark
        benchmark = None
        if metric in population_benchmarks:
            benchmarks = population_benchmarks[metric]
            if demographic_group in benchmarks:
                benchmark = benchmarks[demographic_group]
            else:
                benchmark = benchmarks["general"]
        if not benchmark:
            # Create generic benchmark
            benchmark = {"average": user_avg * 0.9, "unit": ""}  # Assume user is slightly above average

        # Calculate comparison
        if isinstance(benchmark, dict) and "average" in benchmark:
            benchmark_value = benchmark["average"]
            difference = user_avg - benchmark_value
            percent_difference = (difference / benchmark_value * 100) if benchmark_value > 0 else 0
            if abs(percent_difference) < 10:
                comparison = "similar to"
                status = "normal"
            elif percent_difference > 0:
                comparison = "higher than"
                status = "elevated" if percent_difference > 20 else "slightly elevated"
            else:
                comparison = "lower than"
                status = "reduced" if percent_difference < -20 else "slightly reduced"
        else:
            comparison = "compared to"
            status = "unknown"
            difference = 0
            percent_difference = 0
            benchmark_value = 0

        return {
            "user_id": str(user_id),
            "metric": metric,
            "user_average": round(user_avg, 2),
            "benchmark_group": demographic_group,
            "benchmark_average": round(benchmark_value, 2),
            "unit": benchmark.get("unit", ""),
            "difference": round(difference, 2),
            "percent_difference": round(percent_difference, 2),
            "comparison": comparison,
            "status": status,
            "recommendation": self._generate_comparison_recommendation(metric, status, percent_difference),
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_wearable_data_analysis(self, user_id, device_type="smartwatch", days=30):
        """Analyze data from wearable devices."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")
        start_date = datetime.utcnow() - timedelta(days=days)

        # Fetch user to check athlete status
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Get wearable data (assuming it's stored in health_records with type="wearable_data")
        wearable_data = list(self.health_records.find({
            "user_id": ObjectId(user_id),
            "type": "wearable_data",
            "metadata.device_type": device_type,
            "created_at": {"$gte": start_date}
        }).sort("created_at", -1))

        # ✅ FIXED: was 'wearable_' → now 'wearable_data'
        if not wearable_data:
            return {
                "user_id": str(user_id),
                "device_type": device_type,
                "days": days,
                "data_points": 0,
                "summary": "No wearable data available",
                "metrics": {},
                "insights": [],
                "recommendations": []
            }

        # Analyze different metrics from wearable data
        metrics = defaultdict(list)
        for record in wearable_data:
            data = record.get("data", {})
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    metrics[key].append(value)

        # Calculate statistics for each metric
        analyzed_metrics = {}
        for metric, values in metrics.items():
            if len(values) > 0:
                analyzed_metrics[metric] = {
                    "count": len(values),
                    "average": round(sum(values) / len(values), 2),
                    "minimum": min(values),
                    "maximum": max(values),
                    "std_dev": round(np.std(values), 2) if len(values) > 1 else 0
                }

        # Generate insights from wearable data
        insights = []
        recommendations = []

        # Sleep analysis
        if "sleep_hours" in analyzed_metrics:
            sleep_avg = analyzed_metrics["sleep_hours"]["average"]
            if sleep_avg < 7:
                insights.append("Consistently getting less than 7 hours of sleep per night")
                recommendations.append("Aim for 7-9 hours of sleep per night for optimal health")
            elif sleep_avg > 9:
                insights.append("Consistently sleeping more than 9 hours per night")
                recommendations.append("Excessive sleep can be associated with health issues; consult your doctor if concerned")

        # Activity analysis
        if "steps" in analyzed_metrics:
            steps_avg = analyzed_metrics["steps"]["average"]
            if steps_avg < 5000:
                insights.append("Low daily step count (less than 5,000 steps)")
                recommendations.append("Try to increase daily activity; aim for at least 7,500-10,000 steps per day")
            elif steps_avg > 15000:
                insights.append("Very high daily step count (more than 15,000 steps)")
                recommendations.append("Ensure adequate rest and recovery with high activity levels")

        # Heart rate analysis
        if "resting_heart_rate" in analyzed_metrics:
            hr_avg = analyzed_metrics["resting_heart_rate"]["average"]
            if hr_avg > 80:
                insights.append("Elevated resting heart rate")
                recommendations.append("Consider stress management techniques and regular cardiovascular exercise")
            elif hr_avg < 60 and not user.get('is_athlete', False):
                insights.append("Low resting heart rate")
                recommendations.append("If experiencing dizziness or fatigue, consult your doctor about low heart rate")

        # Stress analysis
        if "stress_level" in analyzed_metrics:
            stress_avg = analyzed_metrics["stress_level"]["average"]
            if stress_avg > 7:
                insights.append("High average stress levels")
                recommendations.append("Practice stress-reduction techniques such as meditation, deep breathing, or yoga")

        return {
            "user_id": str(user_id),
            "device_type": device_type,
            "days": days,
            "data_points": len(wearable_data),
            "metrics": analyzed_metrics,
            "insights": insights,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    # --- Helper methods (unchanged except minor safety improvements) ---

    def _calculate_health_trends(self, user_id, days):
        trends = {}
        try:
            symptom_trend = self.get_health_trend_analysis(user_id, "symptom_severity", days)
            trends["symptom_severity"] = {
                "direction": symptom_trend["statistics"]["trend_direction"],
                "average_severity": symptom_trend["statistics"]["average"]
            }
        except:
            trends["symptom_severity"] = {"direction": "neutral", "average_severity": 0}

        try:
            med_adherence = self.get_health_trend_analysis(user_id, "medication_adherence", days)
            trends["medication_adherence"] = {
                "direction": med_adherence["statistics"]["trend_direction"],
                "average_adherence": med_adherence["statistics"]["average"]
            }
        except:
            trends["medication_adherence"] = {"direction": "neutral", "average_adherence": 0}
        return trends

    def _calculate_medication_adherence_trend(self, user_id, days):
        start_date = datetime.utcnow() - timedelta(days=days)
        medications = list(self.medications.find({
            "user_id": ObjectId(user_id),
            "$or": [
                {"start_date": {"$lte": datetime.utcnow()}},
                {"start_date": {"$gte": start_date, "$lte": datetime.utcnow()}}
            ]
        }))
        if not medications:
            return []
        trend_data = []
        current_date = start_date
        while current_date <= datetime.utcnow():
            daily_adherence = self._calculate_daily_adherence(user_id, medications, current_date)
            trend_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "value": daily_adherence,
                "created_at": current_date.isoformat()
            })
            current_date += timedelta(days=1)
        return trend_data

    def _calculate_daily_adherence(self, user_id, medications, date):
        total_doses = 0
        taken_doses = 0
        for med in medications:
            if med.get("start_date") and med["start_date"] > date:
                continue
            if med.get("end_date") and med["end_date"] < date:
                continue
            expected_doses = self._get_expected_doses_for_day(med, date)
            total_doses += expected_doses
            actual_doses = self._get_actual_doses_taken(med, date)
            taken_doses += actual_doses
        if total_doses == 0:
            return 100.0
        else:
            return round((taken_doses / total_doses) * 100, 2)

    def _get_expected_doses_for_day(self, medication, date):
        frequency = medication.get("frequency", "").lower()
        if "once daily" in frequency:
            return 1
        elif "twice daily" in frequency or "two times" in frequency:
            return 2
        elif "three times" in frequency or "thrice" in frequency:
            return 3
        elif "every 8 hours" in frequency:
            return 3
        elif "every 12 hours" in frequency:
            return 2
        elif "every 6 hours" in frequency:
            return 4
        else:
            return 1

    def _get_actual_doses_taken(self, medication, date):
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        dose_history = medication.get("dose_history", [])
        doses_taken = 0
        for dose in dose_history:
            taken_at = dose.get("taken_at")
            if taken_at and start_of_day <= taken_at <= end_of_day:
                doses_taken += 1
        return doses_taken

    def _identify_risk_factors(self, user_id, recent_symptoms, recent_lab_tests, active_medications):
        risk_factors = []
        high_severity_count = sum(1 for a in recent_symptoms if a.get("risk_percentage", 0) > 70)
        if high_severity_count >= 2:
            risk_factors.append({
                "type": "high_symptom_severity",
                "description": "Multiple high-severity symptom analyses in recent period",
                "severity": "high",
                "recommendation": "Consult a healthcare provider for comprehensive evaluation"
            })

        for test in recent_lab_tests:
            if test.get("status") == "completed" and test.get("results"):
                analysis = self._analyze_lab_results(test["test_name"], test["results"], test.get("reference_ranges", {}))
                if analysis.get("abnormal_values"):
                    risk_factors.append({
                        "type": "abnormal_lab_results",
                        "description": f"Abnormal results in {test['test_name']}",
                        "severity": "medium" if len(analysis["abnormal_values"]) < 3 else "high",
                        "details": analysis["abnormal_values"],
                        "recommendation": "Discuss these results with your doctor"
                    })

        for med in active_medications:
            if med.get("side_effects"):
                risk_factors.append({
                    "type": "medication_side_effects",
                    "description": f"Potential side effects from {med['name']}",
                    "severity": "low",
                    "details": med["side_effects"],
                    "recommendation": f"Monitor for these side effects and report any concerns to your doctor"
                })
            if med.get("interactions"):
                risk_factors.append({
                    "type": "medication_interactions",
                    "description": f"Potential interactions with {med['name']}",
                    "severity": "medium",
                    "details": med["interactions"],
                    "recommendation": f"Review all medications with your doctor or pharmacist to avoid interactions"
                })
        return risk_factors

    def _analyze_lab_trends(self, recent_lab_tests):
        insights = []
        test_groups = defaultdict(list)
        for test in recent_lab_tests:
            if test.get("status") == "completed" and test.get("results"):
                test_groups[test["test_name"]].append(test)

        for test_name, tests in test_groups.items():
            if len(tests) < 2:
                continue
            tests.sort(key=lambda x: x.get("completed_at", datetime.min))
            for param in tests[0].get("results", {}).keys():
                values = []
                dates = []
                for test in tests:
                    if param in test.get("results", {}):
                        try:
                            value = float(str(test["results"][param]).split()[0])
                            values.append(value)
                            dates.append(test.get("completed_at", datetime.min))
                        except:
                            continue
                if len(values) < 2:
                    continue
                first_value = values[0]
                last_value = values[-1]
                percent_change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
                if abs(percent_change) > 10:
                    direction = "increasing" if percent_change > 0 else "decreasing"
                    severity = "high" if abs(percent_change) > 25 else "medium"
                    insights.append({
                        "type": "lab_trend",
                        "test_name": test_name,
                        "parameter": param,
                        "trend": direction,
                        "percent_change": round(percent_change, 2),
                        "severity": severity,
                        "recommendation": f"{param} in {test_name} is {direction} significantly. Consult your doctor for interpretation."
                    })
        return insights

    def _analyze_medication_patterns(self, medications):
        insights = []
        recent_meds = [med for med in medications if med.get("start_date", datetime.min) > datetime.utcnow() - timedelta(days=30)]
        for med in recent_meds:
            missed = med.get("missed_doses", 0)
            total = med.get("total_doses", 1)
            if missed > total * 0.2:
                adherence_rate = ((total - missed) / total * 100) if total > 0 else 100
                insights.append({
                    "type": "poor_medication_adherence",
                    "medication": med["name"],
                    "adherence_rate": round(adherence_rate, 2),
                    "missed_doses": missed,
                    "severity": "high" if adherence_rate < 80 else "medium",
                    "recommendation": f"Consider setting more reminders or discussing alternative treatments with your doctor for {med['name']}"
                })

        if len(medications) > 1:
            interaction_pairs = []
            for i, med1 in enumerate(medications):
                for j, med2 in enumerate(medications[i+1:], i+1):
                    if (med2["name"] in med1.get("interactions", []) or
                        med1["name"] in med2.get("interactions", [])):
                        interaction_pairs.append((med1["name"], med2["name"]))
            if interaction_pairs:
                insights.append({
                    "type": "potential_medication_interactions",
                    "interactions": interaction_pairs,
                    "severity": "high",
                    "recommendation": "Review all medications with your doctor or pharmacist to identify and manage potential interactions"
                })
        return insights

    def _analyze_chronic_conditions(self, chronic_conditions, recent_symptoms, recent_lab_tests):
        insights = []
        for condition in chronic_conditions:
            condition_symptoms = self._get_condition_symptoms(condition)
            symptom_count = 0
            for analysis in recent_symptoms:
                for symptom in analysis.get("symptoms", []):
                    if symptom in condition_symptoms:
                        symptom_count += 1
            if symptom_count > 2:
                insights.append({
                    "type": "poor_chronic_condition_control",
                    "condition": condition,
                    "symptom_count": symptom_count,
                    "severity": "high",
                    "recommendation": f"Frequent symptoms related to {condition} suggest poor control. Consult your doctor for treatment adjustment."
                })

            condition_tests = self._get_condition_tests(condition)
            relevant_tests = [test for test in recent_lab_tests if test["test_name"] in condition_tests]
            abnormal_tests = []
            for test in relevant_tests:
                if test.get("status") == "completed" and test.get("results"):
                    analysis = self._analyze_lab_results(test["test_name"], test["results"], test.get("reference_ranges", {}))
                    if analysis.get("abnormal_values"):
                        abnormal_tests.append(test["test_name"])
            if abnormal_tests:
                insights.append({
                    "type": "abnormal_chronic_condition_tests",
                    "condition": condition,
                    "abnormal_tests": abnormal_tests,
                    "severity": "high",
                    "recommendation": f"Abnormal test results for {condition} management. Consult your doctor for treatment adjustment."
                })
        return insights

    def _get_condition_symptoms(self, condition):
        condition_symptoms = {
            "diabetes": ["increased_thirst", "frequent_urination", "extreme_hunger", "unexplained_weight_loss", "fatigue", "blurred_vision"],
            "hypertension": ["headache", "shortness_of_breath", "nosebleeds", "flushing", "dizziness"],
            "asthma": ["wheezing", "coughing", "shortness_of_breath", "chest_tightness"],
            "arthritis": ["joint_pain", "stiffness", "swelling", "reduced_range_of_motion"],
            "hypothyroidism": ["fatigue", "weight_gain", "cold_intolerance", "dry_skin", "constipation"],
            "hyperthyroidism": ["weight_loss", "rapid_heartbeat", "nervousness", "increased_appetite", "sweating"]
        }
        return condition_symptoms.get(condition.lower(), [])

    def _get_condition_tests(self, condition):
        condition_tests = {
            "diabetes": ["Blood Glucose", "HbA1c", "Lipid Profile"],
            "hypertension": ["Blood Pressure Monitoring", "Kidney Function Test", "Lipid Profile"],
            "asthma": ["Pulmonary Function Test", "Allergy Testing"],
            "arthritis": ["Rheumatoid Factor", "ESR", "CRP"],
            "hypothyroidism": ["Thyroid Function Test", "TSH"],
            "hyperthyroidism": ["Thyroid Function Test", "TSH", "Free T4"]
        }
        return condition_tests.get(condition.lower(), [])

    def _analyze_lab_results(self, test_name, results, reference_ranges):
        analysis = {
            "summary": "",
            "abnormal_values": [],
            "recommendations": [],
            "risk_assessment": "normal"
        }
        # Use .get() for safety
        if "Complete Blood Count" in test_name:
            hemoglobin = results.get("hemoglobin")
            if hemoglobin:
                try:
                    value = float(str(hemoglobin).split()[0])
                    if value < 12.0:
                        analysis["abnormal_values"].append({
                            "parameter": "hemoglobin",
                            "value": hemoglobin,
                            "status": "low",
                            "interpretation": "Possible anemia"
                        })
                        analysis["recommendations"].append("Consult your doctor about possible iron deficiency or other causes of anemia.")
                        analysis["risk_assessment"] = "moderate"
                    elif value > 15.5:
                        analysis["abnormal_values"].append({
                            "parameter": "hemoglobin",
                            "value": hemoglobin,
                            "status": "high",
                            "interpretation": "Possible polycythemia"
                        })
                        analysis["recommendations"].append("Consult your doctor about possible causes of elevated hemoglobin.")
                        analysis["risk_assessment"] = "moderate"
                except:
                    pass
        elif "Blood Glucose" in test_name:
            fasting_glucose = results.get("fasting_glucose")
            if fasting_glucose:
                try:
                    value = float(str(fasting_glucose).split()[0])
                    if value < 70:
                        analysis["abnormal_values"].append({
                            "parameter": "fasting_glucose",
                            "value": fasting_glucose,
                            "status": "low",
                            "interpretation": "Hypoglycemia"
                        })
                        analysis["recommendations"].append("If experiencing symptoms, consume 15-20 grams of fast-acting carbohydrates and recheck blood sugar after 15 minutes.")
                        analysis["risk_assessment"] = "high"
                    elif value > 100:
                        analysis["abnormal_values"].append({
                            "parameter": "fasting_glucose",
                            "value": fasting_glucose,
                            "status": "high",
                            "interpretation": "Possible prediabetes or diabetes"
                        })
                        analysis["recommendations"].append("Consult your doctor for further evaluation and possible HbA1c test.")
                        analysis["risk_assessment"] = "moderate"
                except:
                    pass
        return analysis

    def _calculate_risk_scores(self, user, recent_symptoms, recent_lab_tests, medications):
        scores = {
            "overall_health_risk": 0,
            "chronic_disease_risk": 0,
            "medication_risk": 0,
            "lifestyle_risk": 0
        }
        if recent_symptoms:
            avg_severity = sum(a.get("risk_percentage", 0) for a in recent_symptoms) / len(recent_symptoms)
            scores["overall_health_risk"] = min(100, avg_severity * 1.2)
        chronic_conditions = user.get("health_data", {}).get("chronic_conditions", [])
        scores["chronic_disease_risk"] = min(100, len(chronic_conditions) * 20)
        med_count = len(medications)
        interaction_count = sum(len(med.get("interactions", [])) for med in medications)
        scores["medication_risk"] = min(100, med_count * 10 + interaction_count * 5)
        scores["lifestyle_risk"] = 30
        return scores

    def _generate_recommendations(self, user_id, recent_symptoms, recent_lab_tests, active_medications):
        recommendations = []
        if recent_symptoms:
            high_severity_analyses = [a for a in recent_symptoms if a.get("risk_percentage", 0) > 70]
            if high_severity_analyses:
                recommendations.append("Schedule an appointment with a healthcare provider to discuss your recent high-severity symptoms.")
        for test in recent_lab_tests:
            if test.get("status") == "completed" and test.get("interpretation"):
                recommendations.append(f"Review your {test['test_name']} results: {test['interpretation']}")
        for med in active_medications:
            if med.get("missed_doses", 0) > 0:
                recommendations.append(f"Consider setting additional reminders for {med['name']} to improve adherence.")
        recommendations.extend([
            "Maintain a balanced diet rich in fruits, vegetables, and whole grains",
            "Engage in at least 30 minutes of moderate exercise most days of the week",
            "Ensure 7-9 hours of quality sleep each night",
            "Practice stress management techniques such as meditation or deep breathing",
            "Stay hydrated by drinking plenty of water throughout the day"
        ])
        return recommendations[:10]

    def _generate_preventive_recommendations(self, insights, risk_scores):
        recommendations = []
        if risk_scores.get("overall_health_risk", 0) > 70:
            recommendations.append("Schedule a comprehensive health check-up with your primary care provider")
        if risk_scores.get("chronic_disease_risk", 0) > 60:
            recommendations.append("Work with your doctor to develop a comprehensive chronic disease management plan")
        if risk_scores.get("medication_risk", 0) > 50:
            recommendations.append("Schedule a medication review with your pharmacist to identify and manage potential interactions")
        for insight in insights:
            if insight.get("type") == "recurring_symptom" and insight.get("severity") == "high":
                recommendations.append(f"Keep a detailed symptom diary for {insight['symptom']} to identify triggers and patterns")
            elif insight.get("type") == "lab_trend" and insight.get("severity") == "high":
                recommendations.append(f"Follow up with your doctor regarding the {insight['trend']} trend in {insight['parameter']}")
            elif insight.get("type") == "poor_medication_adherence" and insight.get("severity") == "high":
                recommendations.append(f"Discuss alternative treatment options or adherence strategies with your doctor for {insight['medication']}")
        if not any("vaccination" in r.lower() for r in recommendations):
            recommendations.append("Ensure you are up to date on recommended vaccinations based on your age and health status")
        if not any("screening" in r.lower() for r in recommendations):
            recommendations.append("Discuss appropriate health screenings with your doctor based on your age, gender, and risk factors")
        return recommendations[:8]

    def _generate_comparison_recommendation(self, metric, status, percent_difference):
        if status == "elevated":
            if metric == "blood_pressure":
                return "Your blood pressure is higher than average. Consider lifestyle modifications such as reducing sodium intake, increasing physical activity, and managing stress."
            elif metric == "blood_glucose":
                return "Your blood glucose levels are higher than average. Focus on a balanced diet, regular exercise, and maintaining a healthy weight."
            elif metric == "weight":
                return "Your weight is higher than average for your demographic group. Consider consulting a nutritionist for personalized dietary advice."
            else:
                return f"Your {metric} is higher than average. Consult your healthcare provider for personalized advice."
        elif status == "reduced":
            if metric == "blood_pressure":
                return "Your blood pressure is lower than average. If you're experiencing dizziness or fatigue, consult your doctor."
            elif metric == "weight":
                return "Your weight is lower than average for your demographic group. Ensure you're getting adequate nutrition and consult a healthcare provider if concerned."
            else:
                return f"Your {metric} is lower than average. Consult your healthcare provider for personalized advice."
        else:
            return f"Your {metric} is within normal range compared to the general population. Maintain your current healthy habits."

    def _serialize(self, obj):
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