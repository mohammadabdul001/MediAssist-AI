import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import os
from .db import db

class SymptomAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        
        # Load datasets
        self.severity_df = pd.read_csv(os.path.join(data_dir, 'Symptom-severity.csv'))
        self.description_df = pd.read_csv(os.path.join(data_dir, 'symptom_Description.csv'))
        self.precaution_df = pd.read_csv(os.path.join(data_dir, 'symptom_precaution.csv'))
        self.precaution_df = self.precaution_df.fillna('')  # Fill empty precautions
        
        # Train model
        self.model, self.label_encoder = self._train_model()
        self.db = db

    def _train_model(self):
        # Get list of diseases and symptoms
        diseases = self.description_df['Disease'].tolist()
        symptoms = self.severity_df['Symptom'].tolist()
        
        # Create synthetic training data (replace with real dataset in production)
        data = []
        np.random.seed(42)  # For reproducibility
        for disease in diseases:
            # Each disease associated with 3-5 random symptoms
            num_symptoms = np.random.randint(3, 6)
            selected_symptoms = np.random.choice(symptoms, size=num_symptoms, replace=False)
            for symptom in selected_symptoms:
                data.append({'Disease': disease, 'Symptom': symptom})
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # One-hot encode symptoms
        df_encoded = df.join(pd.get_dummies(df['Symptom']))
        df_encoded = df_encoded.drop('Symptom', axis=1)
        
        # Group by disease to create one row per disease (sum of symptom occurrences)
        X_grouped = df_encoded.groupby('Disease').sum().reset_index()
        y = X_grouped['Disease']
        X = X_grouped.drop('Disease', axis=1)
        
        # Encode labels
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y_encoded)
        
        return model, label_encoder

    def analyze(self, user_id, symptoms):
        """
        Analyze symptoms and return predictions with descriptions and precautions.
        Also saves analysis to user's health record history.
        """
        if not symptoms:
            raise ValueError("Symptom list cannot be empty")

        # Validate symptoms against known symptoms
        valid_symptoms = self.severity_df['Symptom'].tolist()
        symptoms = [s for s in symptoms if s in valid_symptoms]
        
        if not symptoms:
            raise ValueError("No valid symptoms provided. Please check spelling.")

        # Calculate severity score for risk assessment
        severity_map = dict(zip(self.severity_df['Symptom'], self.severity_df['weight']))
        total_severity = sum(severity_map.get(s, 0) for s in symptoms)
        max_possible_severity = len(symptoms) * 7  # Max weight is 7
        risk_percentage = min(100, (total_severity / max_possible_severity) * 100) if max_possible_severity > 0 else 0

        # Prepare feature vector for model
        all_symptoms = self.severity_df['Symptom'].tolist()
        feature_vector = [1 if symptom in symptoms else 0 for symptom in all_symptoms]
        
        # Get prediction probabilities
        probabilities = self.model.predict_proba([feature_vector])[0]
        
        # Get top 3 predictions
        top3_indices = probabilities.argsort()[-3:][::-1]
        top3_diseases = self.label_encoder.inverse_transform(top3_indices)
        top3_probs = probabilities[top3_indices]

        # Build results with descriptions and precautions
        results = []
        for disease, prob in zip(top3_diseases, top3_probs):
            # Get description
            desc_row = self.description_df[self.description_df['Disease'] == disease]
            description = desc_row['Description'].values[0] if len(desc_row) > 0 else "No description available."
            
            # Get precautions
            prec_row = self.precaution_df[self.precaution_df['Disease'] == disease]
            precautions = []
            if len(prec_row) > 0:
                row = prec_row.iloc[0]  # Get first (and only) row for this disease
                for i in range(1, 5):  # Precaution_1 to Precaution_4
                    col_name = f'Precaution_{i}'
                    if col_name in row and pd.notna(row[col_name]) and row[col_name].strip():
                        precautions.append(row[col_name].strip())
            
            results.append({
                "disease": disease,
                "probability": float(prob),
                "description": description,
                "precautions": precautions
            })

        # Save to user's health record history
        analysis_record = {
            "user_id": user_id,
            "type": "symptom_analysis",
            "symptoms": symptoms,
            "risk_percentage": risk_percentage,
            "predictions": results,
            "created_at": datetime.utcnow()
        }
        self.db.health_records.insert_one(analysis_record)

        # Return analysis result
        return {
            "user_id": user_id,
            "symptoms_analyzed": symptoms,
            "risk_percentage": round(risk_percentage, 2),
            "total_severity_score": total_severity,
            "predictions": results,
            "timestamp": datetime.utcnow().isoformat(),
            "disclaimer": "This analysis is for informational purposes only and not a substitute for professional medical advice."
        }