import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Container,
    Typography,
    Box,
    CircularProgress,
    Alert,
    Card,
    CardContent,
    Link,
    Chip,
    Button,
    Stack,
    Divider,
    Collapse,
} from '@mui/material';
import {
    ArrowBack,
    OpenInNew,
    AccessTime,
    Category,
    Source,
    ExpandMore,
    ExpandLess,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { pt } from 'date-fns/locale';
import axios from 'axios';
import { CATEGORY_TRANSLATIONS } from '../utils/categories';
import Header from '../components/Header';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Component for related news section
const RelatedNews = ({ relatedArticles }) => {
    const [expanded, setExpanded] = useState(false);

    const formatDate = (dateString) => {
        try {
            return format(parseISO(dateString), 'HH:mm - dd/MM/yyyy', { locale: pt });
        } catch {
            return dateString;
        }
    };

    if (!relatedArticles || relatedArticles.length === 0) {
        return null;
    }

    return (
        <Card sx={{ mt: 3 }}>
            <CardContent>
                <Button
                    startIcon={expanded ? <ExpandLess /> : <ExpandMore />}
                    onClick={() => setExpanded(!expanded)}
                    size="medium"
                    sx={{ mb: 1, textTransform: 'none' }}
                >
                    <Typography variant="h6" component="span">
                        {relatedArticles.length} notícia{relatedArticles.length > 1 ? 's' : ''} relacionada{relatedArticles.length > 1 ? 's' : ''}
                    </Typography>
                </Button>

                <Collapse in={expanded}>
                    <Box sx={{ mt: 2 }}>
                        {relatedArticles.map((article, index) => (
                            <Card 
                                key={article.id} 
                                variant="outlined" 
                                sx={{ 
                                    mb: 2,
                                    '&:hover': { boxShadow: 2 },
                                    '&:last-child': { mb: 0 }
                                }}
                            >
                                <CardContent sx={{ pb: '16px !important' }}>
                                    <Typography variant="h6" component="h4" sx={{ mb: 1, fontSize: '1.1rem' }}>
                                        <Link
                                            href={article.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            sx={{
                                                textDecoration: 'none',
                                                color: 'inherit',
                                                '&:hover': { color: 'primary.main' }
                                            }}
                                        >
                                            {article.title}
                                        </Link>
                                    </Typography>

                                    {article.summary && (
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            {article.summary}
                                        </Typography>
                                    )}

                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', justifyContent: 'space-between' }}>
                                        <Chip
                                            label={article.source_name}
                                            size="small"
                                            variant="outlined"
                                        />
                                        {article.similarity_score && (
                                            <Chip
                                                label={`Similaridade: ${(article.similarity_score * 100).toFixed(0)}%`}
                                                size="small"
                                                color="info"
                                                variant="outlined"
                                            />
                                        )}
                                        <Typography variant="caption" color="text.secondary">
                                            {formatDate(article.published_at)}
                                        </Typography>
                                    </Box>
                                </CardContent>
                            </Card>
                        ))}
                    </Box>
                </Collapse>
            </CardContent>
        </Card>
    );
};

const ArticlePage = () => {
    const { articleId } = useParams();
    const navigate = useNavigate();
    const [article, setArticle] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchArticle = async () => {
            try {
                setLoading(true);
                setError(null);
                
                const response = await axios.get(`${API_BASE_URL}/articles/${articleId}`);
                
                if (response.data.error) {
                    setError(response.data.error);
                } else {
                    setArticle(response.data);
                }
            } catch (err) {
                console.error('Error fetching article:', err);
                setError('Erro ao carregar o artigo. Tente novamente mais tarde.');
            } finally {
                setLoading(false);
            }
        };

        if (articleId) {
            fetchArticle();
        }
    }, [articleId]);

    const formatDate = (dateString) => {
        try {
            return format(parseISO(dateString), 'HH:mm - dd/MM/yyyy', { locale: pt });
        } catch {
            return dateString;
        }
    };

    const getCategoryTranslation = (category) => {
        return CATEGORY_TRANSLATIONS[category] || category;
    };

    const handleBackToNews = () => {
        navigate('/news');
    };

    const handleSourceClick = (url) => {
        window.open(url, '_blank', 'noopener,noreferrer');
    };

    if (loading) {
        return (
            <>
                <Header />
                <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                        <CircularProgress />
                    </Box>
                </Container>
            </>
        );
    }

    if (error) {
        return (
            <>
                <Header />
                <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                    <Button
                        variant="contained"
                        startIcon={<ArrowBack />}
                        onClick={handleBackToNews}
                    >
                        Voltar para Notícias
                    </Button>
                </Container>
            </>
        );
    }

    if (!article) {
        return (
            <>
                <Header />
                <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                    <Alert severity="warning" sx={{ mb: 2 }}>
                        Artigo não encontrado.
                    </Alert>
                    <Button
                        variant="contained"
                        startIcon={<ArrowBack />}
                        onClick={handleBackToNews}
                    >
                        Voltar para Notícias
                    </Button>
                </Container>
            </>
        );
    }

    return (
        <>
            <Header />
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                {/* Back to News Button */}
                <Box sx={{ mb: 3 }}>
                    <Button
                        variant="outlined"
                        startIcon={<ArrowBack />}
                        onClick={handleBackToNews}
                        sx={{ mb: 2 }}
                    >
                        Voltar para Notícias
                    </Button>
                </Box>

                {/* Article Card */}
                <Card elevation={2}>
                    <CardContent sx={{ p: 4 }}>
                        {/* Article Title */}
                        <Typography 
                            variant="h4" 
                            component="h1" 
                            gutterBottom
                            sx={{ 
                                fontWeight: 600,
                                lineHeight: 1.2,
                                mb: 3 
                            }}
                        >
                            {article.title}
                        </Typography>

                        {/* Article Metadata */}
                        <Stack 
                            direction={{ xs: 'column', sm: 'row' }} 
                            spacing={2} 
                            sx={{ mb: 3 }}
                            divider={<Divider orientation="vertical" flexItem />}
                        >
                            {/* Publication Date */}
                            <Box display="flex" alignItems="center" gap={1}>
                                <AccessTime fontSize="small" color="action" />
                                <Typography variant="body2" color="text.secondary">
                                    {formatDate(article.published_at)}
                                </Typography>
                            </Box>

                            {/* Category */}
                            {article.category && (
                                <Box display="flex" alignItems="center" gap={1}>
                                    <Category fontSize="small" color="action" />
                                    <Chip 
                                        label={getCategoryTranslation(article.category)}
                                        size="small"
                                        color="primary"
                                        variant="outlined"
                                    />
                                </Box>
                            )}

                            {/* Source */}
                            {article.source_name && (
                                <Box display="flex" alignItems="center" gap={1}>
                                    <Source fontSize="small" color="action" />
                                    <Link
                                        component="button"
                                        variant="body2"
                                        onClick={() => handleSourceClick(article.url)}
                                        sx={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 0.5,
                                            textDecoration: 'none',
                                            '&:hover': {
                                                textDecoration: 'underline',
                                            },
                                        }}
                                    >
                                        {article.source_name}
                                        <OpenInNew fontSize="small" />
                                    </Link>
                                </Box>
                            )}
                        </Stack>

                        <Divider sx={{ my: 3 }} />

                        {/* Article Summary */}
                        <Typography 
                            variant="h6" 
                            component="h2" 
                            gutterBottom
                            sx={{ fontWeight: 500, mb: 2 }}
                        >
                            Resumo
                        </Typography>
                        <Typography 
                            variant="body1" 
                            component="div"
                            sx={{ 
                                lineHeight: 1.6,
                                mb: 3,
                                whiteSpace: 'pre-wrap'
                            }}
                        >
                            {article.summary_pt || article.summary || 'Resumo não disponível.'}
                        </Typography>

                        <Divider sx={{ my: 3 }} />

                        {/* Action Buttons */}
                        <Stack direction="row" spacing={2} justifyContent="center">
                            <Button
                                variant="contained"
                                startIcon={<OpenInNew />}
                                onClick={() => handleSourceClick(article.url)}
                                sx={{ minWidth: 200 }}
                            >
                                Ler Artigo Completo
                            </Button>
                            <Button
                                variant="outlined"
                                startIcon={<ArrowBack />}
                                onClick={handleBackToNews}
                            >
                                Voltar para Notícias
                            </Button>
                        </Stack>
                    </CardContent>
                </Card>

                {/* Related News Section */}
                {article.related_articles && (
                    <RelatedNews relatedArticles={article.related_articles} />
                )}
            </Container>
        </>
    );
};

export default ArticlePage;
