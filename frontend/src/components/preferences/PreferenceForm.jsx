/**
 * Main preference form component
 * Orchestrates all preference controls and handles form submission
 */
import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import CategorySelector from './CategorySelector';
import SourceSelector from './SourceSelector';
import KeywordManager from './KeywordManager';

const PreferenceForm = ({
  preferences,
  onPreferenceChange,
  onSave,
  onReset,
  isMobile = false,
  isTouch = false
}) => {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isDirty }
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
      setValue('categories', preferences.enabled_categories || []);
      setValue('sources', preferences.enabled_sources || []);
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

  // Handle reset
  const handleReset = () => {
    if (window.confirm('Tem certeza que deseja redefinir todas as preferências para os valores padrão?')) {
      onReset();
    }
  };

  if (!preferences) {
    return <div>Loading form...</div>;
  }

  // Mock available options for now (these would come from API in real implementation)
  const availableOptions = {
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
      'G1',
      'UOL',
      'Folha de S.Paulo',
      'O Estado de S. Paulo',
      'BBC Brasil',
      'CNN Brasil',
      'R7',
      'Band'
    ]
  };

  return (
    <form className="preference-form" onSubmit={handleSubmit(onSubmit)}>
      {/* Category Selection */}
      <div className="form-section">
        <CategorySelector
          selectedCategories={watchedValues.categories || []}
          availableCategories={availableOptions.categories || []}
          onChange={(categories) => handleChange('categories', categories)}
          error={errors.categories}
          register={register}
        />
      </div>

      {/* Source Selection */}
      <div className="form-section">
        <SourceSelector
          selectedSources={watchedValues.sources || []}
          availableSources={availableOptions.sources || []}
          onChange={(sources) => handleChange('sources', sources)}
          error={errors.sources}
          register={register}
        />
      </div>

      {/* Keyword Management */}
      <div className="form-section">
        <KeywordManager
          keywords={watchedValues.keywords || []}
          onChange={(keywords) => handleChange('keywords', keywords)}
          error={errors.keywords}
          register={register}
        />
      </div>

      {/* Form Actions */}
      <div className="form-actions">
        <div className="action-group">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={!isDirty}
          >
            Salvar Agora
          </button>
          
          <button
            type="button"
            onClick={handleReset}
            className="btn btn-secondary"
          >
            Redefinir
          </button>
        </div>
        
        <div className="form-status">
          {isDirty && (
            <span className="status-text status-dirty">
              📝 Alterações serão salvas automaticamente
            </span>
          )}
          
          {!isDirty && (
            <span className="status-text status-saved">
              ✅ Preferências salvas
            </span>
          )}
        </div>
      </div>
    </form>
  );
};

export default PreferenceForm;
