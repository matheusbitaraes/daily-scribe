import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import DOMPurify from 'dompurify';
import {
  Alert,
  Box,
  CircularProgress,
  Container,
  Typography
} from '@mui/material';
import Header from '../components/Header';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const FeedbackPage = () => {
  const { token } = useParams();
  const location = useLocation();
  const [state, setState] = useState({
    loading: true,
    error: null,
    status: null,
    payload: null
  });

  useEffect(() => {
    const query = new URLSearchParams(location.search);
    const articleId = query.get('article_id');
    const signalParam = query.get('signal');
    const digestId = query.get('digest_id');

    if (!token || !articleId || !signalParam) {
      setState({
        loading: false,
        error: 'Link de feedback inválido. Verifique se o endereço está completo.',
        status: null,
        payload: null
      });
      return;
    }

    const parsedSignal = parseInt(signalParam, 10);
    if (Number.isNaN(parsedSignal) || ![1, -1].includes(parsedSignal)) {
      setState({
        loading: false,
        error: 'O sinal enviado não é válido.',
        status: null,
        payload: null
      });
      return;
    }

    const controller = new AbortController();

    const fetchFeedback = async () => {
      setState(prev => ({ ...prev, loading: true, error: null }));
      try {
        const params = new URLSearchParams({
          article_id: articleId,
          signal: parsedSignal.toString()
        });
        if (digestId) {
          params.append('digest_id', digestId);
        }

        const response = await fetch(`${API_BASE_URL}/news/${token}/feedback?${params.toString()}`, {
          method: 'GET',
          signal: controller.signal,
          headers: {
            'Accept': 'application/json'
          }
        });

        const data = await response.json();

        setState({
          loading: false,
          error: response.ok ? null : data?.message || 'Não foi possível carregar o feedback.',
          status: response.status,
          payload: data
        });
      } catch (error) {
        if (error.name === 'AbortError') {
          return;
        }
        setState({
          loading: false,
          error: 'Não foi possível carregar o feedback. Tente novamente mais tarde.',
          status: null,
          payload: null
        });
      }
    };

    fetchFeedback();

    return () => controller.abort();
  }, [location.search, token]);

  useEffect(() => {
    if (state.payload?.title) {
      document.title = state.payload.title;
    }
  }, [state.payload?.title]);

  useEffect(() => {
    if (state.payload) {
      const timeout = window.setTimeout(() => {
        try {
          window.close();
        } catch (err) {
          // ignore errors when window cannot be closed programmatically
        }
      }, 2500);
      return () => window.clearTimeout(timeout);
    }
    return undefined;
  }, [state.payload]);

  const sanitizedHtml = useMemo(() => {
    if (!state.payload?.html) {
      return null;
    }
    return DOMPurify.sanitize(state.payload.html);
  }, [state.payload?.html]);

  const renderContent = () => {
    if (state.loading) {
      return (
        <Box textAlign="center" py={6}>
          <CircularProgress size={64} sx={{ mb: 3 }} />
          <Typography variant="h6" color="text.secondary">
            Registrando o seu feedback…
          </Typography>
        </Box>
      );
    }

    if (!state.payload && state.error) {
      return (
        <Alert severity="error" sx={{ mt: 4 }}>
          {state.error}
        </Alert>
      );
    }

    return (
      <>
        {state.error && (
          <Alert severity="warning" sx={{ mb: 3 }}>
            {state.error}
          </Alert>
        )}
        {sanitizedHtml ? (
          <Container elevation={4} sx={{ p: { xs: 2, sm: 4 } }}>
            <div dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />
          </Container>
        ) : (
          <Container sx={{ p: { xs: 2, sm: 4 } }}>
            <Typography variant="h5" gutterBottom>
              Obrigado pelo feedback!
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Em breve esta janela pode ser fechada automaticamente. Caso contrário, você pode fechá-la manualmente.
            </Typography>
          </Container>
        )}
      </>
    );
  };

  return (
    <>
    <Header />
    <Container maxWidth="sm" sx={{ py: { xs: 4, sm: 8 } }}>
      {renderContent()}
    </Container>
    </>
  );
};

export default FeedbackPage;
