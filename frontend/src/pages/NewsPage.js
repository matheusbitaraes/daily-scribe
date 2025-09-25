import { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Tabs,
    Tab,
    Box,
    CircularProgress,
    Alert,
    Card,
    CardContent,
    Link,
    Chip,
    Collapse,
    List,
    ListItem,
    ListItemText,
    Button,
} from '@mui/material';
import {
    ExpandMore,
    ExpandLess,
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import { pt } from 'date-fns/locale';
import axios from 'axios';
import { CATEGORY_TRANSLATIONS } from '../utils/categories';
import Header from '../components/Header';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Component for individual news cluster
const NewsCluster = ({ cluster }) => {
    const [expanded, setExpanded] = useState(false);
    const { main_article, related_articles } = cluster;

    const formatDate = (dateString) => {
        try {

            return format(parseISO(dateString), 'HH:mm - dd/MM/yyyy', { locale: pt });
        } catch {
            return dateString;
        }
    };

    // const getScoreColor = (score) => {
    //     if (score >= 7) return 'error';
    //     if (score >= 5) return 'warning';
    //     if (score >= 3) return 'info';
    //     return 'default';
    // };

    return (
        <Card
            sx={{
                mb: 2,
                border: '1px solid #e0e0e0',
                '&:hover': { boxShadow: 3 }
            }}
        >
            <CardContent>
                {/* Main Article */}
                <Box sx={{ mb: 2 }}>
                    <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600 }}>
                        <Link
                            href={main_article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{
                                textDecoration: 'none',
                                color: 'inherit',
                                '&:hover': { color: 'primary.main' }
                            }}
                        >
                            {main_article.title}
                        </Link>
                    </Typography>

                    {main_article.summary && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {main_article.summary}
                        </Typography>
                    )}

                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center', justifyContent: 'space-between' }}>
                        <Chip
                            label={main_article.source_name}
                            size="small"
                            variant="outlined"
                        />
                        {/* {(main_article.urgency_score > 0 || main_article.impact_score > 0) && (
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                                {main_article.urgency_score > 0 && (
                                    <Chip
                                        label={`Urgência: ${main_article.urgency_score}`}
                                        size="small"
                                        color={getScoreColor(main_article.urgency_score)}
                                    />
                                )}
                                {main_article.impact_score > 0 && (
                                    <Chip
                                        label={`Impacto: ${main_article.impact_score}`}
                                        size="small"
                                        color={getScoreColor(main_article.impact_score)}
                                    />
                                )}
                            </Box>
                        )} */}
                        <Typography variant="caption" color="text.secondary">
                            {formatDate(main_article.published_at)}
                        </Typography>
                    </Box>
                </Box>

                {/* Related Articles */}
                {related_articles && related_articles.length > 0 && (
                    <Box>
                        <Button
                            startIcon={expanded ? <ExpandLess /> : <ExpandMore />}
                            onClick={() => setExpanded(!expanded)}
                            size="small"
                            sx={{ mb: 1 }}
                        >
                            {related_articles.length} notícia{related_articles.length > 1 ? 's' : ''} relacionada{related_articles.length > 1 ? 's' : ''}
                        </Button>

                        <Collapse in={expanded}>
                            <List dense sx={{ bgcolor: 'grey.50', borderRadius: 1, p: 1 }}>
                                {related_articles.map((article, index) => (
                                    <ListItem key={article.id} disablePadding>
                                        <ListItemText
                                            primary={
                                                <Link
                                                    href={article.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    sx={{
                                                        fontSize: '0.875rem',
                                                        textDecoration: 'none',
                                                        '&:hover': { textDecoration: 'underline' }
                                                    }}
                                                >
                                                    [{article.source_name}] {article.title}
                                                </Link>
                                            }
                                            secondary={formatDate(article.published_at)}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Collapse>
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

const NewsPage = () => {
    const [categories, setCategories] = useState([]);
    const [selectedCategoryId, setselectedCategoryId] = useState(0); // 0 = "All"
    const [clusters, setClusters] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    // const [hasMore, setHasMore] = useState(false);
    // const [offset, setOffset] = useState(0);
    // const [loadingMore, setLoadingMore] = useState(false);

    // Fetch categories
    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/categories`);

                if (response.status === 200) {
                    const categories = response.data;
                    setCategories(categories);
                } else {
                    throw new Error('Failed to fetch categories');
                }
            } catch (err) {
                console.error('Error fetching categories:', err);
                setError('Erro ao carregar categorias');
            }
        };

        fetchCategories();
    }, []);

    // Fetch clusters when category, dates change
    useEffect(() => {


    // Fetch clusters
    const fetchClusters = async (categoryValue = null, reset = true) => {
        try {
            if (reset) {
                setLoading(true);
                // setOffset(0);
            } else {
                // setLoadingMore(true);
            }

            const params = new URLSearchParams({
                limit: '20',
                // offset: reset ? '0' : offset.toString(),
            });

            if (categoryValue) {
                params.append('category', categoryValue);
            }

            // read this variable from the page route. if /news?use_search=true, then its passed

            // read the query parameter
            const urlParams = new URLSearchParams(window.location.search);
            const use_search = urlParams.get('use_search') || 'false';

            if (use_search === 'true') {
                params.append('use_search', 'true');
            }

            const response = await fetch(`${API_BASE_URL}/news/clustered?${params}`);
            const data = await response.json();

            if (data.success) {
                if (reset) {
                    setClusters(data.clusters);
                    // setOffset(data.clusters.length);
                } else {
                    setClusters(prev => [...prev, ...data.clusters]);
                    // setOffset(prev => prev + data.clusters.length);
                }
                // setHasMore(data.has_more);
                setError(null);
            } else {
                throw new Error('Failed to fetch clusters');
            }
        } catch (err) {
            console.error('Error fetching clusters:', err);
            setError('Erro ao carregar notícias');
        } finally {
            setLoading(false);
            // setLoadingMore(false);
        }
    };
    
        if (categories?.length > 0) {
            fetchClusters(categories[selectedCategoryId], true);
        }
    }, [categories, selectedCategoryId]);

    const handleCategoryChange = (event, newValue) => {
        setselectedCategoryId(newValue);
    };

    // const handleLoadMore = () => {
    //     const category = categories[selectedCategoryId];
    //     fetchClusters(category?.value, false);
    // };

    if (loading && clusters.length === 0) {
        return (
            <Container maxWidth="lg" sx={{ py: 4 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
                    <CircularProgress />
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="lg" sx={{ py: 4 }}>
            <Header />

            {/* Category Tabs */}
            {categories.length > 0 && (
                <Card sx={{ mb: 3 }}>
                    <Tabs
                        value={selectedCategoryId}
                        onChange={handleCategoryChange}
                        variant="scrollable"
                        scrollButtons="auto"
                        sx={{ px: 2 }}
                    >
                        {categories.map((category, index) => (
                            <Tab
                                key={category}
                                label={
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        <Typography variant="body2">{CATEGORY_TRANSLATIONS[category] || category}</Typography>
                                    </Box>
                                }
                            />
                        ))}
                    </Tabs>
                </Card>
            )}

            {/* Error Display */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {/* News Clusters */}
            {loading && (

                <Container maxWidth="lg" sx={{ py: 4 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
                        <CircularProgress />
                    </Box>
                </Container>
            )}

            {!loading && clusters.length > 0 ? (
                <Box>
                    {clusters.map((cluster, index) => (
                        <NewsCluster key={`${cluster.main_article.id}-${index}`} cluster={cluster} />
                    ))}

                    {/* Load More Button */}
                    {/* {hasMore && (
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                            <Button
                                variant="outlined"
                                onClick={handleLoadMore}
                                disabled={loadingMore}
                                startIcon={loadingMore ? <CircularProgress size={20} /> : <Article />}
                            >
                                {loadingMore ? 'Carregando...' : 'Carregar Mais Notícias'}
                            </Button>
                        </Box>
                    )} */}
                </Box>
            ) : !loading && (
                <Card sx={{ textAlign: 'center', py: 4 }}>
                    <CardContent>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            Nenhuma notícia encontrada
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Tente ajustar os filtros ou selecionar uma categoria diferente.
                        </Typography>
                    </CardContent>
                </Card>
            )}
        </Container>
    );
};

export default NewsPage;