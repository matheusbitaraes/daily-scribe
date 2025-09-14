/**
 * Main preference form component
 * Orchestrates all preference controls and handles form submission
 */
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import CategorySelector from './CategorySelector';
import SourceSelector from './SourceSelector';
import KeywordManager from './KeywordManager';
import {
  Box,
  Paper,
  Grid
} from '@mui/material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const PreferenceForm = ({
  preferences,
  onPreferenceChange,
  onSave,
  onReset,
  isMobile = false,
  isTouch = false
}) => {
  const [availableOptions, setAvailableOptions] = useState({
    categories: [],
    sources: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [, setLoadError] = useState(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors } //, isDirty
  } = useForm({
    defaultValues: preferences ? {
      categories: preferences.enabled_categories || [],
      sources: preferences.enabled_sources || [],
      keywords: preferences.keywords || []
    } : {
      categories: [],
      sources: [],
      keywords: []
    }
  });

  // Watch for form changes
  const watchedValues = watch();

  // Reset form when preferences change
  useEffect(() => {
    if (preferences) {
      // Ensure sources are numbers to match the available sources format
      const sources = (preferences.enabled_sources || []).map(s =>
        typeof s === 'string' ? parseInt(s, 10) : s
      ).filter(s => !isNaN(s));

      const orderedCategories = (preferences.enabled_categories || []).sort((a, b) => a.localeCompare(b));
      const orderedSources = sources
        .filter(source => sources.includes(source.id))
        .sort((a, b) => a.name.localeCompare(b.name));
      setValue('categories', orderedCategories|| []);
      setValue('sources', orderedSources);
      setValue('keywords', preferences.keywords || []);
    }
  }, [preferences, setValue]);

  // Handle form submission (manual save)
  const onSubmit = (data) => {
    // Map frontend form fields to API format
    const apiData = {
      enabled_categories: data.categories || [],
      enabled_sources: data.sources || [],
      keywords: data.keywords || [],
      max_news_per_category: preferences?.max_news_per_category || 10
    };

    onSave(apiData);
  };

  // Handle input changes with preference updates
  const handleChange = (field, value) => {
    setValue(field, value, { shouldDirty: true });

    const updatedData = {
      ...watchedValues,
      [field]: value
    };

    // Map frontend form fields to API format
    const apiData = {
      enabled_categories: updatedData.categories || [],
      enabled_sources: updatedData.sources || [],
      keywords: updatedData.keywords || [],
      max_news_per_category: preferences?.max_news_per_category || 10
    };

    // Update preferences through parent component
    onPreferenceChange(apiData);
  };

  // Fetch available options from API
  useEffect(() => {
    const fetchAvailableOptions = async () => {
      setIsLoading(true);
      setLoadError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/preferences-options`);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        console.log('Fetched available options:', data);

        setAvailableOptions({
          categories: data.categories || [],
          sources: data.sources || []
        });
      } catch (error) {
        console.error('Error fetching available options:', error);
        setLoadError(error.message);

        // Fallback to mock data if API fails
        setAvailableOptions({
          categories: [
            'Technology',
            'Politics',
            'Sports',
            'Entertainment',
            'Science and Health',
            'Business',
            'Other'
          ],
          sources: [
          ]
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchAvailableOptions();
  }, []);


  if (!preferences || isLoading) {
    return <div>Loading form...</div>;
  }

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)}>
      <Grid container spacing={2}>
        {/* Category Selection */}
        <Grid size={6}>
          <Paper elevation={4} sx={{ p: 3, mb: 3 }}>
            <CategorySelector
              selectedCategories={watchedValues.categories || []}
              availableCategories={availableOptions.categories || []}
              onChange={(categories) => handleChange('categories', categories)}
              error={errors.categories}
              register={register}
            />
          </Paper>
        </Grid>

        {/* Keyword Management */}
        <Grid size={6} >
          <Paper elevation={4} sx={{ p: 3 }}>
            <KeywordManager
              keywords={watchedValues.keywords || []}
              onChange={(keywords) => handleChange('keywords', keywords)}
              error={errors.keywords}
              register={register}
            />
          </Paper>
        </Grid>

        {/* Source Selection */}
        <Grid size={12}>
          <Paper elevation={4} sx={{ p: 3 }}>
            <SourceSelector
              selectedSources={watchedValues.sources || []}
              availableSources={availableOptions.sources || []}
              onChange={(sources) => handleChange('sources', sources)}
              error={errors.sources}
              register={register}
            />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PreferenceForm;
