import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Container,
  Stack,
  Collapse,
  Divider,
  Grid,
  Chip,
  FormControlLabel,
  Checkbox,
  InputAdornment,
  IconButton
} from '@mui/material';
import { useForm, useWatch } from 'react-hook-form';
import axios from 'axios';
import { CATEGORY_PREFERENCES_ORDER, CATEGORY_TRANSLATIONS } from '../utils/categories';

const SubscriptionForm = ({ onSuccess, className = '', variant = 'default' }) => {
  const [submissionState, setSubmissionState] = useState({
    isSubmitting: false,
    isSuccess: false,
    error: null
  });

  // Preference state
  const [showPreferences, setShowPreferences] = useState(false);
  const [availableOptions, setAvailableOptions] = useState({
    categories: [],
    sources: []
  });
  const [loadingOptions, setLoadingOptions] = useState(false);
  const [preferences, setPreferences] = useState({
    enabled_categories: [],
    enabled_sources: [],
    keywords: [],
    max_news_per_category: 10
  });
  const [newKeyword, setNewKeyword] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    control,
    trigger
  } = useForm({
    mode: 'onChange',
    defaultValues: {
      email: ''
    }
  });

  // Watch email field to show preferences when valid
  const watchedEmail = useWatch({
    control,
    name: 'email'
  });

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  // Validate email and show preferences
  useEffect(() => {
    const validateAndShowPreferences = async () => {
      if (watchedEmail && watchedEmail.length > 0) {
        const isValid = await trigger('email');
        if (isValid && !showPreferences) {
          setShowPreferences(true);
          fetchAvailableOptions();
        } else if (!isValid && showPreferences) {
          setShowPreferences(false);
        }
      } else if (showPreferences) {
        setShowPreferences(false);
      }
    };

    const timeoutId = setTimeout(validateAndShowPreferences, 300);
    return () => clearTimeout(timeoutId);
  }, [watchedEmail, trigger, showPreferences]);

  // Fetch available preference options
  const fetchAvailableOptions = async () => {
    if (availableOptions.categories.length > 0) return; // Already loaded

    setLoadingOptions(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/preferences-options`);
      const data = response.data;

      const orderedCategories = (data.categories || []).sort((a, b) => {
        const indexA = CATEGORY_PREFERENCES_ORDER.indexOf(a);
        const indexB = CATEGORY_PREFERENCES_ORDER.indexOf(b);
        return (indexA === -1 ? Number.MAX_VALUE : indexA) - (indexB === -1 ? Number.MAX_VALUE : indexB);
      });

      setAvailableOptions({
        categories: orderedCategories,
        sources: data.sources || []
      });

      // Set default preferences (all categories, popular sources, default keywords)
      setPreferences(prev => ({
        ...prev,
        enabled_categories: orderedCategories,
        enabled_sources: [],
        keywords: ['brasil', 'política', 'tecnologia'] // Default keywords
      }));
    } catch (error) {
      console.error('Error fetching preference options:', error);
      // Set fallback categories
      setAvailableOptions({
        categories: CATEGORY_PREFERENCES_ORDER,
        sources: []
      });
      setPreferences(prev => ({
        ...prev,
        enabled_categories: CATEGORY_PREFERENCES_ORDER,
        keywords: ['brasil', 'política', 'tecnologia'] // Default keywords
      }));
    } finally {
      setLoadingOptions(false);
    }
  };

  // Preference handlers
  const handleCategoryToggle = (category) => {
    setPreferences(prev => ({
      ...prev,
      enabled_categories: prev.enabled_categories.includes(category)
        ? prev.enabled_categories.filter(cat => cat !== category)
        : [...prev.enabled_categories, category]
    }));
  };

  const handleSourceToggle = (sourceId) => {
    setPreferences(prev => ({
      ...prev,
      enabled_sources: prev.enabled_sources.includes(sourceId)
        ? prev.enabled_sources.filter(id => id !== sourceId)
        : [...prev.enabled_sources, sourceId]
    }));
  };

  const handleAddKeyword = () => {
    const trimmedKeyword = newKeyword.trim().toLowerCase();
    if (trimmedKeyword && !preferences.keywords.includes(trimmedKeyword)) {
      setPreferences(prev => ({
        ...prev,
        keywords: [...prev.keywords, trimmedKeyword]
      }));
      setNewKeyword('');
    }
  };

  const handleRemoveKeyword = (keyword) => {
    setPreferences(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }));
  };

  const handleKeywordKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddKeyword();
    }
  };

  const onSubmit = async (data) => {
    setSubmissionState({ isSubmitting: true, isSuccess: false, error: null });

    try {
      // Prepare the subscription data with preferences
      const subscriptionData = {
        email: data.email,
        preferences: showPreferences ? preferences : null
      };

      // Create subscription with preferences
      const subscriptionResponse = await axios.post(`${API_BASE_URL}/subscribe`, subscriptionData, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });

      if (subscriptionResponse.status === 200 || subscriptionResponse.status === 201) {
        setSubmissionState({
          isSubmitting: false,
          isSuccess: true,
          error: null
        });
        
        // Reset form after successful submission
        reset();
        setShowPreferences(false);
        setPreferences({
          enabled_categories: [],
          enabled_sources: [],
          keywords: [],
          max_news_per_category: 10
        });
        
        // Call success callback if provided
        if (onSuccess) {
          onSuccess(data.email, { 
            subscription: subscriptionResponse.data,
            preferences: preferences
          });
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
        maxWidth: showPreferences ? 800 : 600,
        mx: 'auto'
      }}
      className={className}
    >
    <Container maxWidth="md" disableGutters sx={{ px: 2 }}>
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
          <span className="material-symbols-outlined" style={{ fontSize: 48 }}>
          check_circle_unread
          </span>
          
          <Typography variant="h5" component="h4" gutterBottom sx={{ fontWeight: 500 }}>
            Confirme seu email
          </Typography>
          
          <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 400, mx: 'auto' }}>
            Foi enviado um link de verificação para o seu e-mail. Clique no link para confirmar sua inscrição e suas preferências serão aplicadas automaticamente.
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
                {submissionState.isSubmitting ? 'Enviando...' : 'Enviar'}
              </Button>
            </Box>

            {/* Preferences Section */}
            <Collapse in={showPreferences} timeout={300}>
              <Box sx={{ mt: 4 }}>
                <Divider sx={{ mb: 3 }} />
                
                <Typography variant="h5" component="h3" gutterBottom sx={{ textAlign: 'center', mb: 3 }}>
                  Personalize suas notícias
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mb: 4 }}>
                  Configure suas preferências para receber notícias mais relevantes
                </Typography>

                {loadingOptions ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <Grid container spacing={3}>
                    {/* Categories */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Paper elevation={1} sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Categorias de Interesse
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          Selecione as categorias de notícias que mais interessam você
                        </Typography>
                        
                        <Stack direction="row" flexWrap="wrap" gap={1}>
                          {availableOptions.categories.map((category) => (
                            <Chip
                              key={category}
                              label={CATEGORY_TRANSLATIONS[category] || category}
                              variant={preferences.enabled_categories.includes(category) ? "filled" : "outlined"}
                              color={preferences.enabled_categories.includes(category) ? "primary" : "default"}
                              onClick={() => handleCategoryToggle(category)}
                              sx={{ 
                                cursor: 'pointer',
                                '&:hover': {
                                  bgcolor: preferences.enabled_categories.includes(category) 
                                    ? 'primary.dark' 
                                    : 'action.hover'
                                }
                              }}
                            />
                          ))}
                        </Stack>
                      </Paper>
                    </Grid>

                    {/* Keywords */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Paper elevation={1} sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                          Palavras-chave
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          Adicione palavras-chave para filtrar notícias específicas
                        </Typography>
                        
                        <TextField
                          fullWidth
                          size="small"
                          placeholder="Digite uma palavra-chave e pressione Enter"
                          value={newKeyword}
                          onChange={(e) => setNewKeyword(e.target.value)}
                          onKeyPress={handleKeywordKeyPress}
                          InputProps={{
                            endAdornment: (
                              <InputAdornment position="end">
                                <IconButton
                                  edge="end"
                                  onClick={handleAddKeyword}
                                  disabled={!newKeyword.trim()}
                                  size="small"
                                >
                                  <span className="material-icons">add</span>
                                </IconButton>
                              </InputAdornment>
                            ),
                          }}
                          sx={{ mb: 2 }}
                        />
                        
                        <Stack direction="row" flexWrap="wrap" gap={1}>
                          {preferences.keywords.map((keyword) => (
                            <Chip
                              key={keyword}
                              label={keyword}
                              onDelete={() => handleRemoveKeyword(keyword)}
                              size="small"
                              color="secondary"
                            />
                          ))}
                        </Stack>
                      </Paper>
                    </Grid>

                    {/* Sources */}
                    {/* {availableOptions.sources.length > 0 && (
                      <Grid size={12}>
                        <Paper elevation={1} sx={{ p: 3 }}>
                          <Typography variant="h6" gutterBottom>
                            Fontes Preferenciais
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Escolha suas fontes de notícias favoritas
                          </Typography>
                          
                          <Grid container spacing={1}>
                            {availableOptions.sources.slice(0, 10).map((source) => (
                              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={source.id}>
                                <FormControlLabel
                                  control={
                                    <Checkbox
                                      checked={preferences.enabled_sources.includes(source.id)}
                                      onChange={() => handleSourceToggle(source.id)}
                                      size="small"
                                    />
                                  }
                                  label={
                                    <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                                      {source.name}
                                    </Typography>
                                  }
                                />
                              </Grid>
                            ))}
                          </Grid>
                          
                          {availableOptions.sources.length > 10 && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
                              Mostrando as 10 fontes principais. Você poderá personalizar todas as fontes após confirmar sua inscrição.
                            </Typography>
                          )}
                        </Paper>
                      </Grid>
                    )} */}
                  </Grid>
                )}
              </Box>
            </Collapse>

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
