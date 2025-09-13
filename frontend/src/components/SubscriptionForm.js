import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Container,
  Stack
} from '@mui/material';
import { useForm } from 'react-hook-form';
import axios from 'axios';

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
      let errorMessage = 'Erro desconhecido. Por favor, tente novamente mais tarde.';
      
      if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const responseData = error.response.data;
        
        if (status === 400) {
          errorMessage = responseData.detail || 'Formato de endereço de e-mail inválido.';
        } else if (status === 409) {
          errorMessage = 'Este email já está inscrito.';
        } else if (status >= 500) {
          errorMessage = 'Erro no servidor. Por favor, tente novamente mais tarde.';
        } else if (responseData && responseData.detail) {
          errorMessage = responseData.detail;
        }
      } else if (error.request) {
        // Network error
        errorMessage = 'Erro de rede. Por favor, verifique sua conexão e tente novamente.';
      }

      setSubmissionState({
        isSubmitting: false,
        isSuccess: false,
        error: errorMessage
      });
    }
  };

  const validateEmail = (value) => {
    if (!value) return 'Email é obrigatório.';
    
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(value)) {
      return false;
    }
    
    // Additional validation rules
    if (value.length > 254) {
      return 'Email é muito longo.';
    }
    
    return true;
  };

  return (
    // <div className={`subscription-form ${variant} ${className}`}>
    //   <div className="subscription-form-content">
    //     <div className="subscription-form-header">
    //       <h3 className="subscription-form-title">
    //         Assine a Newsletter
    //       </h3>
    //       <p className="subscription-form-description">

    //         {/* Get the latest insights delivered straight to your inbox. 
    //         Subscribe to our newsletter for curated content and updates. */}
    //         Tenha as ultimas noticias dos principais jornais do Brasil e do mundo, resumidas, concatenadas e curadas com base em suas preferências.
    //       </p>
    //     </div>

    //     {submissionState.isSuccess ? (
    //       <div className="subscription-success">
    //         <div className="success-icon">✓</div>
    //         <h4>Confirme seu email</h4>
    //         <p>
    //           Nós enviamos um link de verificação para o seu endereço de e-mail.
    //           Por favor, clique no link para confirmar sua inscrição.
    //         </p>
    //       </div>
    //     ) : (
    //       <form onSubmit={handleSubmit(onSubmit)} className="subscription-form-form">
    //         <div className="form-group">
    //           <div className="input-group">
    //             <input
    //               id="email"
    //               type="email"
    //               placeholder="Digite seu endereço de e-mail"
    //               className={`form-input ${errors.email ? 'error' : ''}`}
    //               {...register('email', { 
    //                 validate: validateEmail,
    //                 required: 'Email address is required'
    //               })}
    //               disabled={submissionState.isSubmitting}
    //               autoComplete="email"
    //               aria-describedby={errors.email ? 'email-error' : undefined}
    //             />
    //             <button
    //               type="submit"
    //               className="btn-primary"
    //               disabled={submissionState.isSubmitting}
    //               aria-label="Subscribe to newsletter"
    //             >
    //               {submissionState.isSubmitting ? (
    //                 <>
    //                   <span className="spinner" aria-hidden="true"></span>
    //                   Subscribing...
    //                 </>
    //               ) : (
    //                 'Subscribe'
    //               )}
    //             </button>
    //           </div>
    //         </div>

    //         {submissionState.error && (
    //           <div className="error-message global-error" role="alert">
    //             <strong>Error:</strong> {submissionState.error}
    //           </div>
    //         )}
    //       </form>
    //     )}

    //     <div className="subscription-form-footer">
    //       <p className="privacy-note">
    //         Respeitamos sua privacidade. Cancele a inscrição a qualquer momento.
    //       </p>
    //     </div>
    //   </div>
    // </div>
    <Paper 
    elevation={2}
    sx={{
      p: 4,
      borderRadius: 2,
      borderColor: 'divider',
      maxWidth: 600,
      mx: 'auto'
    }}
    className={className}
  >
    <Container maxWidth="sm" disableGutters sx={{ px: 2 }}>
      {/* Header Section */}
      <Box sx={{ textAlign: 'center', mb: 5, mt: 1 }}>
        <Typography 
          variant="h4" 
          component="h4" 
          gutterBottom
          sx={{ 
            fontWeight: 500,
            color: 'text.primary'
          }}
        >
          Assine a Newsletter
        </Typography>
        
        <Typography 
          variant="body1" 
          color="text.secondary"
        >
          Receba diariamente as últimas notícias dos principais jornais do Brasil e do mundo, 
          resumidas, concatenadas e curadas com base em suas preferências.
        </Typography>
      </Box>

      {/* Success State */}
      {submissionState.isSuccess ? (
        <Box sx={{ textAlign: 'center', py: 3 }}>
          {/* <CheckCircleIcon 
            sx={{ 
              fontSize: 64, 
              color: 'success.main', 
              mb: 2 
            }} 
          /> */}
          <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&icon_names=check_circle_unread" />         
          <span class="material-symbols-outlined" style={{ fontSize: 48 }}>
          check_circle_unread
          </span>
          
          <Typography variant="h5" component="h4" gutterBottom sx={{ fontWeight: 500 }}>
            Confirme seu email
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
            Foi enviado um link de verificação para o seu e-mail. Clique no link para confirmar sua inscrição.
          </Typography>
        </Box>
      ) : (
        /* Subscription Form */
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
          <Stack spacing={3}>
            {/* Email Input with Button */}
            <Box sx={{ 
              display: 'flex', 
              gap: 2, 
              flexDirection: { xs: 'column', sm: 'row' }
            }}>
              <TextField
                id="email"
                type="email"
                placeholder="Digite seu endereço de e-mail"
                fullWidth
                variant="outlined"
                size="large"
                error={!!errors.email}
                helperText={errors.email?.message}
                disabled={submissionState.isSubmitting}
                autoComplete="email"
                {...register('email', { 
                  validate: validateEmail
                })}
              />
              
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={submissionState.isSubmitting}
                sx={{ 
                  minWidth: { xs: '100%', sm: 140 },
                  height: 56, // Match TextField height
                  fontWeight: 600,
                  textTransform: 'none',
                  fontSize: '1rem'
                }}
                startIcon={
                  submissionState.isSubmitting ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : null
                }
              >
                {submissionState.isSubmitting ? 'Subscribing...' : 'Subscribe'}
              </Button>
            </Box>

            {/* Error Message */}
            {submissionState.error && (
              <Alert 
                severity="error" 
                sx={{ 
                  '& .MuiAlert-message': {
                    fontWeight: 500
                  }
                }}
              >
                <strong>Error:</strong> {submissionState.error}
              </Alert>
            )}
          </Stack>
        </Box>
      )}

      {/* Footer */}
      <Box sx={{ mt: 4, textAlign: 'center', mb: 0 }}>
        <Typography 
          variant="caption" 
          color="text.secondary"
        >
          Respeitamos sua privacidade. Cancele a inscrição a qualquer momento.
        </Typography>
      </Box>
    </Container>
  </Paper>
  );
};

export default SubscriptionForm;
