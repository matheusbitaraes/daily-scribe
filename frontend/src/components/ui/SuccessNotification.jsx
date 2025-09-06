/**
 * Success notification component with mobile-optimized design
 * Provides user feedback for successful actions and state changes
 */
import React, { useState, useEffect, useCallback } from 'react';
import '../../styles/responsive.css';

/**
 * SuccessNotification component
 * @param {Object} props - Component props
 * @param {string} props.message - Success message to display
 * @param {number} props.duration - Auto-hide duration in milliseconds
 * @param {function} props.onClose - Callback when notification closes
 * @param {string} props.type - Notification type ('success', 'info', 'warning')
 * @param {boolean} props.persistent - Whether notification persists until manually closed
 * @param {string} props.position - Position on screen ('top', 'bottom', 'center')
 * @returns {JSX.Element|null} Success notification component
 */
const SuccessNotification = ({
  message,
  duration = 3000,
  onClose,
  type = 'success',
  persistent = false,
  position = 'bottom'
}) => {
  const [visible, setVisible] = useState(false);
  const [mounted, setMounted] = useState(false);

  const handleClose = useCallback(() => {
    setVisible(false);
    setTimeout(() => {
      setMounted(false);
      if (onClose) {
        onClose();
      }
    }, 300); // Animation duration
  }, [onClose]);

  useEffect(() => {
    if (message) {
      setMounted(true);
      // Small delay to trigger enter animation
      setTimeout(() => setVisible(true), 10);

      if (!persistent && duration > 0) {
        const timer = setTimeout(() => {
          handleClose();
        }, duration);

        return () => clearTimeout(timer);
      }
    }
  }, [message, duration, persistent, handleClose]);

  if (!mounted || !message) {
    return null;
  }

  const typeClasses = {
    success: 'notification-success',
    info: 'notification-info',
    warning: 'notification-warning',
    error: 'notification-error'
  };

  const typeIcons = {
    success: '✓',
    info: 'ℹ',
    warning: '⚠',
    error: '✕'
  };

  const positionClasses = {
    top: 'notification-top',
    bottom: 'notification-bottom',
    center: 'notification-center'
  };

  return (
    <div 
      className={`
        mobile-notification 
        ${typeClasses[type]} 
        ${positionClasses[position]}
        ${visible ? 'notification-visible' : 'notification-hidden'}
      `}
      role="alert"
      aria-live="polite"
    >
      <div className="notification-content">
        <span className="notification-icon" aria-hidden="true">
          {typeIcons[type]}
        </span>
        <span className="notification-message">{message}</span>
        {persistent && (
          <button 
            className="notification-close"
            onClick={handleClose}
            aria-label="Fechar notificação"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Toast notification hook for programmatic usage
 */
export const useToast = () => {
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success', options = {}) => {
    setToast({
      message,
      type,
      ...options,
      id: Date.now() // Unique ID for each toast
    });
  };

  const hideToast = () => {
    setToast(null);
  };

  const showSuccess = (message, options = {}) => {
    showToast(message, 'success', options);
  };

  const showError = (message, options = {}) => {
    showToast(message, 'error', { ...options, persistent: true });
  };

  const showInfo = (message, options = {}) => {
    showToast(message, 'info', options);
  };

  const showWarning = (message, options = {}) => {
    showToast(message, 'warning', options);
  };

  return {
    toast,
    showToast,
    hideToast,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    ToastComponent: () => toast ? (
      <SuccessNotification
        {...toast}
        onClose={hideToast}
      />
    ) : null
  };
};

/**
 * Inline success indicator for form elements
 */
export const InlineSuccess = ({ message, visible = false }) => (
  <div className={`inline-success ${visible ? 'visible' : 'hidden'}`}>
    <span className="success-icon" aria-hidden="true">✓</span>
    <span className="success-text">{message}</span>
  </div>
);

/**
 * Progress indicator with success states
 */
export const ProgressIndicator = ({ 
  steps = [], 
  currentStep = 0, 
  completedSteps = [] 
}) => (
  <div className="progress-indicator" role="progressbar" aria-valuemax={steps.length}>
    <div className="progress-steps">
      {steps.map((step, index) => (
        <div 
          key={index}
          className={`
            progress-step 
            ${index === currentStep ? 'current' : ''}
            ${completedSteps.includes(index) ? 'completed' : ''}
          `}
        >
          <div className="step-indicator">
            {completedSteps.includes(index) ? '✓' : index + 1}
          </div>
          <span className="step-label">{step}</span>
        </div>
      ))}
    </div>
  </div>
);

export default SuccessNotification;
