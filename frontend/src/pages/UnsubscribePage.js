import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  Stack
} from '@mui/material';
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
    <Box textAlign="center" py={4}>
      <CircularProgress size={60} sx={{ mb: 3 }} />
      <Typography variant="h5" gutterBottom>
        Processing your request...
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Please wait while we unsubscribe you from our newsletter.
      </Typography>
    </Box>
  );

  const renderConfirmationState = () => (
    <Box textAlign="center" py={4}>
      <span class="material-icons" style={{ fontSize: 80, color: '#f57c00', marginBottom: '16px' }}>
        warning_amber
      </span> 
      <Typography variant="h4" gutterBottom>
        Confirmar Cancelamento da Inscrição
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
        Tem certeza de que deseja cancelar a inscrição em nosso boletim diário?
        Você não receberá mais e-mails de resumo em seu endereço de e-mail registrado.
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
        <Button 
          variant="contained"
          color="error"
          size="large"
          onClick={handleUnsubscribe}
          disabled={unsubscribeState.isLoading}
          startIcon={unsubscribeState.isLoading ? <CircularProgress size={20} /> : null}
        >
          {unsubscribeState.isLoading ? 'Processando...' : 'Sim, Cancelar Inscrição'}
        </Button>
        <Button 
          variant="outlined"
          size="large"
          onClick={handleGoHome}
          disabled={unsubscribeState.isLoading}
        >
          Cancelar
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
        Mudou de ideia? Você sempre pode se inscrever novamente mais tarde.
      </Typography>
    </Box>
  );

  const renderSuccessState = () => (
    <Box textAlign="center" py={4}>
      <span class="material-icons" style={{ fontSize: 80, color: '#4caf50', marginBottom: '16px' }}>
        check_circle_outline
      </span>
      <Typography variant="h4" gutterBottom>
        Desincrição Bem-Sucedida
      </Typography>
      {unsubscribeState.email && (
        <Alert severity="success" sx={{ mb: 3, maxWidth: 500, mx: 'auto' }}>
          {unsubscribeState.email} foi removido da nossa lista de e-mails.
        </Alert>
      )}
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
        Pronto! Você não receberá mais e-mails diários de resumo de nossa parte.
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
        <Button 
          variant="contained"
          size="large"
          onClick={handleGoHome}
        >
          Voltar para a Página Inicial
        </Button>
        <Button 
          variant="outlined"
          size="large"
          onClick={handleSubscribeAgain}
        >
          Inscrever-se Novamente
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
        Se você tiver algum feedback sobre nosso boletim informativo, adoraríamos ouvir sua opinião.
      </Typography>
    </Box>
  );

  const renderErrorState = () => (
    <Box textAlign="center" py={4}>
      <span class="material-icons" style={{ fontSize: 80, color: '#f44336', marginBottom: '16px' }}>
        error_outline
      </span>
      <Typography variant="h4" gutterBottom>
        Unsubscription Failed
      </Typography>
      <Alert severity="error" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
        {unsubscribeState.error}
      </Alert>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
        <Button 
          variant="contained"
          size="large"
          onClick={() => setUnsubscribeState(prev => ({
            ...prev,
            isConfirmationShown: true,
            error: null
          }))}
        >
          Try Again
        </Button>
        <Button 
          variant="outlined"
          size="large"
          onClick={handleGoHome}
        >
          Return to Homepage
        </Button>
      </Stack>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
        If this problem persists, please contact our support team.
      </Typography>
    </Box>
  );

  return (
    <>
      <Header />
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          {unsubscribeState.isLoading && renderLoadingState()}
          {unsubscribeState.isConfirmationShown && !unsubscribeState.isLoading && renderConfirmationState()}
          {unsubscribeState.isSuccess && renderSuccessState()}
          {unsubscribeState.error && !unsubscribeState.isConfirmationShown && renderErrorState()}
        </Paper>
      </Container>
    </>
  );
};

export default UnsubscribePage;