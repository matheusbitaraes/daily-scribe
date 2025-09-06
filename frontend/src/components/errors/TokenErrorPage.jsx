/**
 * Token Error Page Component
 * Generic error page for token-related issues
 */
import React from 'react';
import { getTokenErrorDetails } from '../../utils/tokenValidator';

/**
 * Generic token error page component
 * @param {Object} props - Component props
 * @param {string} props.errorType - Type of error (e.g., 'INVALID_TOKEN')
 * @param {string} props.token - Token that caused the error (optional)
 * @param {Function} props.onRetry - Retry callback (optional)
 * @param {Function} props.onGoHome - Go home callback (optional)
 * @returns {JSX.Element} Token error page
 */
function TokenErrorPage({ 
  errorType = 'INVALID_TOKEN', 
  token = null, 
  onRetry = null, 
  onGoHome = null 
}) {
  const errorDetails = getTokenErrorDetails(errorType);
  const isRetryable = onRetry && (errorType === 'NETWORK_ERROR' || errorType === 'VALIDATION_FAILED');

  return (
    <div className="preference-page">
      <div className="preference-container">
        <div className="preference-header">
          <h1>Preferências</h1>
        </div>

        <div className="error-page">
          <div className="error-icon" role="img" aria-label={errorDetails.title}>
            {errorDetails.icon}
          </div>

          <h2>{errorDetails.title}</h2>
          
          <p className="error-message">
            {errorDetails.message}
          </p>

          <p className="error-description">
            {errorDetails.description}
          </p>

          <div className="error-details">
            <p><strong>O que fazer agora:</strong></p>
            <p>{errorDetails.action}</p>
          </div>

          <div className="error-actions">
            {isRetryable && (
              <button 
                className="btn btn-primary"
                onClick={onRetry}
                aria-label="Tentar novamente"
              >
                <span className="btn-icon">🔄</span>
                Tentar Novamente
              </button>
            )}
          </div>

          {/* Technical details for debugging (only in development) */}
          {process.env.NODE_ENV === 'development' && (
            <details className="error-debug">
              <summary>Detalhes Técnicos (Dev)</summary>
              <pre>{JSON.stringify({
                errorType,
                tokenLength: token?.length || 0,
                tokenStart: token?.substring(0, 10) + '...',
              }, null, 2)}</pre>
            </details>
          )}
        </div>

        <div className="preference-footer">
          <p className="footer-note">
            <strong>Precisa de ajuda?</strong> Responda ao email do seu digest com as dúvidas.
          </p>
        </div>
      </div>
    </div>
  );
}

export default TokenErrorPage;
