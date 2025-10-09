from datetime import datetime
from bson import ObjectId
from .db import db
import re
import json
from difflib import get_close_matches

class Chatbot:
    def __init__(self, symptom_analyzer, medication_manager):
        self.collection = db.chatbot_conversations
        self.users = db.users
        self.symptom_analyzer = symptom_analyzer
        self.medication_manager = medication_manager
        self.health_records = db.health_records
        self.emergency_sos = db.emergency_logs  # For SOS integration
        
        # Load symptom and disease data for NLP matching
        self.symptom_list = self._load_symptoms()
        self.disease_list = self._load_diseases()

    def _load_symptoms(self):
        """Load symptoms from Symptom-severity.csv for matching."""
        try:
            # In production, load from actual file or database
            # For now, use hardcoded list based on provided file
            symptoms = [
                "itching", "skin_rash", "nodal_skin_eruptions", "continuous_sneezing", 
                "shivering", "chills", "joint_pain", "stomach_pain", "acidity", 
                "ulcers_on_tongue", "muscle_wasting", "vomiting", "burning_micturition", 
                "spotting_urination", "fatigue", "weight_gain", "anxiety", 
                "cold_hands_and_feets", "mood_swings", "weight_loss", "restlessness", 
                "lethargy", "patches_in_throat", "irregular_sugar_level", "cough", 
                "high_fever", "sunken_eyes", "breathlessness", "sweating", "dehydration", 
                "indigestion", "headache", "yellowish_skin", "dark_urine", "nausea", 
                "loss_of_appetite", "pain_behind_the_eyes", "back_pain", "constipation", 
                "abdominal_pain", "diarrhoea", "mild_fever", "yellow_urine", 
                "yellowing_of_eyes", "acute_liver_failure", "fluid_overload", 
                "swelling_of_stomach", "swelled_lymph_nodes", "malaise", 
                "blurred_and_distorted_vision", "phlegm", "throat_irritation", 
                "redness_of_eyes", "sinus_pressure", "runny_nose", "congestion", 
                "chest_pain", "weakness_in_limbs", "fast_heart_rate", 
                "pain_during_bowel_movements", "pain_in_anal_region", "bloody_stool", 
                "irritation_in_anus", "neck_pain", "dizziness", "cramps", "bruising", 
                "obesity", "swollen_legs", "swollen_blood_vessels", "puffy_face_and_eyes", 
                "enlarged_thyroid", "brittle_nails", "swollen_extremeties", 
                "excessive_hunger", "extra_marital_contacts", "drying_and_tingling_lips", 
                "slurred_speech", "knee_pain", "hip_joint_pain", "muscle_weakness", 
                "stiff_neck", "swelling_joints", "movement_stiffness", "spinning_movements", 
                "loss_of_balance", "unsteadiness", "weakness_of_one_body_side", 
                "loss_of_smell", "bladder_discomfort", "foul_smell_ofurine", 
                "continuous_feel_of_urine", "passage_of_gases", "internal_itching", 
                "toxic_look_(typhos)", "depression", "irritability", "muscle_pain", 
                "altered_sensorium", "red_spots_over_body", "belly_pain", 
                "abnormal_menstruation", "dischromic_patches", "watering_from_eyes", 
                "increased_appetite", "polyuria", "family_history", "mucoid_sputum", 
                "rusty_sputum", "lack_of_concentration", "visual_disturbances", 
                "receiving_blood_transfusion", "receiving_unsterile_injections", "coma", 
                "stomach_bleeding", "distention_of_abdomen", "history_of_alcohol_consumption", 
                "fluid_overload", "blood_in_sputum", "prominent_veins_on_calf", 
                "palpitations", "painful_walking", "pus_filled_pimples", "blackheads", 
                "scurring", "skin_peeling", "silver_like_dusting", "small_dents_in_nails", 
                "inflammatory_nails", "blister", "red_sore_around_nose", "yellow_crust_ooze"
            ]
            return symptoms
        except Exception as e:
            print(f"Error loading symptoms: {str(e)}")
            return []

    def _load_diseases(self):
        """Load diseases from symptom_Description.csv for matching."""
        try:
            # In production, load from actual file or database
            # For now, use hardcoded list based on provided file
            diseases = [
                "Drug Reaction", "Malaria", "Allergy", "Hypothyroidism", "Psoriasis", 
                "GERD", "Chronic cholestasis", "hepatitis A", "Osteoarthristis", 
                "(vertigo) Paroymsal  Positional Vertigo", "Hypoglycemia", "Acne", 
                "Impetigo", "Diabetes", "Hypertension", "Peptic ulcer diseae", 
                "Dimorphic hemorrhoids(piles)", "Common Cold", "Chicken pox", 
                "Cervical spondylosis", "Hyperthyroidism", "Urinary tract infection", 
                "Varicose veins", "AIDS", "Paralysis (brain hemorrhage)", "Typhoid", 
                "Hepatitis B", "Fungal infection", "Hepatitis C", "Migraine", 
                "Bronchial Asthma", "Alcoholic hepatitis", "Jaundice", "Hepatitis E", 
                "Dengue", "Hepatitis D", "Heart attack", "Pneumonia", "Arthritis", 
                "Gastroenteritis", "Tuberculosis"
            ]
            return diseases
        except Exception as e:
            print(f"Error loading diseases: {str(e)}")
            return []

    def process_message(self, user_id, message, context=None):
        """Process user message and return AI response."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        # Get user language
        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")
        language = user.get("profile", {}).get("language", "en")

        # Initialize context if not provided
        context = context or {}

        # Process message based on content
        response_data = self._generate_response(user_id, message, context, language)

        # Save conversation history
        conversation = {
            "user_id": ObjectId(user_id),
            "message": message,
            "response": response_data["response"],
            "context": context,
            "language": language,
            "created_at": datetime.utcnow(),
            "type": response_data.get("type", "general")
        }
        self.collection.insert_one(conversation)

        return response_data

    def _generate_response(self, user_id, message, context, language):
        """Generate AI response based on message content."""
        message_lower = message.lower().strip()

        # Handle symptom analysis requests
        if "symptom" in message_lower or "symptoms" in message_lower or "symptoms:" in message_lower:
            return self._handle_symptom_query(user_id, message, language)

        # Handle disease precaution requests
        elif "precaution" in message_lower or "precautions" in message_lower:
            return self._handle_precaution_query(message, language)

        # Handle medication information requests
        elif "medication" in message_lower or "medicine" in message_lower or "drug" in message_lower:
            return self._handle_medication_query(user_id, message, language)

        # Handle emergency/SOS requests
        elif "emergency" in message_lower or "sos" in message_lower or "help" in message_lower:
            return self._handle_emergency_query(user_id, message, language)

        # Handle nearby hospital/pharmacy requests
        elif "nearby" in message_lower and ("hospital" in message_lower or "pharmacy" in message_lower or "doctor" in message_lower):
            return self._handle_nearby_query(message, language)

        # Handle general health tips
        elif "tip" in message_lower or "advice" in message_lower or "recommendation" in message_lower:
            return self._handle_health_tip_query(user_id, message, language)

        # Handle greeting messages
        elif any(greeting in message_lower for greeting in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
            return self._handle_greeting_query(user_id, language)

        # Default response
        else:
            return self._handle_default_query(message, language)

    def _handle_symptom_query(self, user_id, message, language):
        """Handle symptom analysis queries."""
        try:
            # Extract symptoms from message (look for "symptoms:" prefix or comma-separated list)
            symptoms = []
            
            if "symptoms:" in message.lower():
                # Extract symptoms after "symptoms:" keyword
                parts = message.split("symptoms:", 1)
                if len(parts) > 1:
                    symptom_text = parts[1].strip()
                    # Split by commas, semicolons, or "and"
                    symptom_list = re.split(r'[,;]|\s+and\s+', symptom_text)
                    for symptom in symptom_list:
                        symptom = symptom.strip().lower().replace(" ", "_")
                        # Find closest matching symptom
                        matches = get_close_matches(symptom, self.symptom_list, n=1, cutoff=0.6)
                        if matches:
                            symptoms.append(matches[0])
            else:
                # Look for symptom keywords in message
                for symptom in self.symptom_list:
                    if symptom.replace("_", " ") in message.lower() or symptom in message.lower():
                        symptoms.append(symptom)

            if not symptoms:
                return {
                    "type": "error",
                    "response": "I couldn't identify any symptoms in your message. Please try: 'symptoms: fever, cough, headache'"
                }

            # Perform symptom analysis
            analysis_result = self.symptom_analyzer.analyze(user_id, symptoms)

            # Generate response based on analysis
            top_prediction = analysis_result["predictions"][0] if analysis_result["predictions"] else None
            
            if top_prediction:
                response = f"Based on your symptoms, the most likely condition is {top_prediction['disease']} (confidence: {top_prediction['probability']:.1%}).\n\n"
                response += f"Description: {top_prediction['description']}\n\n"
                if top_prediction['precautions']:
                    response += "Precautions:\n" + "\n".join([f"- {p}" for p in top_prediction['precautions']])
                response += f"\n\nRisk level: {analysis_result['risk_percentage']}%"
                
                if analysis_result['risk_percentage'] > 70:
                    response += "\n\n⚠️ This appears to be a high-risk situation. Consider seeking medical attention immediately."
            else:
                response = "I analyzed your symptoms but couldn't determine a specific condition. Please consult a healthcare professional."

            return {
                "type": "symptom_analysis",
                "response": response,
                "data": analysis_result
            }

        except Exception as e:
            print(f"Error in symptom analysis: {str(e)}")
            return {
                "type": "error",
                "response": "Sorry, I encountered an error while analyzing your symptoms. Please try again later."
            }

    def _handle_precaution_query(self, message, language):
        """Handle disease precaution queries."""
        try:
            # Extract disease name from message
            disease = None
            
            # Look for disease names in message
            for d in self.disease_list:
                if d.lower() in message.lower():
                    disease = d
                    break
            
            if not disease:
                return {
                    "type": "error",
                    "response": "I couldn't identify a specific disease in your message. Please try: 'What are precautions for Malaria?'"
                }

            # Get precautions from symptom_analyzer
            # Note: In production, this would query the precaution_df directly
            # For now, we'll use a simplified approach
            precautions = self._get_disease_precautions(disease)
            
            if precautions:
                response = f"Precautions for {disease}:\n" + "\n".join([f"- {p}" for p in precautions])
            else:
                response = f"I don't have specific precautions for {disease}. Please consult a healthcare professional."

            return {
                "type": "precaution",
                "response": response,
                "disease": disease,
                "precautions": precautions
            }

        except Exception as e:
            print(f"Error in precaution query: {str(e)}")
            return {
                "type": "error",
                "response": "Sorry, I encountered an error while retrieving precautions. Please try again later."
            }

    def _get_disease_precautions(self, disease):
        """Get precautions for a disease (simplified version)."""
        # In production, this would query the actual symptom_precaution.csv file
        # For now, return dummy data based on disease name
        precaution_map = {
            "Malaria": ["Take complete bed rest", "Drink plenty of fluids", "Take antimalarial drugs as prescribed", "Use mosquito nets"],
            "Diabetes": ["Monitor blood sugar regularly", "Follow a balanced diet", "Exercise regularly", "Take medications/insulin as prescribed"],
            "Hypertension": ["Reduce salt intake", "Exercise regularly", "Maintain a healthy weight", "Take prescribed medications"],
            "Common Cold": ["Rest and stay hydrated", "Use saline nasal drops", "Gargle with warm salt water", "Over-the-counter cold remedies"],
            "Chicken pox": ["Stay at home until all blisters have crusted", "Keep nails short to prevent scratching", "Use calamine lotion for itching", "Take paracetamol for fever"],
            "AIDS": ["Take antiretroviral therapy (ART) as prescribed", "Practice safe sex", "Regular medical check-ups", "Maintain a healthy lifestyle"],
            "Heart attack": ["Call emergency services immediately", "Chew and swallow aspirin if not allergic", "Rest and stay calm", "Do not drive yourself to hospital"],
            "Dengue": ["Drink plenty of fluids", "Rest", "Use paracetamol for fever (avoid aspirin/NSAIDs)", "Monitor for warning signs (bleeding, severe pain)"],
            "Tuberculosis": ["Complete full course of TB medications", "Cover mouth when coughing", "Avoid close contact until non-infectious", "Regular follow-up with doctor"]
        }
        
        # Return precautions if disease is in map, otherwise return empty list
        return precaution_map.get(disease, [])

    def _handle_medication_query(self, user_id, message, language):
        """Handle medication information queries."""
        try:
            # Get user's medications
            medications = list(self.medication_manager.collection.find({
                "user_id": ObjectId(user_id),
                "status": "active"
            }))
            
            if "list" in message.lower() or "my medications" in message.lower():
                if medications:
                    response = "Your current medications:\n"
                    for med in medications:
                        response += f"- {med['name']}: {med['dosage']}, {med['frequency']}\n"
                        if med.get("reminders"):
                            response += f"  Reminders: {', '.join(med['reminders'])}\n"
                else:
                    response = "You don't have any active medications recorded. You can add medications in the Medication Tracker section."
                return {
                    "type": "medication_list",
                    "response": response,
                    "medications": medications
                }
            
            # Look for specific medication name
            med_name = None
            for med in medications:
                if med['name'].lower() in message.lower():
                    med_name = med['name']
                    break
            
            if med_name:
                med = next((m for m in medications if m['name'] == med_name), None)
                if med:
                    response = f"Medication: {med['name']}\n"
                    response += f"Dosage: {med['dosage']}\n"
                    response += f"Frequency: {med['frequency']}\n"
                    if med.get("side_effects"):
                        response += f"Side effects: {', '.join(med['side_effects'])}\n"
                    if med.get("interactions"):
                        response += f"Interactions: {', '.join(med['interactions'])}\n"
                    if med.get("reminders"):
                        response += f"Reminders: {', '.join(med['reminders'])}\n"
                    response += f"Status: {med['status']}"
                    return {
                        "type": "medication_info",
                        "response": response,
                        "medication": med
                    }
            
            # General medication advice
            return {
                "type": "medication_advice",
                "response": "I can help you manage your medications. You can ask me about your current medications, side effects, or reminders. Try: 'What are my medications?' or 'Tell me about [medication name]'"
            }

        except Exception as e:
            print(f"Error in medication query: {str(e)}")
            return {
                "type": "error",
                "response": "Sorry, I encountered an error while retrieving medication information. Please try again later."
            }

    def _handle_emergency_query(self, user_id, message, language):
        """Handle emergency/SOS queries."""
        try:
            # Check if user has emergency contacts
            user = self.users.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("emergency_contacts"):
                response = "⚠️ Emergency contacts not configured. Please add emergency contacts in your profile settings first.\n\n"
                response += "In a real emergency, call your local emergency number immediately."
                return {
                    "type": "emergency_setup",
                    "response": response
                }

            # Simulate SOS trigger (in production, this would call the actual SOS system)
            response = "🚨 EMERGENCY ALERT INITIATED\n\n"
            response += "I've notified your emergency contacts with your location and health status.\n\n"
            response += "While waiting for help, here are some first-aid instructions:\n"
            response += "- Stay calm and try to remain still\n"
            response += "- If you're having trouble breathing, sit in a comfortable position\n"
            response += "- If you're bleeding, apply pressure to the wound\n"
            response += "- If you're experiencing chest pain, chew an aspirin (if not allergic)\n\n"
            response += "Help is on the way!"

            # In production: trigger actual SOS system
            # self._trigger_sos(user_id, message)

            return {
                "type": "emergency_sos",
                "response": response,
                "emergency_contacts": user.get("emergency_contacts", [])
            }

        except Exception as e:
            print(f"Error in emergency query: {str(e)}")
            return {
                "type": "error",
                "response": "Sorry, I encountered an error while processing your emergency request. Please call your local emergency number immediately."
            }

    def _handle_nearby_query(self, message, language):
        """Handle nearby hospital/pharmacy queries."""
        try:
            location = "your location"  # In production, get from user profile or GPS
            if "hospital" in message.lower():
                response = f"🏥 Nearby hospitals in {location}:\n"
                response += "1. City General Hospital - 2.3 miles away\n"
                response += "2. Mercy Medical Center - 3.1 miles away\n"
                response += "3. Community Health Clinic - 1.8 miles away\n\n"
                response += "You can book an appointment through our Appointment Scheduling feature."
                entity_type = "hospital"
            elif "pharmacy" in message.lower():
                response = f"💊 Nearby pharmacies in {location}:\n"
                response += "1. CVS Pharmacy - 0.8 miles away\n"
                response += "2. Walgreens - 1.2 miles away\n"
                response += "3. Local Drug Store - 0.5 miles away\n\n"
                response += "You can request medication refills through our Medication Tracker."
                entity_type = "pharmacy"
            elif "doctor" in message.lower():
                response = f"👨‍⚕️ Nearby doctors in {location}:\n"
                response += "1. Dr. Smith (General Practice) - 1.5 miles away\n"
                response += "2. Dr. Johnson (Cardiology) - 2.0 miles away\n"
                response += "3. Dr. Williams (Pediatrics) - 1.8 miles away\n\n"
                response += "You can book a consultation through our Appointment Scheduling feature."
                entity_type = "doctor"
            else:
                response = "Please specify if you need a hospital, pharmacy, or doctor nearby."
                entity_type = "unknown"

            return {
                "type": "nearby_locations",
                "response": response,
                "entity_type": entity_type,
                "location": location
            }

        except Exception as e:
            print(f"Error in nearby query: {str(e)}")
            return {
                "type": "error",
                "response": "Sorry, I encountered an error while finding nearby locations. Please try again later."
            }

    def _handle_health_tip_query(self, user_id, message, language):
        """Handle health tip queries."""
        try:
            # Get user's health data for personalized tips
            user = self.users.find_one({"_id": ObjectId(user_id)})
            chronic_conditions = user.get("health_data", {}).get("chronic_conditions", []) if user else []
            
            tips = []
            
            # General health tips
            tips.extend([
                "💧 Stay hydrated by drinking at least 8 glasses of water daily",
                "😴 Get 7-9 hours of quality sleep each night",
                "🚶‍♂️ Aim for at least 30 minutes of moderate exercise most days",
                "🥗 Eat a balanced diet rich in fruits, vegetables, and whole grains",
                "🧘‍♀️ Practice stress management techniques like meditation or deep breathing"
            ])
            
            # Condition-specific tips
            if "diabetes" in [c.lower() for c in chronic_conditions]:
                tips.extend([
                    "🩸 Monitor your blood sugar levels regularly as recommended by your doctor",
                    "🍎 Choose low-glycemic foods to help control blood sugar spikes",
                    "👟 Regular physical activity can help improve insulin sensitivity"
                ])
            if "hypertension" in [c.lower() for c in chronic_conditions]:
                tips.extend([
                    "🧂 Reduce sodium intake to help control blood pressure",
                    "🏃‍♂️ Regular aerobic exercise can help lower blood pressure",
                    "🍷 Limit alcohol consumption to recommended levels"
                ])
            
            # Get recent symptom analysis for personalized tips
            recent_analysis = self.health_records.find_one({
                "user_id": ObjectId(user_id),
                "type": "symptom_analysis"
            }, sort=[("created_at", -1)])
            
            if recent_analysis and recent_analysis.get("risk_percentage", 0) > 50:
                tips.append("⚠️ Based on your recent symptom analysis, consider scheduling a follow-up with your healthcare provider")
            
            # Generate response
            response = "Here are some health tips for you:\n\n" + "\n".join([f"• {tip}" for tip in tips[:5]])  # Limit to 5 tips
            
            return {
                "type": "health_tips",
                "response": response,
                "tips": tips[:5],
                "personalized": len(chronic_conditions) > 0
            }

        except Exception as e:
            print(f"Error in health tip query: {str(e)}")
            return {
                "type": "error",
                "response": "Sorry, I encountered an error while generating health tips. Please try again later."
            }

    def _handle_greeting_query(self, user_id, language):
        """Handle greeting queries."""
        try:
            # Get user's name
            user = self.users.find_one({"_id": ObjectId(user_id)})
            username = user.get("username", "there") if user else "there"
            
            # Get time-based greeting
            current_hour = datetime.now().hour
            if current_hour < 12:
                greeting = "Good morning"
            elif current_hour < 17:
                greeting = "Good afternoon"
            else:
                greeting = "Good evening"
            
            response = f"{greeting}, {username}! 👋 I'm your MediAssist AI assistant. How can I help you today?\n\n"
            response += "You can ask me about:\n"
            response += "• Your symptoms (e.g., 'symptoms: fever, cough')\n"
            response += "• Medications and side effects\n"
            response += "• Health tips and recommendations\n"
            response += "• Nearby hospitals or pharmacies\n"
            response += "• Emergency assistance (say 'emergency' or 'SOS')\n\n"
            response += "What would you like to know?"

            return {
                "type": "greeting",
                "response": response,
                "username": username,
                "time_greeting": greeting
            }

        except Exception as e:
            print(f"Error in greeting query: {str(e)}")
            return {
                "type": "error",
                "response": "Hello! I'm your MediAssist AI assistant. How can I help you today?"
            }

    def _handle_default_query(self, message, language):
        """Handle default queries."""
        response = "I'm here to help with your health-related questions! You can ask me about:\n\n"
        response += "• Symptoms and possible conditions (try: 'symptoms: fever, cough')\n"
        response += "• Medications and side effects\n"
        response += "• Health tips and recommendations\n"
        response += "• Nearby hospitals or pharmacies\n"
        response += "• Emergency assistance (say 'emergency' or 'SOS')\n\n"
        response += "What would you like to know today?"

        return {
            "type": "help",
            "response": response
        }

    def get_conversation_history(self, user_id, limit=10):
        """Get conversation history for a user."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        conversations = self.collection.find({
            "user_id": ObjectId(user_id)
        }).sort("created_at", -1).limit(limit)

        return [self._serialize_conversation(conv) for conv in conversations]

    def clear_conversation_history(self, user_id):
        """Clear conversation history for a user."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        result = self.collection.delete_many({
            "user_id": ObjectId(user_id)
        })

        return {"success": True, "deleted_count": result.deleted_count}

    def _serialize_conversation(self, conversation):
        """Serialize conversation for JSON response."""
        if conversation:
            conversation["_id"] = str(conversation["_id"])
            conversation["user_id"] = str(conversation["user_id"])
            conversation["created_at"] = conversation["created_at"].isoformat()
        return conversation

    def _trigger_sos(self, user_id, message):
        """Trigger actual SOS system (stub for production implementation)."""
        try:
            # In production, this would integrate with the actual SOS system
            # For now, log to emergency_logs collection
            sos_log = {
                "user_id": ObjectId(user_id),
                "triggered_by": "chatbot",
                "message": message,
                "timestamp": datetime.utcnow(),
                "status": "triggered",
                "contacts_notified": []
            }
            self.emergency_sos.insert_one(sos_log)
            return True
        except Exception as e:
            print(f"Error triggering SOS: {str(e)}")
            return False