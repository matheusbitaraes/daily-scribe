import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './DigestFilters.css';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const DigestFilters = ({ 
  onFiltersChange, 
  selectedCategories = [], 
  selectedSources = [],
  isLoading = false 
}) => {
  console.log('DigestFilters props:', { selectedCategories, selectedSources, isLoading });
  
  const [categories, setCategories] = useState([]);
  const [sources, setSources] = useState([]);
  const [isLoadingFilters, setIsLoadingFilters] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    categories: true,
    sources: false
  });

  // Load available categories and sources
  useEffect(() => {
    const loadFilterOptions = async () => {
      setIsLoadingFilters(true);
      setError(null);
      
      try {
        // Load real data from API endpoints
        const [categoriesResponse, sourcesResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/categories`),
          axios.get(`${API_BASE_URL}/sources`)
        ]);
        
        // Transform categories data to expected format
        const categoriesData = Array.isArray(categoriesResponse.data) 
          ? categoriesResponse.data.map(cat => ({
              id: typeof cat === 'string' ? cat : cat.id || cat.name,
              name: typeof cat === 'string' ? cat.charAt(0).toUpperCase() + cat.slice(1) : cat.name || cat.id,
              count: cat.count || 0
            }))
          : [];
        
        // Transform sources data to expected format  
        const sourcesData = Array.isArray(sourcesResponse.data)
          ? sourcesResponse.data.map(source => ({
              id: typeof source === 'string' ? source : source.id || source.name,
              name: typeof source === 'string' ? source : source.name || source.id,
              count: source.count || 0
            }))
          : [];

        setCategories(categoriesData);
        setSources(sourcesData);
        
        console.log('Loaded filter options - Categories:', categoriesData, 'Sources:', sourcesData);
      } catch (err) {
        console.error('Error loading filters from API, falling back to mock data:', err);
        
        // Fallback to mock data if API calls fail
        const mockCategories = [
          { id: 'technology', name: 'Technology', count: 45 },
          { id: 'business', name: 'Business', count: 32 },
          { id: 'science', name: 'Science', count: 28 },
          { id: 'health', name: 'Health', count: 21 },
          { id: 'politics', name: 'Politics', count: 19 },
          { id: 'sports', name: 'Sports', count: 15 },
          { id: 'entertainment', name: 'Entertainment', count: 12 },
          { id: 'world', name: 'World News', count: 38 }
        ];

        const mockSources = [
          { id: 'techcrunch', name: 'TechCrunch', count: 25 },
          { id: 'bbc', name: 'BBC News', count: 42 },
          { id: 'reuters', name: 'Reuters', count: 38 },
          { id: 'cnn', name: 'CNN', count: 35 },
          { id: 'guardian', name: 'The Guardian', count: 28 },
          { id: 'nytimes', name: 'New York Times', count: 31 },
          { id: 'washpost', name: 'Washington Post', count: 22 },
          { id: 'wired', name: 'Wired', count: 18 }
        ];

        setCategories(mockCategories);
        setSources(mockSources);
        setError('Using fallback data - API connection failed');
      } finally {
        setIsLoadingFilters(false);
      }
    };

    loadFilterOptions();
  }, []);

  // Handle category selection
  const handleCategoryChange = (categoryId) => {
    const newSelectedCategories = selectedCategories.includes(categoryId)
      ? selectedCategories.filter(id => id !== categoryId)
      : [...selectedCategories, categoryId];
    
    console.log('Category change:', categoryId, 'New selection:', newSelectedCategories);
    
    onFiltersChange({
      categories: newSelectedCategories,
      sources: selectedSources
    });
  };

  // Handle source selection
  const handleSourceChange = (sourceId) => {
    const newSelectedSources = selectedSources.includes(sourceId)
      ? selectedSources.filter(id => id !== sourceId)
      : [...selectedSources, sourceId];
    
    console.log('Source change:', sourceId, 'New selection:', newSelectedSources);
    
    onFiltersChange({
      categories: selectedCategories,
      sources: newSelectedSources
    });
  };

  // Clear all filters
  const handleClearAll = () => {
    onFiltersChange({
      categories: [],
      sources: []
    });
  };

  // Select all items in a category
  const handleSelectAllCategories = () => {
    const allCategoryIds = categories.map(cat => cat.id);
    onFiltersChange({
      categories: allCategoryIds,
      sources: selectedSources
    });
  };

  const handleSelectAllSources = () => {
    const allSourceIds = sources.map(source => source.id);
    onFiltersChange({
      categories: selectedCategories,
      sources: allSourceIds
    });
  };

  // Toggle section expansion
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  if (isLoadingFilters) {
    return (
      <div className="digest-filters">
        <div className="filters-header">
          <h2>Filters</h2>
        </div>
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading filter options...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="digest-filters">
        <div className="filters-header">
          <h2>Filters</h2>
        </div>
        <div className="error-state">
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalSelected = selectedCategories.length + selectedSources.length;

  return (
    <div className="digest-filters">
      <div className="filters-header">
        <h2>Filters</h2>
        {totalSelected > 0 && (
          <div className="filter-summary">
            <span className="selected-count">{totalSelected} selected</span>
            <button onClick={handleClearAll} className="clear-all-button">
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Categories Section */}
      <div className="filter-section">
        <div 
          className="section-header" 
          onClick={() => toggleSection('categories')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleSection('categories');
            }
          }}
        >
          <h3>Categories</h3>
          <div className="section-controls">
            <span className="selection-count">
              {selectedCategories.length} of {categories.length}
            </span>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleSelectAllCategories();
              }}
              className="select-all-button"
              disabled={isLoading}
            >
              Select All
            </button>
            <span className={`expand-icon ${expandedSections.categories ? 'expanded' : ''}`}>
              ▼
            </span>
          </div>
        </div>
        
        {expandedSections.categories && (
          <div className="filter-options">
            {categories.map(category => (
              <label key={category.id} className="filter-option">
                <input
                  type="checkbox"
                  checked={selectedCategories.includes(category.id)}
                  onChange={() => handleCategoryChange(category.id)}
                  disabled={isLoading}
                />
                <span className="option-name">{category.name}</span>
                <span className="option-count">({category.count})</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Sources Section */}
      <div className="filter-section">
        <div 
          className="section-header" 
          onClick={() => toggleSection('sources')}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleSection('sources');
            }
          }}
        >
          <h3>Sources</h3>
          <div className="section-controls">
            <span className="selection-count">
              {selectedSources.length} of {sources.length}
            </span>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleSelectAllSources();
              }}
              className="select-all-button"
              disabled={isLoading}
            >
              Select All
            </button>
            <span className={`expand-icon ${expandedSections.sources ? 'expanded' : ''}`}>
              ▼
            </span>
          </div>
        </div>
        
        {expandedSections.sources && (
          <div className="filter-options">
            {sources.map(source => (
              <label key={source.id} className="filter-option">
                <input
                  type="checkbox"
                  checked={selectedSources.includes(source.id)}
                  onChange={() => handleSourceChange(source.id)}
                  disabled={isLoading}
                />
                <span className="option-name">{source.name}</span>
                <span className="option-count">({source.count})</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Applied Filters Summary */}
      {totalSelected > 0 && (
        <div className="applied-filters">
          <h4>Applied Filters:</h4>
          <div className="filter-tags">
            {selectedCategories.map(categoryId => {
              const category = categories.find(cat => cat.id === categoryId);
              return (
                <span key={categoryId} className="filter-tag category-tag">
                  {category?.name}
                  <button
                    onClick={() => handleCategoryChange(categoryId)}
                    className="remove-filter"
                    aria-label={`Remove ${category?.name} filter`}
                  >
                    ×
                  </button>
                </span>
              );
            })}
            {selectedSources.map(sourceId => {
              const source = sources.find(src => src.id === sourceId);
              return (
                <span key={sourceId} className="filter-tag source-tag">
                  {source?.name}
                  <button
                    onClick={() => handleSourceChange(sourceId)}
                    className="remove-filter"
                    aria-label={`Remove ${source?.name} filter`}
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default DigestFilters;
