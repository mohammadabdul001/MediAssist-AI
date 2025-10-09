from models.language import LanguageSupport
from models.db import db
from datetime import datetime

def initialize_sample_translations():
    """Initialize database with sample translations for all Indian languages."""
    language_manager = LanguageSupport()
    
    # Sample UI translations
    ui_translations = {
        "welcome_message": "Welcome to MediAssist AI",
        "symptom_analysis": "Symptom Analysis",
        "health_records": "Health Records",
        "appointments": "Appointments",
        "medications": "Medications",
        "lab_tests": "Lab Tests",
        "health_analytics": "Health Analytics",
        "chatbot": "Chatbot Assistance",
        "emergency_sos": "Emergency SOS",
        "telemedicine": "Telemedicine",
        "recommendations": "Health Recommendations",
        "settings": "Settings",
        "logout": "Logout",
        "login": "Login",
        "register": "Register",
        "book_appointment": "Book Appointment",
        "view_results": "View Results",
        "take_medicine": "Take Medicine",
        "emergency_contact": "Emergency Contact",
        "language_preference": "Language Preference"
    }
    
    # Add translations for each language
    for lang_code in language_manager.supported_languages.keys():
        if lang_code == "en":
            continue  # Skip English as it's the default
            
        translations_data = {"ui": {}}
        
        for key, value in ui_translations.items():
            # In production, these would be actual translations
            # For now, we'll use a placeholder with the language code
            translations_data["ui"][key] = f"[{lang_code}] {value}"
        
        # Add some specific translations for Hindi as an example
        if lang_code == "hi":
            translations_data["ui"] = {
                "welcome_message": "मेडीअसिस्ट एआई में आपका स्वागत है",
                "symptom_analysis": "लक्षण विश्लेषण",
                "health_records": "स्वास्थ्य रिकॉर्ड",
                "appointments": "नियुक्तियाँ",
                "medications": "दवाइयाँ",
                "lab_tests": "प्रयोगशाला परीक्षण",
                "health_analytics": "स्वास्थ्य विश्लेषण",
                "chatbot": "चैटबॉट सहायता",
                "emergency_sos": "आपातकालीन एसओएस",
                "telemedicine": "टेलीमेडिसिन",
                "recommendations": "स्वास्थ्य सिफारिशें",
                "settings": "सेटिंग्स",
                "logout": "लॉग आउट",
                "login": "लॉगिन",
                "register": "पंजीकरण",
                "book_appointment": "नियुक्ति बुक करें",
                "view_results": "परिणाम देखें",
                "take_medicine": "दवा लें",
                "emergency_contact": "आपातकालीन संपर्क",
                "language_preference": "भाषा प्राथमिकता"
            }
        
        # Bulk update translations
        language_manager.bulk_update_translations(
            language_code=lang_code,
            translations_data=translations_data,
            updated_by="system"
        )
        
        print(f"Initialized translations for {lang_code} - {language_manager.supported_languages[lang_code]['name']}")

if __name__ == "__main__":
    initialize_sample_translations()