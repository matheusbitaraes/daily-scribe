import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Header from '../components/Header';

import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Link,
  Stack,
  Divider
} from '@mui/material';

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
      <Paper elevation={2} 
        sx={{
          p: 4,
          borderRadius: 2,
          borderColor: 'divider',
          maxWidth: 600,
          mx: 'auto'
        }}>
        <Box display="flex" flexDirection="column" alignItems="center" py={8}>
          
          {/* Loading State */}
          {verificationState.isVerifying && (
            <Box textAlign="center">
              <CircularProgress size={64} color="primary" />
              <Typography variant="h3" component="h1" gutterBottom mt={3}>
                Verificando Seu Email
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Aguarde enquanto confirmamos sua inscrição...
              </Typography>
            </Box>
          )}

          {/* Success State */}
          {verificationState.isSuccess && (
            <Box textAlign="center" maxWidth="lg">     
            
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=check_circle_unread" />         
            <span class="material-symbols-outlined" style={{ fontSize: 48 }}>
            check_circle_unread
            </span>      
            <Typography variant="h4" component="h4"  sx={{
                fontWeight: 400,
              }} gutterBottom>
                Email Verificado com Sucesso!
              </Typography>
              
              <Box mt={2}>
                <Typography variant="body1" paragraph>
                  Obrigado por se inscrever no Daily Scribe! Seu email foi verificado e você receberá nossa newsletter curada.
                </Typography>
                
                {verificationState.email && (
                  <Typography variant="body2" color="text.secondary" mt={5}>
                    <strong>Email Verificado:</strong> {verificationState.email}
                  </Typography>
                )}
              </Box>
            </Box>
          )}

          {/* Error State */}
          {verificationState.error && (
            <Box textAlign="center" maxWidth="lg">
              <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=error" />
              <span class="material-symbols-outlined" style={{ fontSize: 48 }}>
              error
              </span>
              
              <Typography variant="h4" component="h4"  sx={{
                fontWeight: 400,
              }} gutterBottom>
                Falha na Verificação
              </Typography>

              <Typography variant="body1" color="text.secondary" mb={4}>
                Infelizmente, não conseguimos verificar seu email. Os links de verificação expiram após 24 horas, seu email pode já ter sido verificado ou o link pode estar corrompido.
              </Typography>
              
              <Button 
                  onClick={handleSubscribeAgain}
                  variant="contained"
                  size="medium"
                >
                  Inscrever-se Novamente
                </Button>
            </Box>
          )}
        </Box>
      </Paper>
    </>
  );
};

export default EmailVerificationPage;
