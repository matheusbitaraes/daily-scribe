import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Header from '../components/Header';

const UnsubscribePage = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [unsubscribeState, setUnsubscribeState] = useState({
    isLoading: false,
    isConfirmationShown: true,
    isSuccess: false,
    error: null,
    email: null
  });

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  // Validate token on component mount
  useEffect(() => {
    if (!token) {
      setUnsubscribeState({
        isLoading: false,
        isConfirmationShown: false,
        isSuccess: false,
        error: 'No unsubscribe token provided. Please check your email link.',
        email: null
      });
    }
  }, [token]);

  const handleUnsubscribe = useCallback(async () => {
    if (!token) {
      return;
    }

    setUnsubscribeState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    try {
      const response = await axios.post(`${API_BASE_URL}/unsubscribe`, {
        token: token
      }, {
        timeout: 10000 // 10 second timeout
      });

      if (response.status === 200) {
        const data = response.data;
        setUnsubscribeState({
          isLoading: false,
          isConfirmationShown: false,
          isSuccess: true,
          error: null,
          email: data.email || null
        });
      }
    } catch (error) {
      console.error('Unsubscribe error:', error);
      let errorMessage = 'Unsubscription failed. Please try again or contact support.';
      
      if (error.response) {
        const status = error.response.status;
        const responseData = error.response.data;
        
        if (status === 400) {
          if (responseData?.code === 'invalid_token') {
            errorMessage = 'This unsubscribe link is invalid or has expired.';
          } else if (responseData?.code === 'invalid_token_type') {
            errorMessage = 'This link is not valid for unsubscription.';
          } else {
            errorMessage = responseData?.error || 'Invalid unsubscribe request.';
          }
        } else if (status === 404) {
          errorMessage = 'Subscription not found. You may already be unsubscribed.';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (responseData && responseData.error) {
          errorMessage = responseData.error;
        }
      } else if (error.request) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (error.message) {
        errorMessage = error.message;
      }

      // Ensure errorMessage is always a string
      if (typeof errorMessage !== 'string') {
        errorMessage = 'An unexpected error occurred.';
      }

      setUnsubscribeState({
        isLoading: false,
        isConfirmationShown: false,
        isSuccess: false,
        error: errorMessage,
        email: null
      });
    }
  }, [token, API_BASE_URL]);

  const handleGoHome = () => {
    navigate('/');
  };

  const handleSubscribeAgain = () => {
    navigate('/#subscribe');
  };

  const renderLoadingState = () => (
    <div className="unsubscribe-loading">
      <div className="loading-spinner"></div>
      <h2>Processing your request...</h2>
      <p>Please wait while we unsubscribe you from our newsletter.</p>
    </div>
  );

  const renderConfirmationState = () => (
    <div className="unsubscribe-confirmation">
      <div className="confirmation-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path 
            d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" 
            stroke="currentColor" 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h1>Confirm Unsubscription</h1>
      <p className="confirmation-message">
        Are you sure you want to unsubscribe from our daily newsletter?
        You will no longer receive digest emails at your registered email address.
      </p>
      <div className="confirmation-actions">
        <button 
          className="btn btn-primary btn-unsubscribe"
          onClick={handleUnsubscribe}
          disabled={unsubscribeState.isLoading}
        >
          {unsubscribeState.isLoading ? 'Processing...' : 'Yes, Unsubscribe Me'}
        </button>
        <button 
          className="btn btn-secondary btn-cancel"
          onClick={handleGoHome}
          disabled={unsubscribeState.isLoading}
        >
          Cancel
        </button>
      </div>
      <p className="help-text">
        Changed your mind? You can always subscribe again later.
      </p>
    </div>
  );

  const renderSuccessState = () => (
    <div className="unsubscribe-success">
      <div className="success-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path 
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
            stroke="currentColor" 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h1>Successfully Unsubscribed</h1>
      {unsubscribeState.email && (
        <p className="success-email">
          {unsubscribeState.email} has been removed from our mailing list.
        </p>
      )}
      <p className="success-message">
        You will no longer receive daily digest emails from us. 
        We're sorry to see you go!
      </p>
      <div className="success-actions">
        <button 
          className="btn btn-primary"
          onClick={handleGoHome}
        >
          Return to Homepage
        </button>
        <button 
          className="btn btn-secondary"
          onClick={handleSubscribeAgain}
        >
          Subscribe Again
        </button>
      </div>
      <p className="help-text">
        If you have any feedback about our newsletter, we'd love to hear from you.
      </p>
    </div>
  );

  const renderErrorState = () => (
    <div className="unsubscribe-error">
      <div className="error-icon">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path 
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" 
            stroke="currentColor" 
            strokeWidth="1.5" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h1>Unsubscription Failed</h1>
      <p className="error-message">{unsubscribeState.error}</p>
      <div className="error-actions">
        <button 
          className="btn btn-primary"
          onClick={() => setUnsubscribeState(prev => ({
            ...prev,
            isConfirmationShown: true,
            error: null
          }))}
        >
          Try Again
        </button>
        <button 
          className="btn btn-secondary"
          onClick={handleGoHome}
        >
          Return to Homepage
        </button>
      </div>
      <p className="help-text">
        If this problem persists, please contact our support team.
      </p>
    </div>
  );

  return (
    <>
      <Header />
      <div className="unsubscribe-page">
        <div className="unsubscribe-container">
          <div className="unsubscribe-content">
            {unsubscribeState.isLoading && renderLoadingState()}
            {unsubscribeState.isConfirmationShown && !unsubscribeState.isLoading && renderConfirmationState()}
            {unsubscribeState.isSuccess && renderSuccessState()}
            {unsubscribeState.error && !unsubscribeState.isConfirmationShown && renderErrorState()}
          </div>
        </div>
      </div>
    </>
  );
};

export default UnsubscribePage;
