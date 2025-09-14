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
import { useToast } from '../ui/SuccessNotification';
import { device } from '../../utils/performance';
import '../../styles/preferences.css';
import Header from '../Header';
import {
  Box,
  Container,
  Typography,
  CircularProgress,
  Backdrop,
  Alert,
  Button,
  Stack,
  Paper
} from '@mui/material';

const PreferencePage = () => {
  const { token } = useParams();
  const navigate = useNavigate();
  const { showSuccess, showError, ToastComponent } = useToast();

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
      <Box minHeight="100vh" bgcolor="background.default" py={4}>
        <Container maxWidth="md">
          <Box textAlign="center" mb={4}>
            <Typography variant="h3" component="h1">
              Preferências
            </Typography>
          </Box>

          <Paper elevation={2} sx={{ p: 6, textAlign: 'center', maxWidth: 500, mx: 'auto' }}>
            <span class="material-icons" style={{ fontSize: 48, color: '#f57c00' }}>
            warning_amber
            </span>

            <Typography variant="h4" component="h2" gutterBottom>
              Erro ao Carregar
            </Typography>

            <Typography variant="body1" color="text.primary" paragraph>
              Não foi possível carregar suas preferências.
            </Typography>

            <Typography variant="body2" color="text.secondary" paragraph>
              Verifique sua conexão com a internet e tente novamente.
            </Typography>

            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={2}
              justifyContent="center"
              sx={{ mt: 4 }}
            >
              <Button
                onClick={handleRetry}
                variant="contained"
                size="large"
              >
                Tentar Novamente
              </Button>

              <Button
                onClick={handleGoHome}
                variant="outlined"
                size="large"
              >
                Início
              </Button>
            </Stack>
          </Paper>
        </Container>
      </Box>
    );
  }

  // Main preference form (token is valid and preferences loaded)
  return (
    <Box>
      <Header />
      <Container maxWidth="lg">
        {/* Header Section */}
        <Box component="header" textAlign="center" py={2}>
          <Typography variant="h4" component="h4" gutterBottom>
            Personalize suas notícias
          </Typography>
          <Typography variant="body1" color="text.secondary" maxWidth="md" mx="auto" paragraph>
            Configure suas categorias, fontes e palavras-chave para receber
            notícias mais relevantes no seu Daily Scribe.
          </Typography>
          {isMobile && (
            <Typography variant="body2" color="info.main">
              Toque nos itens para selecioná-los
            </Typography>
          )}
        </Box>

        {/* Main Content */}
        <Box component="main" id="main-content" position="relative">
          {/* Loading overlay for saving */}
          {saveStatus === 'saving' && (
            <Backdrop open sx={{ zIndex: (theme) => theme.zIndex.modal + 1 }}>
              <Box textAlign="center">
                <CircularProgress color="primary" size={48} />
                <Typography variant="h6" color="white" mt={2}>
                  Salvando preferências...
                </Typography>
              </Box>
            </Backdrop>
          )}

          <PreferenceForm
            preferences={preferences}
            onPreferenceChange={handlePreferenceUpdate}
            onSave={savePreferences}
            onReset={resetPreferences}
            isMobile={isMobile}
            isTouch={isTouch}
          />
        </Box>

        <Box component="footer" py={4} mt={6}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Dica:</strong> Suas alterações são salvas automaticamente.
              {isMobile
                ? ' Você pode minimizar o app a qualquer momento.'
                : ' Você pode fechar esta página a qualquer momento.'
              }
            </Typography>
          </Alert>

          <Alert severity="success" variant="outlined">
            <Typography variant="body2">
              Esta página usa um link seguro que expira em 24 horas ou após 10 usos.
            </Typography>
          </Alert>
        </Box>
      </Container>
      <ToastComponent />
    </Box>
  );
};

export default PreferencePage;
