import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './EmailVerificationPage.css';
import Header from '../components/Header';

const EmailVerificationPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const verificationAttempted = useRef(false);
  const [verificationState, setVerificationState] = useState({
    isVerifying: true,
    isSuccess: false,
    error: null,
    email: null
  });

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
  const token = searchParams.get('token');

  const verifyEmail = useCallback(async (verificationToken) => {
    // Prevent multiple simultaneous calls
    if (verificationAttempted.current) {
      return;
    }
    verificationAttempted.current = true;
    try {
      const response = await axios.get(`${API_BASE_URL}/verify-email`, {
        params: { token: verificationToken },
        timeout: 10000 // 10 second timeout
      });

      if (response.status === 200) {
        const data = response.data;
        setVerificationState({
          isVerifying: false,
          isSuccess: true,
          error: null,
          email: data.email || null
        });
      }
    } catch (error) {
      console.error('Verification error:', error);
      let errorMessage = 'Verification failed. Please try again or contact support.';
      
      if (error.response) {
        const status = error.response.status;
        const responseData = error.response.data;
        
        if (status === 400) {
          errorMessage = responseData?.detail || 'Invalid verification token.';
        } else if (status === 404) {
          errorMessage = 'Verification token not found or has expired.';
        } else if (status === 410) {
          errorMessage = 'This verification link has expired. Please subscribe again.';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (responseData && responseData.detail) {
          errorMessage = responseData.detail;
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

      setVerificationState({
        isVerifying: false,
        isSuccess: false,
        error: errorMessage,
        email: null
      });
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    if (!token) {
      setVerificationState({
        isVerifying: false,
        isSuccess: false,
        error: 'No verification token provided. Please check your email link.',
        email: null
      });
      return;
    }

    verifyEmail(token);
  }, [token, verifyEmail]);

  const handleGoHome = () => {
    navigate('/');
  };

  const handleSubscribeAgain = () => {
    navigate('/#subscribe');
  };

  const handleRetryVerification = () => {
    if (token) {
      // Reset the verification attempt flag
      verificationAttempted.current = false;
      setVerificationState({
        isVerifying: true,
        isSuccess: false,
        error: null,
        email: null
      });
      verifyEmail(token);
    }
  };

  return (
    <>
      <Header />
      <div className="email-verification-page">
        <div className="verification-container">
          <div className="verification-content">
            {/* Loading State */}
            {verificationState.isVerifying && (
              <div className="verification-loading">
                <div className="loading-spinner"></div>
                <h1>Verifying Your Email</h1>
                <p>Please wait while we confirm your subscription...</p>
              </div>
            )}

            {/* Success State */}
            {verificationState.isSuccess && (
              <div className="verification-success">
                <div className="success-icon">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="11" fill="#48BB78"/>
                    <path d="M8 12L11 15L16 10" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <h1>Email Verified Successfully!</h1>
                <div className="success-details">
                  <p className="success-message">
                    Thank you for subscribing to Daily Scribe! Your email has been verified and you're now signed up to receive our curated newsletter.
                  </p>
                  {verificationState.email && (
                    <p className="verified-email">
                      <strong>Verified Email:</strong> {verificationState.email}
                    </p>
                  )}
                  <div className="success-info">
                    <div className="info-item">
                      <h3>What's Next?</h3>
                      <ul>
                        <li>You'll receive our daily digest of curated news articles</li>
                        <li>We'll send you the latest insights from trusted sources</li>
                        <li>You can update your preferences or unsubscribe at any time</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <div className="success-actions">
                  <button 
                    onClick={handleGoHome}
                    className="btn-primary"
                  >
                    Browse Articles
                  </button>
                  <a 
                    href="mailto:support@dailyscribe.com" 
                    className="btn-secondary"
                  >
                    Contact Support
                  </a>
                </div>
              </div>
            )}

            {/* Error State */}
            {verificationState.error && (
              <div className="verification-error">
                <div className="error-icon">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="11" fill="#E53E3E"/>
                    <path d="M15 9L9 15M9 9L15 15" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
                <h1>Verification Failed</h1>
                <div className="error-details">
                  <p className="error-message">
                    {typeof verificationState.error === 'string' 
                      ? verificationState.error 
                      : 'An unexpected error occurred.'}
                  </p>
                  <div className="error-help">
                    <h3>Common Issues:</h3>
                    <ul>
                      <li><strong>Expired Link:</strong> Verification links expire after 24 hours</li>
                      <li><strong>Already Verified:</strong> You may have already confirmed this email</li>
                      <li><strong>Broken Link:</strong> The email link may have been corrupted</li>
                    </ul>
                  </div>
                </div>
                <div className="error-actions">
                  <button 
                    onClick={handleSubscribeAgain}
                    className="btn-primary"
                  >
                    Subscribe Again
                  </button>
                  <button 
                    onClick={handleRetryVerification}
                    className="btn-secondary"
                  >
                    Retry Verification
                  </button>
                  <button 
                    onClick={handleGoHome}
                    className="btn-tertiary"
                  >
                    Go to Home
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <footer className="verification-footer">
            <div className="footer-content">
              <p>
                Having trouble? 
                <a href="mailto:support@dailyscribe.com" className="support-link">
                  Contact our support team
                </a>
              </p>
              <div className="footer-links">
                <a href="/privacy" className="footer-link">Privacy Policy</a>
                <a href="/terms" className="footer-link">Terms of Service</a>
                <button onClick={handleGoHome} className="footer-link">
                  Back to Daily Scribe
                </button>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </>
  );
};

export default EmailVerificationPage;
