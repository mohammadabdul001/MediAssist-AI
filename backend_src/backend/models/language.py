from datetime import datetime
from bson import ObjectId
from .db import db
import json
import os
from collections import defaultdict

class LanguageSupport:
    def __init__(self):
        self.collection = db.language_translations
        self.users = db.users
        self.cache = {}  # In-memory cache for performance
        self.supported_languages = self._get_supported_languages()
        
        # Load translations into cache on initialization
        self._load_translations_to_cache()

    def _get_supported_languages(self):
        """Get all supported Indian languages with their codes and names."""
        # 22 Scheduled Languages of India (Constitution of India)
        languages = {
            "en": {"name": "English", "native_name": "English", "region": "All India"},
            "hi": {"name": "Hindi", "native_name": "हिन्दी", "region": "North India"},
            "bn": {"name": "Bengali", "native_name": "বাংলা", "region": "West Bengal, Tripura"},
            "te": {"name": "Telugu", "native_name": "తెలుగు", "region": "Andhra Pradesh, Telangana"},
            "mr": {"name": "Marathi", "native_name": "मराठी", "region": "Maharashtra"},
            "ta": {"name": "Tamil", "native_name": "தமிழ்", "region": "Tamil Nadu, Puducherry"},
            "ur": {"name": "Urdu", "native_name": "اردو", "region": "Jammu & Kashmir, Telangana, Uttar Pradesh"},
            "gu": {"name": "Gujarati", "native_name": "ગુજરાતી", "region": "Gujarat, Dadra & Nagar Haveli"},
            "kn": {"name": "Kannada", "native_name": "ಕನ್ನಡ", "region": "Karnataka"},
            "ml": {"name": "Malayalam", "native_name": "മലയാളം", "region": "Kerala, Lakshadweep"},
            "or": {"name": "Odia", "native_name": "ଓଡ଼ିଆ", "region": "Odisha"},
            "pa": {"name": "Punjabi", "native_name": "ਪੰਜਾਬੀ", "region": "Punjab"},
            "as": {"name": "Assamese", "native_name": "অসমীয়া", "region": "Assam"},
            "mai": {"name": "Maithili", "native_name": "मैथिली", "region": "Bihar, Jharkhand"},
            "sat": {"name": "Santali", "native_name": "ᱥᱟᱱᱛᱟᱞᱤ", "region": "Jharkhand, West Bengal, Odisha"},
            "ks": {"name": "Kashmiri", "native_name": "कश्मीरी", "region": "Jammu & Kashmir"},
            "doi": {"name": "Dogri", "native_name": "डोगरी", "region": "Jammu & Kashmir"},
            "mni": {"name": "Manipuri", "native_name": "মৈতৈলোন্", "region": "Manipur"},
            "ne": {"name": "Nepali", "native_name": "नेपाली", "region": "Sikkim, West Bengal"},
            "sd": {"name": "Sindhi", "native_name": "सिन्धी", "region": "Scattered across India"},
            "kok": {"name": "Konkani", "native_name": "कोंकणी", "region": "Goa, Karnataka, Maharashtra"},
            "brx": {"name": "Bodo", "native_name": "बर'", "region": "Assam"}
        }
        return languages

    def _load_translations_to_cache(self):
        """Load all translations into memory cache for performance."""
        try:
            # Get all translations from database
            translations = self.collection.find({})
            
            for trans in translations:
                lang_code = trans["language_code"]
                category = trans["category"]
                key = trans["key"]
                value = trans["value"]
                
                if lang_code not in self.cache:
                    self.cache[lang_code] = {}
                if category not in self.cache[lang_code]:
                    self.cache[lang_code][category] = {}
                
                self.cache[lang_code][category][key] = value
                
        except Exception as e:
            print(f"Error loading translations to cache: {str(e)}")

    def get_translation(self, language_code, category, key, default=None):
        """Get translation for a specific key in a specific language and category."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        # Try to get from cache first
        if language_code in self.cache and category in self.cache[language_code] and key in self.cache[language_code][category]:
            return self.cache[language_code][category][key]

        # If not in cache, get from database
        translation = self.collection.find_one({
            "language_code": language_code,
            "category": category,
            "key": key
        })

        if translation:
            # Add to cache
            if language_code not in self.cache:
                self.cache[language_code] = {}
            if category not in self.cache[language_code]:
                self.cache[language_code][category] = {}
            self.cache[language_code][category][key] = translation["value"]
            return translation["value"]

        # Return default if provided, otherwise return key
        return default if default is not None else key

    def get_all_translations_for_language(self, language_code):
        """Get all translations for a specific language."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        # Try to get from cache first
        if language_code in self.cache:
            return self.cache[language_code]

        # If not in cache, get from database
        translations = self.collection.find({"language_code": language_code})
        
        result = defaultdict(dict)
        for trans in translations:
            category = trans["category"]
            key = trans["key"]
            value = trans["value"]
            result[category][key] = value

        # Add to cache
        self.cache[language_code] = dict(result)
        
        return dict(result)

    def add_or_update_translation(self, language_code, category, key, value, updated_by=None):
        """Add or update a translation."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        # Update in database
        result = self.collection.update_one(
            {
                "language_code": language_code,
                "category": category,
                "key": key
            },
            {
                "$set": {
                    "value": value,
                    "updated_at": datetime.utcnow(),
                    "updated_by": updated_by
                }
            },
            upsert=True
        )

        # Update in cache
        if language_code not in self.cache:
            self.cache[language_code] = {}
        if category not in self.cache[language_code]:
            self.cache[language_code][category] = {}
        self.cache[language_code][category][key] = value

        return {
            "success": True,
            "language_code": language_code,
            "category": category,
            "key": key,
            "value": value,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }

    def bulk_update_translations(self, language_code, translations_data, updated_by=None):
        """Bulk update translations for a language."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        operations = []
        for category, keys in translations_data.items():
            for key, value in keys.items():
                operations.append({
                    "update_one": {
                        "filter": {
                            "language_code": language_code,
                            "category": category,
                            "key": key
                        },
                        "update": {
                            "$set": {
                                "value": value,
                                "updated_at": datetime.utcnow(),
                                "updated_by": updated_by
                            }
                        },
                        "upsert": True
                    }
                })

        if operations:
            # Execute bulk operations
            results = []
            for op in operations:
                result = self.collection.update_one(
                    op["update_one"]["filter"],
                    op["update_one"]["update"],
                    upsert=op["update_one"]["upsert"]
                )
                results.append({
                    "category": op["update_one"]["filter"]["category"],
                    "key": op["update_one"]["filter"]["key"],
                    "modified_count": result.modified_count,
                    "upserted_id": str(result.upserted_id) if result.upserted_id else None
                })

            # Update cache
            if language_code not in self.cache:
                self.cache[language_code] = {}
            
            for category, keys in translations_data.items():
                if category not in self.cache[language_code]:
                    self.cache[language_code][category] = {}
                for key, value in keys.items():
                    self.cache[language_code][category][key] = value

            return {
                "success": True,
                "language_code": language_code,
                "total_operations": len(operations),
                "results": results
            }

        return {"success": False, "message": "No translations provided"}

    def get_user_language(self, user_id):
        """Get user's preferred language."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        user = self.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")

        # Get language from user profile
        language_code = user.get("profile", {}).get("language", "en")
        
        # Validate language code
        if language_code not in self.supported_languages:
            language_code = "en"  # Default to English

        return language_code

    def set_user_language(self, user_id, language_code):
        """Set user's preferred language."""
        if not ObjectId.is_valid(user_id):
            raise ValueError("Invalid user ID format")

        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        # Update user profile
        result = self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"profile.language": language_code, "updated_at": datetime.utcnow()}}
        )

        if result.modified_count == 0:
            raise ValueError("User not updated")

        return {
            "success": True,
            "user_id": str(user_id),
            "language_code": language_code,
            "language_name": self.supported_languages[language_code]["name"],
            "native_name": self.supported_languages[language_code]["native_name"]
        }

    def translate_text(self, text, source_language="en", target_language="hi"):
        """Translate text from source language to target language."""
        if target_language not in self.supported_languages:
            raise ValueError(f"Unsupported target language: {target_language}")

        if source_language not in self.supported_languages:
            raise ValueError(f"Unsupported source language: {source_language}")

        # For exact matches, look up in translations
        # This is for UI elements and predefined content
        # For dynamic content, we would integrate with a translation API
        # But for now, we'll use our translation system

        # Look for exact match in translations
        translation = self.get_translation(target_language, "dynamic_content", text)
        if translation != text:  # If we found a translation
            return translation

        # If no exact match, try to find similar keys or use a simple mapping
        # In production, this would integrate with Google Translate API or similar
        # For now, return a placeholder with language code
        return f"[{target_language}] {text}"

    def get_language_stats(self):
        """Get statistics about language usage and translations."""
        stats = {
            "supported_languages": len(self.supported_languages),
            "languages": {},
            "total_translations": self.collection.count_documents({}),
            "categories": list(self.collection.distinct("category")),
            "updated_at": datetime.utcnow().isoformat()
        }

        for lang_code, lang_info in self.supported_languages.items():
            lang_stats = {
                "name": lang_info["name"],
                "native_name": lang_info["native_name"],
                "region": lang_info["region"],
                "total_translations": self.collection.count_documents({"language_code": lang_code}),
                "categories": list(self.collection.find({"language_code": lang_code}).distinct("category"))
            }
            stats["languages"][lang_code] = lang_stats

        return stats

    def get_missing_translations(self, language_code):
        """Get missing translations for a language (compared to English)."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        # Get all English translations as reference
        english_translations = self.get_all_translations_for_language("en")
        
        missing = defaultdict(list)
        
        for category, keys in english_translations.items():
            for key in keys.keys():
                # Check if translation exists for target language
                translation = self.get_translation(language_code, category, key, None)
                if translation is None:
                    missing[category].append(key)

        return dict(missing)

    def export_translations(self, language_code):
        """Export all translations for a language as JSON."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        translations = self.get_all_translations_for_language(language_code)
        
        export_data = {
            "language_code": language_code,
            "language_name": self.supported_languages[language_code]["name"],
            "native_name": self.supported_languages[language_code]["native_name"],
            "region": self.supported_languages[language_code]["region"],
            "exported_at": datetime.utcnow().isoformat(),
            "translations": translations
        }

        return export_data

    def import_translations(self, language_code, import_data, updated_by=None):
        """Import translations from JSON data."""
        if language_code not in self.supported_languages:
            raise ValueError(f"Unsupported language code: {language_code}")

        if not isinstance(import_data, dict) or "translations" not in import_:
            raise ValueError("Invalid import data format")

        translations_data = import_data["translations"]
        
        # Use bulk update
        result = self.bulk_update_translations(language_code, translations_data, updated_by)

        return result

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