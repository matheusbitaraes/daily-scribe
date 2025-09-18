import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Box, Typography, CircularProgress } from '@mui/material';

const RedirectPage = () => {
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const url = searchParams.get('url');
    
    if (url) {
      try {
        // Decode the URL in case it was encoded
        const decodedUrl = decodeURIComponent(url);
        
        // Validate that it's a proper URL
        const urlObject = new URL(decodedUrl);
        
        // Only allow http and https protocols for security
        if (urlObject.protocol === 'http:' || urlObject.protocol === 'https:') {
          // Small delay to show loading state, then redirect
          setTimeout(() => {
            window.location.href = decodedUrl;
          }, 500);
        } else {
          console.error('Invalid protocol:', urlObject.protocol);
          // Redirect to home page if invalid protocol
          setTimeout(() => {
            window.location.href = '/';
          }, 1000);
        }
      } catch (error) {
        console.error('Invalid URL:', error);
        // Redirect to home page if URL is invalid
        setTimeout(() => {
          window.location.href = '/';
        }, 1000);
      }
    } else {
      // No URL parameter, redirect to home
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    }
  }, [searchParams]);

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      sx={{ p: 3 }}
    >
      <CircularProgress size={40} sx={{ mb: 2 }} />
      <Typography variant="h6" color="text.secondary">
        Redirecting...
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
        You will be redirected shortly.
      </Typography>
    </Box>
  );
};

export default RedirectPage;