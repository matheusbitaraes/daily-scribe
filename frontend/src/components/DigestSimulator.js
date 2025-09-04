import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import DigestDatePicker from './DigestDatePicker';
import DigestFilters from './DigestFilters';
import DigestPreview from './DigestPreview';
import './DigestSimulator.css';

const DigestSimulator = () => {
  // State management for the simulator
  const [state, setState] = useState({
    // User input
    userEmail: 'matheusbitaraesdenovaes@gmail.com', // Default for testing
    selectedDate: null,
    filters: {
      categories: [],
      sources: []
    },
    
    // Data from API
    availableDates: [],
    categories: [],
    sources: [],
    
    // Generated content
    digestContent: null,
    digestMetadata: null,
    
    // UI states
    isLoadingDates: false,
    isLoadingDigest: false,
    isLoadingMetadata: false,
    
    // Error handling
    error: null,
    dateError: null,
    digestError: null
  });

  const API_BASE_URL = 'http://localhost:8000';

  // Helper function to update state
  const updateState = useCallback((updates) => {
    setState(prevState => ({ ...prevState, ...updates }));
  }, []);

  // Load available dates on component mount
  useEffect(() => {
    loadAvailableDates();
    loadFilterOptions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load available dates from API
  const loadAvailableDates = async () => {
    updateState({ isLoadingDates: true, dateError: null });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/digest/available-dates`);
      const data = response.data;
      
      if (data.success) {
        updateState({
          availableDates: data.dates,
          isLoadingDates: false,
          // Auto-select the most recent date
          selectedDate: data.dates.length > 0 ? data.dates[0].date : null
        });
      } else {
        throw new Error(data.message || 'Failed to load available dates');
      }
    } catch (error) {
      console.error('Error loading available dates:', error);
      updateState({
        dateError: error.response?.data?.detail || error.message || 'Failed to load available dates',
        isLoadingDates: false,
        availableDates: []
      });
    }
  };

  // Load filter options (categories and sources)
  const loadFilterOptions = async () => {
    try {
      const [categoriesResponse, sourcesResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/categories`),
        axios.get(`${API_BASE_URL}/sources`)
      ]);
      
      updateState({
        categories: categoriesResponse.data || [],
        sources: sourcesResponse.data || []
      });
    } catch (error) {
      console.error('Error loading filter options:', error);
      // Don't show error for filter options as it's not critical
    }
  };

  // Generate digest simulation
  const generateDigest = async () => {
    if (!state.userEmail.trim()) {
      updateState({ digestError: 'Please enter a valid email address' });
      return;
    }

    updateState({ isLoadingDigest: true, digestError: null, digestContent: null });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/digest/simulate`, {
        params: { user_email: state.userEmail.trim() }
      });
      
      const data = response.data;
      
      if (data.success) {
        updateState({
          digestContent: data.html_content,
          digestMetadata: data.metadata,
          isLoadingDigest: false
        });
        
        // Also load metadata for the selected date if available
        if (state.selectedDate) {
          loadDigestMetadata(state.selectedDate);
        }
      } else {
        throw new Error(data.message || 'Failed to generate digest');
      }
    } catch (error) {
      console.error('Error generating digest:', error);
      updateState({
        digestError: error.response?.data?.detail || error.message || 'Failed to generate digest',
        isLoadingDigest: false
      });
    }
  };

  // Load metadata for selected date
  const loadDigestMetadata = async (date) => {
    if (!date) return;
    
    updateState({ isLoadingMetadata: true });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/digest/metadata/${date}`);
      const data = response.data;
      
      updateState({
        digestMetadata: data,
        isLoadingMetadata: false
      });
    } catch (error) {
      console.error('Error loading digest metadata:', error);
      updateState({ isLoadingMetadata: false });
      // Don't show error for metadata as it's supplementary information
    }
  };

  // Handle user email change
  const handleEmailChange = (email) => {
    updateState({ userEmail: email, digestError: null });
  };

  // Handle date selection (will be used by date picker component)
  const handleDateChange = (date) => {
    updateState({ selectedDate: date });
    if (date) {
      loadDigestMetadata(date);
    }
  };

  // Handle filter changes (will be used by filter components)
  const handleFiltersChange = (newFilters) => {
    updateState({
      filters: newFilters
    });
  };

  // Handle copy to clipboard callback from DigestPreview
  const handleCopyToClipboard = (status) => {
    if (status === 'success') {
      // Could show a toast notification here
      console.log('Content copied to clipboard successfully');
    } else {
      console.error('Failed to copy content to clipboard');
    }
  };

  // Handle export callback from DigestPreview
  const handleExport = (format) => {
    console.log(`Exporting digest in ${format} format`);
    // Could track analytics or show notifications here
  };

  // Clear all errors
  const clearErrors = () => {
    updateState({ error: null, dateError: null, digestError: null });
  };

  return (
    <div className="digest-simulator">
      <div className="simulator-header">
        <h1>Email Digest Simulator</h1>
        <p>Simulate and preview email digests for any user and date</p>
      </div>

      {/* Error Display */}
      {(state.error || state.dateError || state.digestError) && (
        <div className="error-banner">
          <div className="error-content">
            <strong>Error:</strong> {state.error || state.dateError || state.digestError}
            <button onClick={clearErrors} className="error-close">×</button>
          </div>
        </div>
      )}

      <div className="simulator-content">
        {/* User Input Section */}
        <div className="simulator-section">
          <h2>User Configuration</h2>
          <div className="user-input">
            <label htmlFor="userEmail">User Email:</label>
            <input
              id="userEmail"
              type="email"
              value={state.userEmail}
              onChange={(e) => handleEmailChange(e.target.value)}
              placeholder="Enter user email address"
              className="email-input"
            />
          </div>
        </div>

        {/* Date Selection Section */}
        <div className="simulator-section">
          <DigestDatePicker
            availableDates={state.availableDates}
            selectedDate={state.selectedDate}
            onDateChange={handleDateChange}
            isLoading={state.isLoadingDates}
          />
        </div>

        {/* Filters Section */}
        <div className="simulator-section">
          <DigestFilters
            onFiltersChange={handleFiltersChange}
            selectedCategories={state.filters.categories}
            selectedSources={state.filters.sources}
            isLoading={state.isLoadingDigest}
          />
        </div>

        {/* Generate Button */}
        <div className="simulator-section">
          <button
            onClick={generateDigest}
            disabled={state.isLoadingDigest || !state.userEmail.trim()}
            className="generate-button"
          >
            {state.isLoadingDigest ? 'Generating Digest...' : 'Generate Digest Preview'}
          </button>
        </div>

        {/* Preview Section */}
        <div className="simulator-section">
          <DigestPreview
            digestContent={state.digestContent}
            digestMetadata={state.digestMetadata}
            isLoading={state.isLoadingDigest}
            error={state.digestError}
            onCopyToClipboard={handleCopyToClipboard}
            onExport={handleExport}
          />
        </div>
      </div>
    </div>
  );
};

export default DigestSimulator;
