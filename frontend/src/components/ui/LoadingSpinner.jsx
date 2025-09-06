/**
 * Enhanced loading spinner component with mobile optimizations
 * Provides visual feedback during API calls and page transitions
 */
import React from 'react';
import '../../styles/responsive.css';

/**
 * LoadingSpinner component
 * @param {Object} props - Component props
 * @param {string} props.size - Size variant ('small', 'medium', 'large')
 * @param {string} props.message - Loading message to display
 * @param {boolean} props.overlay - Whether to show as full-screen overlay
 * @param {string} props.color - Custom color for the spinner
 * @returns {JSX.Element} Loading spinner component
 */
const LoadingSpinner = ({ 
  size = 'medium', 
  message = 'Carregando...', 
  overlay = false,
  color = '#0a97f5'
}) => {
  const sizeClasses = {
    small: 'loading-spinner-small',
    medium: 'loading-spinner-medium', 
    large: 'loading-spinner-large'
  };

  const spinnerClass = sizeClasses[size] || sizeClasses.medium;

  const spinnerStyles = {
    borderTopColor: color
  };

  if (overlay) {
    return (
      <div className="mobile-loading-overlay" role="progressbar" aria-label={message}>
        <div className="mobile-loading-spinner" style={spinnerStyles}></div>
        <div className="mobile-loading-text">{message}</div>
      </div>
    );
  }

  return (
    <div className="loading-container" role="progressbar" aria-label={message}>
      <div className={`loading-spinner ${spinnerClass}`} style={spinnerStyles}></div>
      {message && <div className="loading-message">{message}</div>}
    </div>
  );
};

/**
 * Inline loading spinner for buttons and form elements
 */
export const InlineSpinner = ({ size = 'small', color = '#ffffff' }) => (
  <div 
    className={`loading-spinner loading-spinner-${size} inline-spinner`}
    style={{ borderTopColor: color }}
    role="progressbar"
    aria-label="Carregando"
  />
);

/**
 * Skeleton loader for content placeholders
 */
export const SkeletonLoader = ({ width = '100%', height = '20px', count = 1 }) => (
  <div className="skeleton-container">
    {Array.from({ length: count }, (_, index) => (
      <div 
        key={index}
        className="skeleton-item"
        style={{ width, height }}
        aria-hidden="true"
      />
    ))}
  </div>
);

/**
 * Pulsing loader for interactive elements
 */
export const PulseLoader = ({ children, loading = false }) => (
  <div className={`pulse-loader ${loading ? 'pulse-active' : ''}`}>
    {children}
  </div>
);

export default LoadingSpinner;
