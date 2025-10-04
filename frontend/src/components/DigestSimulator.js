import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const DigestSimulator = () => {
  // State management for the simulator
  const [state, setState] = useState({
    // User input
    userEmail: 'matheusbitaraesdenovaes@gmail.com', // Default for testing
    selectedDate: null,
    filters: {
      categories: [], // Will be populated from user preferences
      sources: []     // Will be populated from user preferences
    },
    
    // Data from API
    availableDates: [],
    categories: [],
    sources: [],
    
    // Generated content
    digestContent: null,
    digestMetadata: null,
  rankingDetails: [],
    
    // UI states
    isLoadingDates: false,
    isLoadingDigest: false,
    isLoadingMetadata: false,
    
    // Error handling
    error: null,
    dateError: null,
    digestError: null
  });

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  // Helper function to update state
  const updateState = useCallback((updates) => {
    setState(prevState => ({ ...prevState, ...updates }));
  }, []);

  // Load available dates on component mount
  useEffect(() => {
    loadAvailableDates();
    loadFilterOptions();
    loadUserPreferences();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load user preferences when email changes
  useEffect(() => {
    if (state.userEmail.trim()) {
      loadUserPreferences();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.userEmail]);

  // Load available dates from API
  const loadAvailableDates = async () => {
    updateState({ isLoadingDates: true, dateError: null });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/digest/available-dates`);
      const data = response.data;
      
      if (data.success) {
        updateState({
          availableDates: data.dates,
          isLoadingDates: false,
          // Auto-select the most recent date
          selectedDate: data.dates.length > 0 ? data.dates[0].date : null
        });
      } else {
        throw new Error(data.message || 'Failed to load available dates');
      }
    } catch (error) {
      console.error('Error loading available dates:', error);
      updateState({
        dateError: error.response?.data?.detail || error.message || 'Failed to load available dates',
        isLoadingDates: false,
        availableDates: []
      });
    }
  };

  // Load filter options (categories and sources)
  const loadFilterOptions = async () => {
    try {
      const [categoriesResponse, sourcesResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/categories`),
        axios.get(`${API_BASE_URL}/sources`)
      ]);
      
      updateState({
        categories: categoriesResponse.data || [],
        sources: sourcesResponse.data || []
      });
    } catch (error) {
      console.error('Error loading filter options:', error);
      // Don't show error for filter options as it's not critical
    }
  };

  // Load user preferences to pre-select categories and sources
  const loadUserPreferences = async () => {
    if (!state.userEmail.trim()) return;
    
    try {
      const response = await axios.get(`${API_BASE_URL}/user/preferences`, {
        params: { user_email: state.userEmail.trim() }
      });
      
      const data = response.data;
      
      // Ensure we have arrays and convert to strings if needed
      const enabledCategories = Array.isArray(data.enabled_categories) 
        ? data.enabled_categories.map(cat => String(cat))
        : [];
      
      const enabledSources = Array.isArray(data.enabled_sources)
        ? data.enabled_sources.map(source => String(source))
        : [];
      
      // Update filters with user preferences
      updateState({
        filters: {
          categories: enabledCategories,
          sources: enabledSources
        }
      });
      
    } catch (error) {
      console.error('Error loading user preferences:', error);
      // Fall back to empty arrays if preferences can't be loaded
      updateState({
        filters: {
          categories: [],
          sources: []
        }
      });
    }
  };

  // Generate digest simulation
  const generateDigest = async () => {
    if (!state.userEmail.trim()) {
      updateState({ digestError: 'Please enter a valid email address' });
      return;
    }

    updateState({
      isLoadingDigest: true,
      digestError: null,
      digestContent: null,
      rankingDetails: []
    });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/digest/simulate`, {
        params: { user_email: state.userEmail.trim() }
      });
      
      const data = response.data;
      
      if (data.success) {
        updateState({
          digestContent: data.html_content,
          digestMetadata: data.metadata,
          rankingDetails: data.ranking_details || [],
          isLoadingDigest: false
        });
        
        // Also load metadata for the selected date if available
        if (state.selectedDate) {
          loadDigestMetadata(state.selectedDate);
        }
      } else {
        throw new Error(data.message || 'Failed to generate digest');
      }
    } catch (error) {
      console.error('Error generating digest:', error);
      updateState({
        digestError: error.response?.data?.detail || error.message || 'Failed to generate digest',
        isLoadingDigest: false,
        rankingDetails: []
      });
    }
  };

  // Load metadata for selected date
  const loadDigestMetadata = async (date) => {
    if (!date) return;
    
    updateState({ isLoadingMetadata: true });
    
    try {
      const response = await axios.get(`${API_BASE_URL}/digest/metadata/${date}`);
      const data = response.data;
      
      updateState({
        digestMetadata: data,
        isLoadingMetadata: false
      });
    } catch (error) {
      console.error('Error loading digest metadata:', error);
      updateState({ isLoadingMetadata: false });
      // Don't show error for metadata as it's supplementary information
    }
  };

  // Handle user email change
  const handleEmailChange = (email) => {
    updateState({ userEmail: email, digestError: null });
  };

  // Handle date selection (will be used by date picker component)
  const handleDateChange = (date) => {
    updateState({ selectedDate: date });
    if (date) {
      loadDigestMetadata(date);
    }
  };

  // Handle copy to clipboard callback from DigestPreview
  const handleCopyToClipboard = (status) => {
    if (status === 'success') {
      // Could show a toast notification here
      console.log('Content copied to clipboard successfully');
    } else {
      console.error('Failed to copy content to clipboard');
    }
  };

  // Handle export callback from DigestPreview
  const handleExport = (format) => {
    console.log(`Exporting digest in ${format} format`);
    // Could track analytics or show notifications here
  };

  // Clear all errors
  const clearErrors = () => {
    updateState({ error: null, dateError: null, digestError: null });
  };

  const formatNumber = (value, digits = 3) => {
    if (value === null || value === undefined) {
      return '—';
    }
    const numeric = Number(value);
    if (Number.isNaN(numeric)) {
      return '—';
    }
    return numeric.toFixed(digits);
  };

  const formatDateTime = (value) => {
    if (!value) {
      return '—';
    }
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }
    return parsed.toLocaleString();
  };

  const getFeatureValue = (features, key) => {
    if (!features) {
      return null;
    }
    if (Array.isArray(features)) {
      const indexMap = {
        semantic: 0,
        recency: 1,
        urgency: 2,
        impact: 3
      };
      const index = indexMap[key];
      if (typeof index === 'number') {
        return features[index];
      }
      return null;
    }
    return features[key];
  };

  const hasRankingDetails = Array.isArray(state.rankingDetails) && state.rankingDetails.length > 0;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          Email Digest Simulator
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Simulate and preview email digests for any user and date
        </Typography>
      </Box>

      {/* Error Display */}
      {(state.error || state.dateError || state.digestError) && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={clearErrors}
            >
              <span className='material-icons'>close</span>
            </IconButton>
          }
        >
          {state.error || state.dateError || state.digestError}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Controls Panel */}
        <Grid item size={12} md={4}>
          <Card>
            <CardHeader 
              title="Configuration"
              action={
                <IconButton onClick={loadAvailableDates} disabled={state.isLoadingDates}>
                  <span className='material-icons'>refresh</span>
                </IconButton>
              }
            />
            <CardContent>
              {/* User Email Input */}
              <TextField
                fullWidth
                label="User Email"
                type="email"
                value={state.userEmail}
                onChange={(e) => handleEmailChange(e.target.value)}
                placeholder="Enter user email address"
                margin="normal"
                variant="outlined"
              />

              <Divider sx={{ my: 2 }} />

              {/* Date Selection */}
              <Typography variant="h6" gutterBottom>
                Date Selection
              </Typography>
              {state.isLoadingDates ? (
                <Box display="flex" justifyContent="center" py={2}>
                  <CircularProgress size={24} />
                </Box>
              ) : (
                <FormControl fullWidth margin="normal">
                  <InputLabel>Select Date</InputLabel>
                  <Select
                    value={state.selectedDate || ''}
                    label="Select Date"
                    onChange={(e) => handleDateChange(e.target.value)}
                  >
                    {state.availableDates.map((dateInfo) => (
                      <MenuItem key={dateInfo.date} value={dateInfo.date}>
                        {dateInfo.date} ({dateInfo.article_count} articles)
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              <Divider sx={{ my: 2 }} />

              {/* Generate Button */}
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={generateDigest}
                disabled={state.isLoadingDigest || !state.userEmail.trim()}
                sx={{ mt: 2 }}
              >
                {state.isLoadingDigest ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    Generating...
                  </>
                ) : (
                  'Generate Preview'
                )}
              </Button>

              {/* Metadata Display */}
              {state.digestMetadata && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Digest Metadata
                  </Typography>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Total Articles: {state.digestMetadata.total_articles}
                    </Typography>
                    {state.digestMetadata.categories && Object.keys(state.digestMetadata.categories).length > 0 && (
                      <Box mt={1}>
                        <Typography variant="body2" gutterBottom>
                          Categories:
                        </Typography>
                        <Box display="flex" flexWrap="wrap" gap={0.5}>
                          {Object.entries(state.digestMetadata.categories).map(([category, count]) => (
                            <Chip
                              key={category}
                              label={`${category} (${count})`}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Preview Panel */}
        <Grid item size={12} md={8}>
          <Card>
            <CardHeader 
              title="Digest Preview"
              action={
                state.digestContent && (
                  <Box>
                    <IconButton
                      onClick={() => handleCopyToClipboard('success')}
                      title="Copy to clipboard"
                    >
                      <span className='material-icons'>content_copy</span>
                    </IconButton>
                    <IconButton
                      onClick={() => handleExport('html')}
                      title="Export"
                    >
                      <span className='material-icons'>download</span>
                    </IconButton>
                  </Box>
                )
              }
            />
            <CardContent>
              {state.isLoadingDigest ? (
                <Box display="flex" flexDirection="column" alignItems="center" py={8}>
                  <CircularProgress size={40} />
                  <Typography variant="body1" sx={{ mt: 2 }}>
                    Generating digest preview...
                  </Typography>
                </Box>
              ) : state.digestError ? (
                <Alert severity="error">
                  {state.digestError}
                </Alert>
              ) : state.digestContent ? (
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    maxHeight: '70vh', 
                    overflow: 'auto',
                    backgroundColor: 'grey.50'
                  }}
                >
                  <div dangerouslySetInnerHTML={{ __html: state.digestContent }} />
                </Paper>
              ) : (
                <Box 
                  display="flex" 
                  flexDirection="column" 
                  alignItems="center" 
                  justifyContent="center" 
                  py={8}
                  color="text.secondary"
                >
                  <Typography variant="h6" gutterBottom>
                    No preview available
                  </Typography>
                  <Typography variant="body2">
                    Enter an email address and click "Generate Preview" to see the digest
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Ranking Insights */}
        <Grid item size={12}>
          <Card>
            <CardHeader
              title="Ranking Insights"
              subheader="Detailed breakdown of how each cluster and article contributed to the final ranking"
            />
            <CardContent>
              {state.isLoadingDigest && (
                <Box display="flex" justifyContent="center" py={2}>
                  <CircularProgress size={24} />
                </Box>
              )}

              {hasRankingDetails ? (
                state.rankingDetails.map((cluster, index) => {
                  const components = cluster.score_components || {};
                  const weights = components.weights || {};
                  const chipLabel = `Score ${formatNumber(components.final_score, 4)}`;
                  const articles = cluster.articles || [];

                  return (
                    <Accordion
                      key={cluster.cluster_index ?? index}
                      defaultExpanded={index === 0}
                      disableGutters
                      sx={{ mb: 2, '&:last-of-type': { mb: 0 } }}
                    >
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Stack
                          direction={{ xs: 'column', sm: 'row' }}
                          spacing={1}
                          alignItems={{ xs: 'flex-start', sm: 'center' }}
                          sx={{ width: '100%' }}
                        >
                          <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                            {`Cluster ${index + 1}: ${cluster.main_article_title || 'Untitled article'}`}
                          </Typography>
                          <Stack direction="row" spacing={1}>
                            <Chip label={chipLabel} color="primary" size="small" />
                            <Chip
                              label={`Articles ${cluster.cluster_size}`}
                              variant="outlined"
                              size="small"
                            />
                          </Stack>
                        </Stack>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2}>
                          <Grid item size={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>
                              Score breakdown
                            </Typography>
                            <Table size="small" sx={{ mb: 2 }}>
                              <TableBody>
                                {[
                                  ['Final score', components.final_score, 4],
                                  ['Decayed urgency', components.decayed_urgency, 4],
                                  ['Impact', components.impact_raw, 4],
                                  ['User similarity', components.user_similarity, 4],
                                  ['Similarity bonus', components.user_similarity_bonus, 4],
                                  ['Rank score', components.rank_score, 4],
                                  ['Rank component (scaled)', components.rank_component_scaled, 4],
                                  ['Normalized base', components.normalized_base, 4],
                                  ['Normalized with similarity', components.normalized_with_similarity, 4],
                                  ['Normalized with rank', components.normalized_with_rank, 4],
                                  ['Urgency & impact weighted', components.urgency_impact_weighted, 4],
                                  ['Cluster size', components.cluster_size, 0],
                                  ['Cluster size weighted', components.cluster_size_weighted, 4]
                                ].map(([label, value, digits]) => (
                                  <TableRow key={label}>
                                    <TableCell component="th" scope="row" sx={{ width: '60%' }}>
                                      {label}
                                    </TableCell>
                                    <TableCell>{formatNumber(value, digits)}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </Grid>
                          <Grid item size={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>
                              Weights & parameters
                            </Typography>
                            <Table size="small" sx={{ mb: 2 }}>
                              <TableBody>
                                {Object.entries(weights).map(([label, value]) => (
                                  <TableRow key={label}>
                                    <TableCell component="th" scope="row" sx={{ textTransform: 'capitalize' }}>
                                      {label.replace(/_/g, ' ')}
                                    </TableCell>
                                    <TableCell>
                                      {typeof value === 'number'
                                        ? formatNumber(value, Number.isInteger(value) ? 0 : 4)
                                        : String(value)}
                                    </TableCell>
                                  </TableRow>
                                ))}
                                {Object.keys(weights).length === 0 && (
                                  <TableRow>
                                    <TableCell colSpan={2}>
                                      <Typography variant="body2" color="text.secondary">
                                        No weight configuration captured for this cluster.
                                      </Typography>
                                    </TableCell>
                                  </TableRow>
                                )}
                              </TableBody>
                            </Table>
                          </Grid>
                        </Grid>

                        <Divider sx={{ my: 2 }} />
                        <Typography variant="subtitle2" gutterBottom>
                          Articles in cluster
                        </Typography>
                        <Box sx={{ overflowX: 'auto' }}>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>#</TableCell>
                                <TableCell>Article</TableCell>
                                <TableCell>User similarity</TableCell>
                                <TableCell>Rank score</TableCell>
                                <TableCell>Urgency</TableCell>
                                <TableCell>Impact</TableCell>
                                <TableCell>Semantic</TableCell>
                                <TableCell>Recency</TableCell>
                                <TableCell>LTR urgency</TableCell>
                                <TableCell>LTR impact</TableCell>
                                <TableCell>Published</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {articles.map((article) => (
                                <TableRow
                                  key={`${cluster.cluster_index}-${article.id || article.url || article.position}`}
                                >
                                  <TableCell>{(article.position ?? 0) + 1}</TableCell>
                                  <TableCell sx={{ minWidth: 220 }}>
                                    <Typography
                                      variant="body2"
                                      fontWeight={article.position === 0 ? 600 : 400}
                                      gutterBottom
                                    >
                                      {article.title || 'Untitled article'}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      {article.source || 'Unknown source'}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>{formatNumber(article.user_similarity, 4)}</TableCell>
                                  <TableCell>{formatNumber(article.rank_score, 4)}</TableCell>
                                  <TableCell>{formatNumber(article.urgency_score, 1)}</TableCell>
                                  <TableCell>{formatNumber(article.impact_score, 1)}</TableCell>
                                  <TableCell>{formatNumber(getFeatureValue(article.ltr_features, 'semantic'), 4)}</TableCell>
                                  <TableCell>{formatNumber(getFeatureValue(article.ltr_features, 'recency'), 4)}</TableCell>
                                  <TableCell>{formatNumber(getFeatureValue(article.ltr_features, 'urgency'), 4)}</TableCell>
                                  <TableCell>{formatNumber(getFeatureValue(article.ltr_features, 'impact'), 4)}</TableCell>
                                  <TableCell>{formatDateTime(article.published_at)}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  );
                })
              ) : (
                <Box
                  display="flex"
                  flexDirection="column"
                  alignItems="center"
                  justifyContent="center"
                  py={4}
                  color="text.secondary"
                >
                  <Typography variant="body1" gutterBottom>
                    Generate a digest preview to inspect ranking insights.
                  </Typography>
                  <Typography variant="body2">
                    You will see user similarity, learning-to-rank features, and weighting details here.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DigestSimulator;
