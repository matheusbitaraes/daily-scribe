import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import axios from 'axios';
import './SubscriptionForm.css';

const SubscriptionForm = ({ onSuccess, className = '', variant = 'default' }) => {
  const [submissionState, setSubmissionState] = useState({
    isSubmitting: false,
    isSuccess: false,
    error: null
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset
  } = useForm({
    mode: 'onChange'
  });

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  const onSubmit = async (data) => {
    setSubmissionState({ isSubmitting: true, isSuccess: false, error: null });

    try {
      const response = await axios.post(`${API_BASE_URL}/subscribe`, {
        email: data.email
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000 // 10 second timeout
      });

      if (response.status === 200 || response.status === 201) {
        setSubmissionState({
          isSubmitting: false,
          isSuccess: true,
          error: null
        });
        
        // Reset form after successful submission
        reset();
        
        // Call success callback if provided
        if (onSuccess) {
          onSuccess(data.email, response.data);
        }
      }
    } catch (error) {
      let errorMessage = 'An unexpected error occurred. Please try again.';
      
      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const responseData = error.response.data;
        
        if (status === 400) {
          errorMessage = responseData.detail || 'Invalid email address format.';
        } else if (status === 409) {
          errorMessage = 'This email is already subscribed to our newsletter.';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (responseData && responseData.detail) {
          errorMessage = responseData.detail;
        }
      } else if (error.request) {
        // Network error
        errorMessage = 'Network error. Please check your connection and try again.';
      }

      setSubmissionState({
        isSubmitting: false,
        isSuccess: false,
        error: errorMessage
      });
    }
  };

  const validateEmail = (value) => {
    if (!value) return 'Email address is required';
    
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(value)) {
      return 'Please enter a valid email address';
    }
    
    // Additional validation rules
    if (value.length > 254) {
      return 'Email address is too long';
    }
    
    return true;
  };

  const resetForm = () => {
    setSubmissionState({ isSubmitting: false, isSuccess: false, error: null });
    reset();
  };

  return (
    <div className={`subscription-form ${variant} ${className}`}>
      <div className="subscription-form-content">
        <div className="subscription-form-header">
          <h3 className="subscription-form-title">
            Stay Updated
          </h3>
          <p className="subscription-form-description">
            Get the latest insights delivered straight to your inbox. 
            Subscribe to our newsletter for curated content and updates.
          </p>
        </div>

        {submissionState.isSuccess ? (
          <div className="subscription-success">
            <div className="success-icon">✓</div>
            <h4>Check Your Email!</h4>
            <p>
              We've sent a verification link to your email address. 
              Please click the link to confirm your subscription.
            </p>
            <button 
              type="button" 
              className="btn-secondary"
              onClick={resetForm}
            >
              Subscribe Another Email
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="subscription-form-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <div className="input-group">
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your email address"
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  {...register('email', { 
                    validate: validateEmail,
                    required: 'Email address is required'
                  })}
                  disabled={submissionState.isSubmitting}
                  autoComplete="email"
                  aria-describedby={errors.email ? 'email-error' : undefined}
                />
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={submissionState.isSubmitting}
                  aria-label="Subscribe to newsletter"
                >
                  {submissionState.isSubmitting ? (
                    <>
                      <span className="spinner" aria-hidden="true"></span>
                      Subscribing...
                    </>
                  ) : (
                    'Subscribe'
                  )}
                </button>
              </div>
              
              {errors.email && (
                <div id="email-error" className="error-message" role="alert">
                  {errors.email.message}
                </div>
              )}
            </div>

            {submissionState.error && (
              <div className="error-message global-error" role="alert">
                <strong>Error:</strong> {submissionState.error}
              </div>
            )}
          </form>
        )}

        <div className="subscription-form-footer">
          <p className="privacy-note">
            We respect your privacy. Unsubscribe at any time.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionForm;
