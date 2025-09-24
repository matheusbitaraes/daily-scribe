import { useState } from 'react';
import {
    Container,
    Typography,
    Box,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Card,
    CardContent,
    CircularProgress,
    Alert,
    Link,
    Chip,
    Grid,
    Paper,
} from '@mui/material';
import {
    Search,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { format, parseISO } from 'date-fns';
import { pt } from 'date-fns/locale';
import axios from 'axios';
import { CATEGORY_TRANSLATIONS } from '../utils/categories';
import Header from '../components/Header';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Component for individual search result
const SearchResult = ({ article, index }) => {
    const formatDate = (dateString) => {
        try {
            return format(parseISO(dateString), 'HH:mm - dd/MM/yyyy', { locale: pt });
        } catch {
            return dateString;
        }
    };

    return (
        <Card sx={{ mb: 2, '&:hover': { boxShadow: 3 } }}>
            <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                        #{index + 1}
                    </Typography>
                    {article._score && (
                        <Chip
                            label={`Score: ${article._score.toFixed(2)}`}
                            size="small"
                            color="primary"
                        />
                    )}
                </Box>
                
                <Typography variant="h6" component="h3" sx={{ mb: 1, fontWeight: 600 }}>
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

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                            label={article.source_name || 'Unknown'}
                            size="small"
                            variant="outlined"
                        />
                        {article.category && (
                            <Chip
                                label={CATEGORY_TRANSLATIONS[article.category] || article.category}
                                size="small"
                                color="secondary"
                                variant="outlined"
                            />
                        )}
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                        {formatDate(article.published_at)}
                    </Typography>
                </Box>
            </CardContent>
        </Card>
    );
};

const SearchPage = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [category, setCategory] = useState('');
    const [dateFrom, setDateFrom] = useState(null);
    const [dateTo, setDateTo] = useState(null);
    
    const [results, setResults] = useState([]);
    const [facets, setFacets] = useState({});
    const [totalResults, setTotalResults] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const categories = Object.keys(CATEGORY_TRANSLATIONS);

    const performSearch = async () => {
        // Allow search with just filters (no query text required)
        if (!searchQuery.trim() && !category && !dateFrom && !dateTo) return;
        
        setLoading(true);
        setError(null);
        
        try {
            const params = {
                limit: 50,
                page: 1,
            };
            
            if (searchQuery.trim()) {
                params.query = searchQuery;
            }
            
            if (category) {
                params.category = category;
            }
            if (dateFrom) {
                params.date_from = format(dateFrom, 'yyyy-MM-dd');
            }
            if (dateTo) {
                params.date_to = format(dateTo, 'yyyy-MM-dd');
            }
            
            const response = await axios.get(`${API_BASE_URL}/search`, { params });
            
            setResults(response.data.results || []);
            setFacets(response.data.facets || {});
            setTotalResults(response.data.total || 0);
            
        } catch (err) {
            console.error('Search error:', err);
            setError(err.response?.data?.detail || 'Erro ao realizar busca. Verifique se o Elasticsearch está funcionando.');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    };

    return (
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={pt}>
            <Container maxWidth="lg" sx={{ py: 4 }}>
                <Header />
                
                <Typography variant="h4" component="h1" gutterBottom>
                    Busca
                </Typography>
                
                {/* Search Form */}
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                label="Buscar notícias..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={handleKeyPress}
                            />
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>Categoria</InputLabel>
                                <Select
                                    value={category}
                                    label="Categoria"
                                    onChange={(e) => setCategory(e.target.value)}
                                >
                                    <MenuItem value="">Todas</MenuItem>
                                    {categories.map((cat) => (
                                        <MenuItem key={cat} value={cat}>
                                            {CATEGORY_TRANSLATIONS[cat]}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={2}>
                            <DatePicker
                                label="Data inicial"
                                value={dateFrom}
                                onChange={(date) => setDateFrom(date)}
                                renderInput={(params) => <TextField {...params} fullWidth />}
                            />
                        </Grid>
                        
                        <Grid item xs={12} sm={6} md={2}>
                            <DatePicker
                                label="Data final"
                                value={dateTo}
                                onChange={(date) => setDateTo(date)}
                                renderInput={(params) => <TextField {...params} fullWidth />}
                            />
                        </Grid>
                    </Grid>
                    
                    <Box sx={{ mt: 2 }}>
                        <Button
                            variant="contained"
                            startIcon={<Search />}
                            onClick={performSearch}
                            disabled={loading || (!searchQuery.trim() && !category && !dateFrom && !dateTo)}
                        >
                            {loading ? 'Buscando...' : 'Buscar'}
                        </Button>
                    </Box>
                </Paper>
                
                {/* Error Display */}
                {error && (
                    <Alert severity="error" sx={{ mb: 3 }}>
                        {error}
                    </Alert>
                )}
                
                {/* Loading */}
                {loading && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                        <CircularProgress />
                    </Box>
                )}
                
                <Grid container spacing={3}>
                    {/* Results */}
                    <Grid item xs={12} md={8}>
                        {!loading && results.length > 0 && (
                            <Box>
                                <Typography variant="h6" gutterBottom>
                                    Resultados ({totalResults})
                                </Typography>
                                {results.map((article, index) => (
                                    <SearchResult key={article.id || index} article={article} index={index} />
                                ))}
                            </Box>
                        )}
                        
                        {!loading && results.length === 0 && (searchQuery || category || dateFrom || dateTo) && (
                            <Card sx={{ textAlign: 'center', py: 4 }}>
                                <CardContent>
                                    <Typography variant="h6" color="text.secondary" gutterBottom>
                                        Nenhum resultado encontrado
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Tente ajustar os termos de busca ou filtros.
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                    </Grid>
                    
                    {/* Facets Sidebar */}
                    <Grid item xs={12} md={4}>
                        {Object.keys(facets).length > 0 && (
                            <Paper sx={{ p: 2 }}>
                                <Typography variant="h6" gutterBottom>
                                    Filtros
                                </Typography>
                                
                                {Object.entries(facets).map(([key, facet]) => (
                                    <Box key={key} sx={{ mb: 3 }}>
                                        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                                            {key === 'categories' ? 'Categorias' : 
                                             key === 'sources' ? 'Fontes' : 
                                             key === 'source_names' ? 'Fontes' : key}
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                            {facet.buckets?.slice(0, 8).map((bucket) => (
                                                <Box key={bucket.key} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                                    <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                                                        {key === 'categories' 
                                                            ? (CATEGORY_TRANSLATIONS[bucket.key] || bucket.key)
                                                            : bucket.key}
                                                    </Typography>
                                                    <Chip 
                                                        label={bucket.doc_count}
                                                        size="small"
                                                        variant="outlined"
                                                        sx={{ height: 20, fontSize: '0.75rem' }}
                                                    />
                                                </Box>
                                            ))}
                                        </Box>
                                    </Box>
                                ))}
                            </Paper>
                        )}
                    </Grid>
                </Grid>
            </Container>
        </LocalizationProvider>
    );
};

export default SearchPage;