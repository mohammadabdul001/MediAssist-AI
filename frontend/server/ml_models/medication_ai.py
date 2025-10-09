import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class MedicationAI:
    def __init__(self):
        self.adherence_model = None
        self.dosage_model = None
        self.scaler = StandardScaler()
        
    def load_models(self):
        """Load pre-trained medication AI models"""
        try:
            self.adherence_model = joblib.load('medication_adherence_model.pkl')
            self.dosage_model = joblib.load('dosage_optimization_model.pkl')
            self.scaler = joblib.load('medication_scaler.pkl')
            print("Medication AI models loaded successfully")
        except:
            print("Training new medication AI models...")
            self.train_models()
    
    def train_models(self):
        """Train medication adherence and dosage optimization models"""
        # Generate synthetic training data
        adherence_data = self.generate_adherence_data()
        dosage_data = self.generate_dosage_data()
        
        # Train adherence model
        X_adherence = adherence_data.drop(['adherence_rate'], axis=1)
        y_adherence = adherence_data['adherence_rate']
        
        self.adherence_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.adherence_model.fit(X_adherence, y_adherence)
        
        # Train dosage optimization model
        X_dosage = dosage_data.drop(['optimal_dosage'], axis=1)
        y_dosage = dosage_data['optimal_dosage']
        
        self.dosage_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.dosage_model.fit(X_dosage, y_dosage)
        
        # Save models
        joblib.dump(self.adherence_model, 'medication_adherence_model.pkl')
        joblib.dump(self.dosage_model, 'dosage_optimization_model.pkl')
        joblib.dump(self.scaler, 'medication_scaler.pkl')
        print("Medication AI models trained and saved")
    
    def generate_adherence_data(self):
        """Generate synthetic medication adherence data"""
        np.random.seed(42)
        n_samples = 10000
        
        data = []
        for _ in range(n_samples):
            age = np.random.randint(18, 90)
            gender = np.random.choice([0, 1])  # 0: male, 1: female
            medication_count = np.random.randint(1, 10)
            complexity = np.random.randint(1, 5)  # 1-5 scale
            side_effects = np.random.choice([0, 1])
            cost = np.random.uniform(10, 500)
            frequency = np.random.choice([1, 2, 3, 4])  # times per day
            reminder_usage = np.random.choice([0, 1])
            support_system = np.random.choice([0, 1])
            
            # Calculate adherence based on factors
            base_adherence = 0.8
            adherence = base_adherence - (complexity * 0.05) - (side_effects * 0.1) + (reminder_usage * 0.1) + (support_system * 0.05)
            adherence = max(0.3, min(1.0, adherence))
            
            data.append({
                'age': age,
                'gender': gender,
                'medication_count': medication_count,
                'complexity': complexity,
                'side_effects': side_effects,
                'cost': cost,
                'frequency': frequency,
                'reminder_usage': reminder_usage,
                'support_system': support_system,
                'adherence_rate': adherence
            })
        
        return pd.DataFrame(data)
    
    def generate_dosage_data(self):
        """Generate synthetic dosage optimization data"""
        np.random.seed(42)
        n_samples = 5000
        
        data = []
        for _ in range(n_samples):
            age = np.random.randint(18, 90)
            weight = np.random.uniform(40, 120)
            severity = np.random.randint(1, 10)
            kidney_function = np.random.uniform(0.3, 1.0)
            liver_function = np.random.uniform(0.3, 1.0)
            drug_type = np.random.choice([0, 1, 2])  # 0: analgesic, 1: antibiotic, 2: chronic
            
            # Calculate optimal dosage
            base_dosage = 100
            optimal_dosage = base_dosage * (weight / 70) * (severity / 5) * kidney_function * liver_function
            
            data.append({
                'age': age,
                'weight': weight,
                'severity': severity,
                'kidney_function': kidney_function,
                'liver_function': liver_function,
                'drug_type': drug_type,
                'optimal_dosage': optimal_dosage
            })
        
        return pd.DataFrame(data)
    
    def predict_adherence(self, patient_data):
        """Predict medication adherence rate"""
        if not self.adherence_model:
            self.load_models()
        
        features = pd.DataFrame([patient_data])
        prediction = self.adherence_model.predict(features)[0]
        return max(0.0, min(1.0, prediction))
    
    def optimize_dosage(self, patient_data):
        """Optimize medication dosage"""
        if not self.dosage_model:
            self.load_models()
        
        features = pd.DataFrame([patient_data])
        dosage = self.dosage_model.predict(features)[0]
        return max(0, dosage)
    
    def generate_reminders(self, medication_schedule, adherence_rate):
        """Generate personalized medication reminders"""
        reminders = []
        base_time = datetime.now()
        
        for med in medication_schedule:
            reminder_time = base_time + timedelta(hours=med['frequency'])
            
            # Adjust reminder based on adherence
            if adherence_rate < 0.7:
                reminder_time -= timedelta(minutes=15)  # Earlier reminder
                message = f"Important: Don't forget your {med['name']}!"
            elif adherence_rate < 0.9:
                message = f"Time for your {med['name']}"
            else:
                message = f"Medication reminder: {med['name']}"
            
            reminders.append({
                'medication': med['name'],
                'time': reminder_time.strftime('%H:%M'),
                'message': message,
                'type': 'notification' if adherence_rate > 0.8 else 'alarm'
            })
        
        return reminders
    
    def analyze_medication_interactions(self, medications):
        """Analyze potential drug interactions"""
        interactions = []
        
        # Common interaction patterns
        interaction_db = {
            'warfarin': ['aspirin', 'ibuprofen', 'amiodarone'],
            'metformin': ['contrast dye', 'alcohol'],
            'lisinopril': ['potassium supplements', 'nsaids'],
            'digoxin': ['amiodarone', 'verapamil', 'quinidine']
        }
        
        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                med1_name = med1['name'].lower()
                med2_name = med2['name'].lower()
                
                for drug, interactions_list in interaction_db.items():
                    if (drug in med1_name and any(int_drug in med2_name for int_drug in interactions_list)) or \
                       (drug in med2_name and any(int_drug in med1_name for int_drug in interactions_list)):
                        interactions.append({
                            'medications': [med1['name'], med2['name']],
                            'severity': 'moderate',
                            'description': f"Potential interaction between {med1['name']} and {med2['name']}",
                            'recommendation': 'Monitor closely and consult healthcare provider'
                        })
        
        return interactions
    
    def predict_side_effects(self, patient_profile, medication):
        """Predict potential side effects"""
        risk_factors = {
            'age': patient_profile.get('age', 50),
            'gender': patient_profile.get('gender', 'unknown'),
            'kidney_function': patient_profile.get('kidney_function', 1.0),
            'liver_function': patient_profile.get('liver_function', 1.0),
            'allergies': patient_profile.get('allergies', [])
        }
        
        # Side effect database
        side_effects_db = {
            'metformin': ['nausea', 'diarrhea', 'stomach upset'],
            'lisinopril': ['dry cough', 'dizziness', 'hyperkalemia'],
            'atorvastatin': ['muscle pain', 'liver enzyme elevation'],
            'warfarin': ['bleeding', 'bruising']
        }
        
        predicted_effects = []
        med_name = medication['name'].lower()
        
        for drug, effects in side_effects_db.items():
            if drug in med_name:
                predicted_effects.extend(effects)
        
        return {
            'medication': medication['name'],
            'predicted_side_effects': predicted_effects,
            'risk_level': 'low' if len(predicted_effects) < 2 else 'moderate'
        }

if __name__ == "__main__":
    ai = MedicationAI()
    ai.train_models()
    
    # Test predictions
    patient_data = {
        'age': 45,
        'gender': 0,
        'medication_count': 3,
        'complexity': 2,
        'side_effects': 0,
        'cost': 50,
        'frequency': 2,
        'reminder_usage': 1,
        'support_system': 1
    }
    
    adherence = ai.predict_adherence(patient_data)
    print(f"Predicted adherence: {adherence:.2%}")
