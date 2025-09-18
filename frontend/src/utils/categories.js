/**
 * Category constants and translations for Daily Scribe application.
 * 
 * This module contains shared category definitions used across the frontend.
 */

// Standard order for categories as they should appear in the digest
export const STANDARD_CATEGORY_ORDER = [
  'Politics',
  'Technology', 
  'Science and Health',
  'Business',
  'Entertainment',
  'Sports',
  'Other'
];

// Portuguese translations for categories
export const CATEGORY_TRANSLATIONS = {
  'Politics': 'Política',
  'Technology': 'Tecnologia',
  'Science and Health': 'Saúde e Ciência',
  'Business': 'Negócios',
  'Entertainment': 'Entretenimento',
  'Sports': 'Esportes',
  'Other': 'Outros'
};

// Reverse translation mapping (Portuguese to English)
export const CATEGORY_TRANSLATIONS_REVERSE = Object.fromEntries(
  Object.entries(CATEGORY_TRANSLATIONS).map(([key, value]) => [value, key])
);