/**
 * Custom hook for managing user preferences
 * Provides functions to fetch, update, and save preferences with debouncing
 */
import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Base URL for API calls
 */
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

/**
 * Hook for managing user preferences
 * @param {string} token - User's preference token
 * @returns {Object} Preference state and actions
 */
const usePreferences = (token) => {
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);
  const debounceTimerRef = useRef(null);

  /**
   * Fetches user preferences from the API
   */
  const fetchPreferences = useCallback(async () => {
    if (!token) {
      setError('No token provided');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/preferences/${token}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('INVALID_TOKEN');
        } else if (response.status === 403) {
          throw new Error('TOKEN_EXPIRED');
        } else {
          throw new Error('Failed to fetch preferences');
        }
      }

      const data = await response.json();
      setPreferences(data);
    } catch (err) {
      console.error('Error fetching preferences:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  /**
   * Saves preferences to the API
   */
  const savePreferences = useCallback(async (updatedPreferences = preferences) => {
    if (!token || !updatedPreferences) {
      return;
    }

    try {
      setSaving(true);
      setSaveStatus('saving');
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/preferences/${token}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updatedPreferences),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('INVALID_TOKEN');
        } else if (response.status === 403) {
          throw new Error('TOKEN_EXPIRED');
        } else {
          throw new Error('Failed to save preferences');
        }
      }

      const data = await response.json();
      setPreferences(data);
      setSaveStatus('saved');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError(err.message);
      setSaveStatus('error');
      
      // Clear error message after 5 seconds
      setTimeout(() => setSaveStatus(null), 5000);
    } finally {
      setSaving(false);
    }
  }, [token, preferences]);

  /**
   * Resets preferences to default values
   */
  const resetPreferences = useCallback(async () => {
    if (!token) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/preferences/${token}/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('INVALID_TOKEN');
        } else if (response.status === 403) {
          throw new Error('TOKEN_EXPIRED');
        } else {
          throw new Error('Failed to reset preferences');
        }
      }

      const data = await response.json();
      setPreferences(data);
      setSaveStatus('reset');
      
      // Clear message after 3 seconds
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (err) {
      console.error('Error resetting preferences:', err);
      setError(err.message);
      setSaveStatus('error');
      
      // Clear error message after 5 seconds
      setTimeout(() => setSaveStatus(null), 5000);
    } finally {
      setSaving(false);
    }
  }, [token]);

  /**
   * Optimistic update for better UX
   */
  const updatePreferencesOptimistically = useCallback((updates) => {
    setPreferences(prev => ({
      ...prev,
      ...updates
    }));
  }, []);

  /**
   * Debounced save function to avoid excessive API calls
   */
  const debouncedSave = useCallback((updatedPreferences) => {
    // Clear any existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      savePreferences(updatedPreferences);
    }, 1000);
  }, [savePreferences]);

  /**
   * Updates preferences with debounced saving
   */
  const updatePreferences = useCallback((updates) => {
    const updatedPreferences = {
      ...preferences,
      ...updates
    };
    
    // Update UI immediately (optimistic)
    updatePreferencesOptimistically(updates);
    
    // Save with debouncing
    debouncedSave(updatedPreferences);
  }, [preferences, updatePreferencesOptimistically, debouncedSave]);

  // Fetch preferences on mount or token change
  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return {
    preferences,
    loading,
    saving,
    error,
    saveStatus,
    fetchPreferences,
    savePreferences,
    updatePreferences,
    resetPreferences,
    updatePreferencesOptimistically,
  };
};

export default usePreferences;
