import { useState, useCallback } from 'react';
import { validateToken } from '../utils/tokenValidator';

export const useTokenValidation = (initialToken = null) => {
  const [token, setToken] = useState(initialToken);
  const [isValid, setIsValid] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const validateCurrentToken = useCallback(async (tokenToValidate = token) => {
    // EMERGENCY FIX: Explicitly block test_token and invalid tokens to stop infinite loops
    if (!tokenToValidate || tokenToValidate === 'test_token' || tokenToValidate.length < 20) {
      console.log('Blocking invalid token to prevent infinite loop:', tokenToValidate);
      setIsValid(false);
      setIsLoading(false);
      setError('Invalid token format');
      return false;
    }

    // Additional safety check - only allow proper JWT format (3 parts separated by dots)
    const jwtParts = tokenToValidate.split('.');
    if (jwtParts.length !== 3) {
      console.log('Blocking non-JWT token to prevent infinite loop:', tokenToValidate);
      setIsValid(false);
      setIsLoading(false);
      setError('Token must be valid JWT format');
      return false;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await validateToken(tokenToValidate);
      setIsValid(result);
      return result;
    } catch (err) {
      setError(err.message);
      setIsValid(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  return {
    token,
    setToken,
    isValid,
    isLoading,
    error,
    validateToken: validateCurrentToken,
  };
};
