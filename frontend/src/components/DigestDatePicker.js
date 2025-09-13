import React, { useState } from 'react';

const DigestDatePicker = ({ 
  availableDates = [], 
  selectedDate, 
  onDateChange, 
  isLoading = false 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Format date for display
  const formatDisplayDate = (dateString) => {
    if (!dateString) return 'Select a date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Handle date selection
  const handleDateSelect = (dateString) => {
    onDateChange(dateString);
    setIsOpen(false);
  };

  // Get the display text for selected date
  const getSelectedDateInfo = () => {
    if (!selectedDate) return { display: 'Select a date', count: 0 };
    
    const selectedDateObj = availableDates.find(d => d.date === selectedDate);
    return {
      display: formatDisplayDate(selectedDate),
      count: selectedDateObj?.article_count || 0
    };
  };

  const selectedInfo = getSelectedDateInfo();

  if (isLoading) {
    return (
      <div className="digest-date-picker">
        <h2>Date</h2>
        <div className="date-picker-loading">
          <div className="loading-spinner"></div>
          <span>Loading dates...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="digest-date-picker">
      <h2>Date</h2>
      
      <div className="date-dropdown">
        <button 
          className={`date-dropdown-trigger ${isOpen ? 'open' : ''}`}
          onClick={() => setIsOpen(!isOpen)}
          disabled={availableDates.length === 0}
        >
          <div className="selected-date-info">
            <span className="date-text">{selectedInfo.display}</span>
            {selectedInfo.count > 0 && (
              <span className="article-count">{selectedInfo.count} articles</span>
            )}
          </div>
          <span className="dropdown-arrow">▼</span>
        </button>

        {isOpen && (
          <div className="date-dropdown-menu">
            {availableDates.length === 0 ? (
              <div className="no-dates">No dates available</div>
            ) : (
              availableDates.map((dateObj) => (
                <button
                  key={dateObj.date}
                  className={`date-option ${selectedDate === dateObj.date ? 'selected' : ''}`}
                  onClick={() => handleDateSelect(dateObj.date)}
                >
                  <div className="date-option-content">
                    <span className="date-text">{formatDisplayDate(dateObj.date)}</span>
                    <span className="article-count">{dateObj.article_count} articles</span>
                  </div>
                </button>
              ))
            )}
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="dropdown-overlay" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default DigestDatePicker;
