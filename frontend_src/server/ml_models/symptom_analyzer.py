import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

class SymptomAnalyzer:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.symptoms_list = [
            'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing', 'shivering',
            'chills', 'joint_pain', 'stomach_pain', 'acidity', 'ulcers_on_tongue',
            'muscle_wasting', 'vomiting', 'burning_micturition', 'spotting_urination', 'fatigue',
            'weight_gain', 'anxiety', 'cold_hands_and_feets', 'mood_swings', 'weight_loss',
            'restlessness', 'lethargy', 'patches_in_throat', 'irregular_sugar_level', 'cough',
            'high_fever', 'sunken_eyes', 'breathlessness', 'sweating', 'dehydration',
            'indigestion', 'headache', 'yellowish_skin', 'dark_urine', 'nausea',
            'loss_of_appetite', 'pain_behind_the_eyes', 'back_pain', 'constipation', 'abdominal_pain',
            'diarrhoea', 'mild_fever', 'yellow_urine', 'yellowing_of_eyes', 'acute_liver_failure',
            'fluid_overload', 'swelling_of_stomach', 'swelled_lymph_nodes', 'malaise', 'blurred_and_distorted_vision',
            'phlegm', 'throat_irritation', 'redness_of_eyes', 'sinus_pressure', 'runny_nose',
            'congestion', 'chest_pain', 'weakness_in_limbs', 'fast_heart_rate', 'pain_during_bowel_movements',
            'pain_in_anal_region', 'bloody_stool', 'irritation_in_anus', 'neck_pain', 'dizziness',
            'cramps', 'bruising', 'obesity', 'swollen_legs', 'swollen_blood_vessels',
            'puffy_face_and_eyes', 'enlarged_thyroid', 'brittle_nails', 'swollen_extremeties', 'excessive_hunger',
            'extra_marital_contacts', 'drying_and_tingling_lips', 'slurred_speech', 'knee_pain', 'hip_joint_pain',
            'muscle_weakness', 'stiff_neck', 'swelling_joints', 'movement_stiffness', 'spinning_movements',
            'loss_of_balance', 'unsteadiness', 'weakness_of_one_body_side', 'loss_of_smell', 'bladder_discomfort',
            'foul_smell_of_urine', 'continuous_feel_of_urine', 'passage_of_gases', 'internal_itching', 'toxic_look_typhos',
            'depression', 'irritability', 'muscle_pain', 'altered_sensorium', 'red_spots_over_body',
            'belly_pain', 'abnormal_menstruation', 'dischromic_patches', 'watering_from_eyes', 'increased_appetite',
            'polyuria', 'family_history', 'mucoid_sputum', 'rusty_sputum', 'lack_of_concentration',
            'visual_disturbances', 'receiving_blood_transfusion', 'receiving_unsterile_injections', 'coma', 'stomach_bleeding',
            'distention_of_abdomen', 'history_of_alcohol_consumption', 'fluid_overload', 'blood_in_sputum', 'prominent_veins_on_calf',
            'palpitations', 'painful_walking', 'pus_filled_pimples', 'blackheads', 'scurring',
            'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails', 'inflammatory_nails', 'blister',
            'red_sore_around_nose', 'yellow_crust_ooze'
        ]
        
        self.diseases = [
            'Fungal infection', 'Allergy', 'GERD', 'Chronic cholestasis', 'Drug Reaction',
            'Peptic ulcer disease', 'AIDS', 'Diabetes', 'Gastroenteritis', 'Bronchial Asthma',
            'Hypertension', 'Migraine', 'Cervical spondylosis', 'Paralysis (brain hemorrhage)', 'Jaundice',
            'Malaria', 'Chicken pox', 'Dengue', 'Typhoid', 'hepatitis A',
            'Hepatitis B', 'Hepatitis C', 'Hepatitis D', 'Hepatitis E', 'Alcoholic hepatitis',
            'Tuberculosis', 'Common Cold', 'Pneumonia', 'Dimorphic hemorrhoids (piles)', 'Heart attack',
            'Varicose veins', 'Hypothyroidism', 'Hyperthyroidism', 'Hypoglycemia', 'Osteoarthritis',
            'Arthritis', '(vertigo) Paroxysmal Positional Vertigo', 'Acne', 'Urinary tract infection', 'Psoriasis',
            'Impetigo'
        ]
    
    def load_model(self):
        """Load pre-trained model or train new one"""
        try:
            self.model = joblib.load('symptom_model.pkl')
            self.label_encoders = joblib.load('label_encoders.pkl')
            print("Model loaded successfully")
        except:
            print("Training new model...")
            self.train_model()
    
    def train_model(self):
        """Train the symptom analysis model"""
        # Load training data (synthetic for demo)
        # In production, this would be real medical data
        training_data = self.generate_training_data()
        
        X = training_data.drop(['prognosis'], axis=1)
        y = training_data['prognosis']
        
        # Encode labels
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)
        self.label_encoders['prognosis'] = le
        
        # Train model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y_encoded)
        
        # Save model
        joblib.dump(self.model, 'symptom_model.pkl')
        joblib.dump(self.label_encoders, 'label_encoders.pkl')
        print("Model trained and saved successfully")
    
    def generate_training_data(self):
        """Generate synthetic training data for demo"""
        np.random.seed(42)
        n_samples = 5000
        
        data = []
        for _ in range(n_samples):
            disease = np.random.choice(self.diseases)
            symptoms = np.random.choice(self.symptoms_list, size=np.random.randint(3, 8), replace=False)
            
            row = {symptom: 0 for symptom in self.symptoms_list}
            for symptom in symptoms:
                row[symptom] = 1
            row['prognosis'] = disease
            data.append(row)
        
        return pd.DataFrame(data)
    
    def predict_disease(self, symptoms):
        """Predict disease based on symptoms"""
        if not self.model:
            self.load_model()
        
        # Create input vector
        input_vector = [0] * len(self.symptoms_list)
        for symptom in symptoms:
            if symptom in self.symptoms_list:
                idx = self.symptoms_list.index(symptom)
                input_vector[idx] = 1
        
        # Make prediction
        prediction = self.model.predict([input_vector])[0]
        disease = self.label_encoders['prognosis'].inverse_transform([prediction])[0]
        
        # Get probabilities
        probabilities = self.model.predict_proba([input_vector])[0]
        top_3 = sorted(
            [(self.label_encoders['prognosis'].inverse_transform([i])[0], prob) 
             for i, prob in enumerate(probabilities)],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            'predicted_disease': disease,
            'confidence': float(max(probabilities)),
            'top_predictions': [{'disease': d, 'probability': float(p)} for d, p in top_3]
        }
    
    def get_recommendations(self, disease, severity):
        """Get AI recommendations based on disease and severity"""
        recommendations = {
            'Fungal infection': {
                'low': ['Apply antifungal cream', 'Keep area dry and clean', 'Avoid sharing personal items'],
                'medium': ['Oral antifungal medication', 'Continue topical treatment', 'Monitor for improvement'],
                'high': ['Consult dermatologist immediately', 'Systemic antifungal treatment', 'Blood tests required']
            },
            'Allergy': {
                'low': ['Antihistamine medication', 'Avoid allergen', 'Monitor symptoms'],
                'medium': ['Prescription antihistamine', 'Allergy testing recommended', 'Consider immunotherapy'],
                'high': ['Emergency epinephrine available', 'Allergy specialist consultation', 'Carry medical alert']
            },
            'Diabetes': {
                'low': ['Monitor blood sugar regularly', 'Diet and exercise', 'Annual eye exam'],
                'medium': ['Medication adjustment needed', 'Endocrinologist consultation', 'HbA1c testing'],
                'high': ['Immediate medical attention', 'Hospitalization may be required', 'Specialist care']
            }
        }
        
        return recommendations.get(disease, {}).get(severity, ['Consult healthcare provider'])

if __name__ == "__main__":
    analyzer = SymptomAnalyzer()
    analyzer.train_model()
    
    # Test prediction
    test_symptoms = ['fever', 'headache', 'fatigue', 'nausea']
    result = analyzer.predict_disease(test_symptoms)
    print("Prediction:", result)
