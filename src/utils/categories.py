"""
Category constants and translations for Daily Scribe application.

This module contains shared category definitions used across the application.
"""

from typing import Dict, List

# Standard order for categories as they should appear in the digest
STANDARD_CATEGORY_ORDER: List[str] = [
    'Politics', 
    'Technology', 
    'Science and Health', 
    'Business', 
    'Entertainment', 
    'Sports', 
    'Other'
]

# Portuguese translations for categories
CATEGORY_TRANSLATIONS: Dict[str, str] = {
    'Politics': 'Política',
    'Technology': 'Tecnologia',
    'Science and Health': 'Saúde E Ciência',
    'Business': 'Negócios',
    'Entertainment': 'Entretenimento',
    'Sports': 'Esportes',
    'Other': 'Outros'
}

# Reverse translation mapping (Portuguese to English)
CATEGORY_TRANSLATIONS_REVERSE: Dict[str, str] = {
    v: k for k, v in CATEGORY_TRANSLATIONS.items()
}