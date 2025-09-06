/**
 * Token Validation Utilities
 * Client-side token validation and parsing helpers
 */

/**
 * Base URL for API calls
 */
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Validate token format (basic client-side validation)
 * @param {string} token - Token to validate
 * @returns {Object} Validation result
 */
export function validateTokenFormat(token) {
  // EMERGENCY FIX: Explicitly block test_token to prevent infinite loops
  if (token === 'test_token') {
    console.log('Blocking test_token to prevent infinite loop');
    return {
      isValid: false,
      error: 'INVALID_TEST_TOKEN',
      message: 'test_token is not a valid token format',
    };
  }

  if (!token || typeof token !== 'string') {
    return {
      isValid: false,
      error: 'TOKEN_MISSING',
      message: 'Token não fornecido',
    };
  }

  // Minimum length check to prevent obvious invalid tokens
  if (token.length < 20) {
    return {
      isValid: false,
      error: 'TOKEN_TOO_SHORT',
      message: 'Token too short to be valid',
    };
  }

  // JWT format validation (allows dots for JWT structure)
  // JWT tokens have format: header.payload.signature
  const jwtPattern = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;
  const simpleTokenPattern = /^[A-Za-z0-9_-]+$/;
  
  // Accept either JWT format or simple base64url format
  if (!jwtPattern.test(token) && !simpleTokenPattern.test(token)) {
    return {
      isValid: false,
      error: 'TOKEN_INVALID_FORMAT',
      message: 'Formato de token inválido',
    };
  }

  // Check length (reasonable bounds for JWT-style tokens)
  if (token.length < 10 || token.length > 1000) {
    return {
      isValid: false,
      error: 'TOKEN_INVALID_LENGTH',
      message: 'Token com tamanho inválido',
    };
  }

  return {
    isValid: true,
    error: null,
    message: null,
  };
}

/**
 * Validate token with the backend API
 * @param {string} token - Token to validate
 * @returns {Promise<Object>} API validation result
 */
export async function validateTokenWithAPI(token) {
  // EMERGENCY FIX: Explicitly block test_token to prevent infinite API calls
  if (token === 'test_token' || !token || token.length < 20) {
    console.log('Blocking invalid token from API call to prevent infinite loop:', token);
    return {
      isValid: false,
      error: 'INVALID_TOKEN_FORMAT',
      message: 'Invalid token format blocked from API call'
    };
  }

  // Additional JWT format check
  const jwtParts = token.split('.');
  if (jwtParts.length !== 3) {
    console.log('Blocking non-JWT token from API call:', token);
    return {
      isValid: false,
      error: 'INVALID_JWT_FORMAT',
      message: 'Token must be valid JWT format'
    };
  }

  try {
    // Use the correct endpoint - just try to fetch preferences to validate token
    const response = await fetch(`${API_BASE_URL}/preferences/${token}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Parse error response
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = {};
      }

      // Map HTTP status codes to appropriate error types
      let errorType = 'VALIDATION_FAILED';
      if (response.status === 404) {
        errorType = 'TOKEN_NOT_FOUND';
      } else if (response.status === 401) {
        errorType = 'INVALID_TOKEN';
      } else if (response.status === 403) {
        errorType = 'TOKEN_EXPIRED';
      }

      return {
        isValid: false,
        error: errorData.error_type || errorType,
        message: errorData.message || 'Falha na validação do token',
        details: errorData.details || null,
        statusCode: response.status,
      };
    }

    const data = await response.json();
    return {
      isValid: true,
      error: null,
      message: 'Token válido',
      data: data,
      statusCode: response.status,
    };
  } catch (err) {
    // Network or other errors
    return {
      isValid: false,
      error: 'NETWORK_ERROR',
      message: 'Erro de conexão. Verifique sua internet e tente novamente.',
      details: err.message,
      statusCode: null,
    };
  }
}

/**
 * Get user-friendly error message for token errors
 * @param {string} errorType - Error type from validation
 * @returns {Object} Error details with user-friendly messages
 */
export function getTokenErrorDetails(errorType) {
  const errorMap = {
    TOKEN_MISSING: {
      title: 'Token Não Encontrado',
      message: 'Não foi possível localizar o token de acesso.',
      description: 'O link que você utilizou pode estar incompleto ou corrompido.',
      action: 'Verifique o link no email ou solicite um novo.',
      icon: '🔍',
      severity: 'warning',
    },
    TOKEN_INVALID_FORMAT: {
      title: 'Token Inválido',
      message: 'O token de acesso possui formato inválido.',
      description: 'O link que você utilizou pode ter sido modificado ou corrompido.',
      action: 'Utilize o link original do email ou solicite um novo.',
      icon: '❌',
      severity: 'error',
    },
    TOKEN_INVALID_LENGTH: {
      title: 'Token Corrompido',
      message: 'O token de acesso parece estar corrompido.',
      description: 'O link pode ter sido truncado ou modificado.',
      action: 'Copie e cole o link completo do email.',
      icon: '⚠️',
      severity: 'error',
    },
    INVALID_TOKEN: {
      title: 'Token Inválido',
      message: 'Este token de acesso não é reconhecido pelo sistema.',
      description: 'O token pode ter sido modificado ou não existe.',
      action: 'Verifique o link no email ou solicite um novo digest.',
      icon: '🚫',
      severity: 'error',
    },
    TOKEN_NOT_FOUND: {
      title: 'Token Não Encontrado',
      message: 'Este token de acesso não foi encontrado.',
      description: 'O token pode não existir ou ter sido removido do sistema.',
      action: 'Verifique o link no email ou solicite um novo digest.',
      icon: '🔍',
      severity: 'error',
    },
    TOKEN_EXPIRED: {
      title: 'Token Expirado',
      message: 'Este token de acesso expirou.',
      description: 'Por segurança, os tokens têm validade de 24 horas.',
      action: 'Solicite um novo digest para obter um link atualizado.',
      icon: '⏰',
      severity: 'warning',
    },
    TOKEN_USED_UP: {
      title: 'Token Esgotado',
      message: 'Este token já foi utilizado o máximo de vezes permitido.',
      description: 'Por segurança, cada token pode ser usado apenas 10 vezes.',
      action: 'Solicite um novo digest para obter um novo token.',
      icon: '🔄',
      severity: 'warning',
    },
    DEVICE_MISMATCH: {
      title: 'Dispositivo Diferente',
      message: 'Este token foi criado para outro dispositivo.',
      description: 'Por segurança, tokens são vinculados ao dispositivo de origem.',
      action: 'Acesse pelo dispositivo onde solicitou o digest ou solicite um novo.',
      icon: '📱',
      severity: 'warning',
    },
    NETWORK_ERROR: {
      title: 'Erro de Conexão',
      message: 'Não foi possível conectar ao servidor.',
      description: 'Verifique sua conexão com a internet.',
      action: 'Tente novamente em alguns instantes.',
      icon: '🌐',
      severity: 'error',
    },
    VALIDATION_FAILED: {
      title: 'Falha na Validação',
      message: 'Não foi possível validar o token de acesso.',
      description: 'Ocorreu um erro interno durante a validação.',
      action: 'Tente novamente ou solicite um novo digest.',
      icon: '⚡',
      severity: 'error',
    },
    ACCESS_DENIED: {
      title: 'Acesso Negado',
      message: 'Você não tem permissão para acessar esta página.',
      description: 'O token pode não ter as permissões necessárias.',
      action: 'Verifique se está usando o link correto do email.',
      icon: '🔒',
      severity: 'error',
    },
  };

  return errorMap[errorType] || {
    title: 'Erro Desconhecido',
    message: 'Ocorreu um erro inesperado.',
    description: 'Não foi possível identificar o tipo de erro.',
    action: 'Tente novamente ou entre em contato com o suporte.',
    icon: '❓',
    severity: 'error',
  };
}

/**
 * Check if error is retryable
 * @param {string} errorType - Error type
 * @returns {boolean} Whether the error can be retried
 */
export function isRetryableError(errorType) {
  // Disable all retries to prevent infinite loops
  return false;
}

/**
 * Get device fingerprint for token validation
 * @returns {string} Basic device fingerprint
 */
export function getDeviceFingerprint() {
  // Simple client-side fingerprint (not for security, just for UX)
  const navigator_info = navigator.userAgent + navigator.language;
  const screen_info = window.screen ? (window.screen.width + 'x' + window.screen.height) : '0x0';
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  
  return btoa(navigator_info + screen_info + timezone).replace(/[+/=]/g, '');
}

/**
 * Extract token information (if possible)
 * @param {string} token - Token to analyze
 * @returns {Object} Token information
 */
export function getTokenInfo(token) {
  try {
    // Try to decode if it's a JWT-like token
    const parts = token.split('.');
    if (parts.length === 3) {
      // Might be a JWT
      const payload = JSON.parse(atob(parts[1]));
      return {
        isJWT: true,
        payload: payload,
        expiresAt: payload.exp ? new Date(payload.exp * 1000) : null,
        issuedAt: payload.iat ? new Date(payload.iat * 1000) : null,
      };
    }
  } catch (e) {
    // Not a JWT or can't decode
  }
  
  return {
    isJWT: false,
    payload: null,
    expiresAt: null,
    issuedAt: null,
    length: token.length,
  };
}

/**
 * Log token validation error for debugging
 * @param {string} token - Token that failed
 * @param {Object} error - Error details
 */
export function logTokenError(token, error) {
  console.warn('Token validation failed:', {
    tokenLength: token?.length || 0,
    tokenStart: token?.substring(0, 8) + '...',
    errorType: error.error,
    message: error.message,
    statusCode: error.statusCode,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Main token validation function that combines format and API validation
 * @param {string} token - Token to validate
 * @returns {Promise<boolean>} True if token is valid, false otherwise
 */
export async function validateToken(token) {
  // EMERGENCY FIX: Explicitly block test_token to prevent infinite loops
  if (token === 'test_token') {
    console.log('Blocking test_token validation to prevent infinite loop');
    return false;
  }

  // First validate format
  const formatResult = validateTokenFormat(token);
  if (!formatResult.isValid) {
    logTokenError(token, formatResult);
    return false;
  }

  // Then validate with API
  const apiResult = await validateTokenWithAPI(token);
  if (!apiResult.isValid) {
    logTokenError(token, apiResult);
    return false;
  }

  return true;
}
