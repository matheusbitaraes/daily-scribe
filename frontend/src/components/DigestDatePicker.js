import React, { useState, useEffect } from 'react';
import './DigestDatePicker.css';

const DigestDatePicker = ({ 
  availableDates = [], 
  selectedDate, 
  onDateChange, 
  isLoading = false 
}) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [calendarDates, setCalendarDates] = useState([]);

  // Create a set of available dates for quick lookup
  const availableDateSet = new Set(availableDates.map(d => d.date));
  
  // Get article count for a specific date
  const getArticleCount = (date) => {
    const dateObj = availableDates.find(d => d.date === date);
    return dateObj ? dateObj.article_count : 0;
  };

  // Generate calendar dates for the current month
  useEffect(() => {
    generateCalendarDates();
  }, [currentMonth, availableDates]);

  const generateCalendarDates = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    // First day of the month
    const firstDay = new Date(year, month, 1);
    // Last day of the month
    const lastDay = new Date(year, month + 1, 0);
    
    // Starting date (include previous month's dates to fill the grid)
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    // Generate 42 dates (6 weeks * 7 days)
    const dates = [];
    const currentDate = new Date(startDate);
    
    for (let i = 0; i < 42; i++) {
      dates.push({
        date: new Date(currentDate),
        dateString: formatDateString(currentDate),
        isCurrentMonth: currentDate.getMonth() === month,
        isToday: isToday(currentDate),
        isAvailable: availableDateSet.has(formatDateString(currentDate)),
        articleCount: getArticleCount(formatDateString(currentDate))
      });
      currentDate.setDate(currentDate.getDate() + 1);
    }
    
    setCalendarDates(dates);
  };

  const formatDateString = (date) => {
    return date.toISOString().split('T')[0];
  };

  const isToday = (date) => {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  };

  const navigateMonth = (direction) => {
    const newMonth = new Date(currentMonth);
    newMonth.setMonth(newMonth.getMonth() + direction);
    setCurrentMonth(newMonth);
  };

  const handleDateClick = (dateObj) => {
    if (dateObj.isAvailable && onDateChange) {
      onDateChange(dateObj.dateString);
    }
  };

  const getDayClasses = (dateObj) => {
    let classes = ['calendar-day'];
    
    if (!dateObj.isCurrentMonth) {
      classes.push('other-month');
    }
    
    if (dateObj.isToday) {
      classes.push('today');
    }
    
    if (dateObj.isAvailable) {
      classes.push('available');
    } else {
      classes.push('unavailable');
    }
    
    if (selectedDate === dateObj.dateString) {
      classes.push('selected');
    }
    
    return classes.join(' ');
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  if (isLoading) {
    return (
      <div className="date-picker-container">
        <div className="date-picker-loading">
          <div className="loading-spinner"></div>
          <p>Loading available dates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="date-picker-container">
      <div className="date-picker-header">
        <h3>Select Date</h3>
        <p className="date-picker-subtitle">
          {availableDates.length} dates available with articles
        </p>
      </div>

      <div className="calendar-container">
        {/* Calendar Header */}
        <div className="calendar-header">
          <button 
            className="nav-button" 
            onClick={() => navigateMonth(-1)}
            aria-label="Previous month"
          >
            ❮
          </button>
          <h4 className="month-year">
            {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
          </h4>
          <button 
            className="nav-button" 
            onClick={() => navigateMonth(1)}
            aria-label="Next month"
          >
            ❯
          </button>
        </div>

        {/* Day Names */}
        <div className="calendar-days-header">
          {dayNames.map(day => (
            <div key={day} className="day-name">{day}</div>
          ))}
        </div>

        {/* Calendar Grid */}
        <div className="calendar-grid">
          {calendarDates.map((dateObj, index) => (
            <button
              key={index}
              className={getDayClasses(dateObj)}
              onClick={() => handleDateClick(dateObj)}
              disabled={!dateObj.isAvailable}
              title={
                dateObj.isAvailable 
                  ? `${dateObj.articleCount} articles on ${dateObj.dateString}`
                  : 'No articles available'
              }
              aria-label={
                dateObj.isAvailable 
                  ? `${dateObj.date.getDate()}, ${dateObj.articleCount} articles`
                  : `${dateObj.date.getDate()}, no articles`
              }
            >
              <span className="day-number">{dateObj.date.getDate()}</span>
              {dateObj.isAvailable && dateObj.articleCount > 0 && (
                <span className="article-indicator">
                  {dateObj.articleCount > 999 ? '999+' : dateObj.articleCount}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Selected Date Info */}
      {selectedDate && (
        <div className="selected-date-info">
          <p>
            <strong>Selected:</strong> {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </p>
          {availableDateSet.has(selectedDate) && (
            <p>
              <strong>Articles:</strong> {getArticleCount(selectedDate)}
            </p>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="date-picker-legend">
        <div className="legend-item">
          <div className="legend-color available"></div>
          <span>Available dates</span>
        </div>
        <div className="legend-item">
          <div className="legend-color unavailable"></div>
          <span>No articles</span>
        </div>
        <div className="legend-item">
          <div className="legend-color selected"></div>
          <span>Selected</span>
        </div>
      </div>
    </div>
  );
};

export default DigestDatePicker;
