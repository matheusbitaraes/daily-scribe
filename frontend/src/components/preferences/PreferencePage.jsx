/**
 * Main preference configuration page component
 * Handles token validation and renders the preference form
 */
import { useEffect, useMemo, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import PreferenceForm from './PreferenceForm';
import usePreferences from '../../hooks/usePreferences';
import { useTokenValidation } from '../../hooks/useTokenValidation';
import { getTokenInfo } from '../../utils/tokenValidator';
import TokenErrorPage from '../errors/TokenErrorPage';
import ExpiredTokenPage from '../errors/ExpiredTokenPage';
import AccessDeniedPage from '../errors/AccessDeniedPage';
import LoadingSpinner from '../ui/LoadingSpinner';
import ErrorBoundary from '../ui/ErrorBoundary';
import { useToast } from '../ui/SuccessNotification';
import { device } from '../../utils/performance';
import '../../styles/preferences.css';
import Header from '../Header';

const PreferencePage = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { showSuccess, showError,ToastComponent } = useToast();
  
  // Detect if mobile device for enhanced UX
  const isMobile = device.isMobile();
  const isTouch = device.isTouch();
  
  // Token validation hook
  const {
    isValid: tokenValid,
    isLoading: validatingToken,
    error: tokenError,
    validateToken,
  } = useTokenValidation(token);

  // Extract token information for error pages
  const tokenInfo = useMemo(() => {
    if (!token) return null;
    return getTokenInfo(token);
  }, [token]);

  // Validate token on mount
  useEffect(() => {
    if (token) {
      validateToken(token);
    }
  }, [token, validateToken]);

  // Preferences hook (only if token is valid)
  const {
    preferences,
    loading: loadingPreferences,
    error: preferencesError,
    saveStatus,
    fetchPreferences,
    savePreferences,
    updatePreferences,
    resetPreferences,
  } = usePreferences(tokenValid ? token : null);

  // Track previous save status to prevent duplicate toasts
  const prevSaveStatusRef = useRef();

  // Handle save status notifications with toast
  useEffect(() => {
    // Only show toast if saveStatus changed and is not the initial undefined/null
    if (saveStatus && saveStatus !== prevSaveStatusRef.current) {
      if (saveStatus === 'saved') {
        showSuccess('Preferências salvas com sucesso!');
      } else if (saveStatus === 'error') {
        showError('Erro ao salvar preferências. Tente novamente.');
      } else if (saveStatus === 'reset') {
        showSuccess('Preferências redefinidas com sucesso!');
      }
      prevSaveStatusRef.current = saveStatus;
    }
  }, [saveStatus, showSuccess, showError]);

  // Helper functions
  const handleGoHome = () => {
    navigate('/');
  };

  const handleRetry = () => {
    if (tokenError) {
      validateToken(token);
    } else if (preferencesError) {
      fetchPreferences();
    }
  };

  // Handle successful preference updates with toast feedback
  const handlePreferenceUpdate = (updates) => {
    updatePreferences(updates);
  };

  // Render loading with enhanced mobile experience
  if (validatingToken) {
    return (
      <div className="preference-page">
        <div className="preference-container">
          <LoadingSpinner 
            overlay={true}
            message="Validando acesso..."
            size="large"
          />
        </div>
      </div>
    );
  }

  // Handle specific token errors
  if (tokenError) {
    // Expired token - show specialized page
    if (tokenError === 'TOKEN_EXPIRED') {
      return (
        <ExpiredTokenPage
          token={token}
          tokenInfo={tokenInfo}
          onGoHome={handleGoHome}
        />
      );
    }

    // Access denied scenarios
    if (['DEVICE_MISMATCH', 'TOKEN_USED_UP', 'ACCESS_DENIED'].includes(tokenError)) {
      return (
        <AccessDeniedPage
          token={token}
          reason={tokenError}
          onGoHome={handleGoHome}
        />
      );
    }

    // Generic token errors
    return (
      <TokenErrorPage
        errorType={tokenError}
        token={token}
        onRetry={['NETWORK_ERROR', 'VALIDATION_FAILED'].includes(tokenError) ? handleRetry : null}
        onGoHome={handleGoHome}
      />
    );
  }

  // Loading preferences
  if (loadingPreferences) {
    return (
      <div className="preference-page">
        <div className="preference-container">
          <div className="preference-header">
            <h1>Preferências</h1>
          </div>
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <h2>Carregando suas preferências...</h2>
            <p>Aguarde enquanto buscamos suas configurações atuais.</p>
          </div>
        </div>
      </div>
    );
  }

  // Preferences loading error
  if (preferencesError) {
    // Check if it's a token-related error that should be handled specially
    if (['INVALID_TOKEN', 'TOKEN_EXPIRED'].includes(preferencesError)) {
      return (
        <TokenErrorPage
          errorType={preferencesError}
          token={token}
          onRetry={handleRetry}
          onGoHome={handleGoHome}
        />
      );
    }

    // Generic error
    return (
      <div className="preference-page">
        <div className="preference-container">
          <div className="preference-header">
            <h1>Preferências</h1>
          </div>
          <div className="error-page">
            <div className="error-icon">⚠️</div>
            <h2>Erro ao Carregar</h2>
            <p className="error-message">
              Não foi possível carregar suas preferências.
            </p>
            <p className="error-description">
              Verifique sua conexão com a internet e tente novamente.
            </p>
            <div className="error-actions">
              <button 
                onClick={handleRetry} 
                className="btn btn-primary"
              >
                <span className="btn-icon">🔄</span>
                Tentar Novamente
              </button>
              <button 
                onClick={handleGoHome} 
                className="btn btn-secondary"
              >
                <span className="btn-icon">🏠</span>
                Início
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main preference form (token is valid and preferences loaded)
  return (
    <ErrorBoundary>
    <Header />
      <div className={`preference-page ${isMobile ? 'mobile-optimized' : ''}`}>
        <div className="preference-container">
          {/* Skip link for accessibility */}
          <a href="#main-content" className="skip-link">
            Pular para o conteúdo principal
          </a>
          
          <header className="preference-header">
            <h1>📧 Personalize suas notícias</h1>
            <p className="header-description">
              Configure suas categorias, fontes e palavras-chave para receber 
              notícias mais relevantes no seu Daily Scribe.
            </p>
            {isMobile && (
              <p className="mobile-tip">
                💡 Toque nos itens para selecioná-los
              </p>
            )}
          </header>

          <main id="main-content">
            {/* Loading overlay for saving */}
            {saveStatus === 'saving' && (
              <LoadingSpinner 
                overlay={true}
                message="Salvando preferências..."
                size="medium"
              />
            )}

            <PreferenceForm
              preferences={preferences}
              onPreferenceChange={handlePreferenceUpdate}
              onSave={savePreferences}
              onReset={resetPreferences}
              isMobile={isMobile}
              isTouch={isTouch}
            />
          </main>

          <footer className="preference-footer">
            <p className="footer-note">
              💡 <strong>Dica:</strong> Suas alterações são salvas automaticamente. 
              {isMobile ? ' Você pode minimizar o app a qualquer momento.' : ' Você pode fechar esta página a qualquer momento.'}
            </p>
            <p className="footer-security">
              🔒 Esta página usa um link seguro que expira em 24 horas ou após 10 usos.
            </p>
            {/* <div className="footer-links">
              <button 
                onClick={handleGoHome}
                className="footer-link"
                type="button"
              >
                Voltar ao início
              </button>
            </div> */}
          </footer>
        </div>
        
        {/* Toast notifications for mobile */}
        <ToastComponent />
      </div>
    </ErrorBoundary>
  );
};

export default PreferencePage;
