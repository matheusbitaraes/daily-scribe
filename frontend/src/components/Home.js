import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './Home.css';

const Home = () => {
  const [state, setState] = useState({
    // Articles data
    articles: [],
    totalArticles: 0,
    
    // Filter options
    availableCategories: [],
    availableSources: [],
    availableDates: [],
    
    // Current filters
    filters: {
      categories: [],
      sources: [],
      dateFrom: null,
      dateTo: null,
      search: ''
    },
    
    // Pagination
    currentPage: 1,
    articlesPerPage: 20,
    
    // UI states
    isLoading: false,
    isLoadingFilters: false,
    error: null,
    
    // Filter UI state
    showFilters: true,
    expandedSections: {
      categories: true,
      sources: false,
      dates: false
    }
  });

  const API_BASE_URL = 'http://localhost:8000';

  // Load filter options on component mount
  useEffect(() => {
    loadFilterOptions();
  }, []);

  // Load articles when filters or pagination changes
  useEffect(() => {
    loadArticles();
  }, [state.filters, state.currentPage, state.articlesPerPage]);

  const loadFilterOptions = async () => {
    setState(prev => ({ ...prev, isLoadingFilters: true }));
    
    try {
      const [categoriesResponse, sourcesResponse, datesResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/categories`),
        axios.get(`${API_BASE_URL}/sources`),
        axios.get(`${API_BASE_URL}/digest/available-dates`)
      ]);

      // Process categories
      const categories = Array.isArray(categoriesResponse.data) 
        ? categoriesResponse.data.map(cat => ({
            id: typeof cat === 'string' ? cat : cat.name || cat.id,
            name: typeof cat === 'string' ? cat.charAt(0).toUpperCase() + cat.slice(1) : cat.display_name || cat.name || cat.id,
            count: cat.article_count || 0
          }))
        : [];

      // Process sources  
      const sources = Array.isArray(sourcesResponse.data)
        ? sourcesResponse.data.map(source => ({
            id: source.id || source.name,
            name: source.name,
            count: source.article_count || 0
          }))
        : [];

      // Process dates
      const dates = datesResponse.data?.dates || [];

      setState(prev => ({
        ...prev,
        availableCategories: categories,
        availableSources: sources,
        availableDates: dates,
        isLoadingFilters: false
      }));

    } catch (error) {
      console.error('Error loading filter options:', error);
      setState(prev => ({
        ...prev,
        isLoadingFilters: false,
        error: 'Failed to load filter options. Using default values.'
      }));
    }
  };

  const loadArticles = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const params = new URLSearchParams();
      
      // Add pagination
      params.append('limit', state.articlesPerPage.toString());
      params.append('offset', ((state.currentPage - 1) * state.articlesPerPage).toString());
      
      // Add filters
      if (state.filters.categories.length > 0) {
        // Note: API only supports single category, so we'll use the first one
        params.append('category', state.filters.categories[0]);
      }
      
      if (state.filters.sources.length > 0) {
        // Note: API only supports single source_id, so we'll use the first one
        params.append('source_id', state.filters.sources[0].toString());
      }
      
      if (state.filters.dateFrom) {
        params.append('start_date', state.filters.dateFrom);
      }
      
      if (state.filters.dateTo) {
        params.append('end_date', state.filters.dateTo);
      }

      const response = await axios.get(`${API_BASE_URL}/articles?${params.toString()}`);
      
      // The API returns articles directly as an array, not nested in an object
      const articlesData = Array.isArray(response.data) ? response.data : [];
      
      setState(prev => ({
        ...prev,
        articles: articlesData,
        totalArticles: articlesData.length,
        isLoading: false
      }));

    } catch (error) {
      console.error('Error loading articles:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load articles. Please try again.'
      }));
    }
  }, [state.filters, state.currentPage, state.articlesPerPage]);

  // Filter handlers
  const handleCategoryFilter = (categoryId) => {
    setState(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        categories: prev.filters.categories.includes(categoryId)
          ? prev.filters.categories.filter(id => id !== categoryId)
          : [...prev.filters.categories, categoryId]
      },
      currentPage: 1 // Reset to first page when filtering
    }));
  };

  const handleSourceFilter = (sourceId) => {
    setState(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        sources: prev.filters.sources.includes(sourceId)
          ? prev.filters.sources.filter(id => id !== sourceId)
          : [...prev.filters.sources, sourceId]
      },
      currentPage: 1
    }));
  };

  const handleDateFilter = (dateFrom, dateTo) => {
    setState(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        dateFrom,
        dateTo
      },
      currentPage: 1
    }));
  };

  const handleSearchFilter = (search) => {
    setState(prev => ({
      ...prev,
      filters: {
        ...prev.filters,
        search
      },
      currentPage: 1
    }));
  };

  const clearAllFilters = () => {
    setState(prev => ({
      ...prev,
      filters: {
        categories: [],
        sources: [],
        dateFrom: null,
        dateTo: null,
        search: ''
      },
      currentPage: 1
    }));
  };

  const toggleFilterSection = (section) => {
    setState(prev => ({
      ...prev,
      expandedSections: {
        ...prev.expandedSections,
        [section]: !prev.expandedSections[section]
      }
    }));
  };

  // Pagination handlers
  const handlePageChange = (newPage) => {
    setState(prev => ({ ...prev, currentPage: newPage }));
  };

  const getTotalPages = () => {
    return Math.ceil(state.totalArticles / state.articlesPerPage);
  };

  // Format date for display
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Get active filter count
  const getActiveFilterCount = () => {
    return state.filters.categories.length + state.filters.sources.length + 
           (state.filters.dateFrom ? 1 : 0) + (state.filters.dateTo ? 1 : 0) +
           (state.filters.search ? 1 : 0);
  };

  const filteredArticles = state.articles.filter(article => {
    if (!state.filters.search) return true;
    const searchTerm = state.filters.search.toLowerCase();
    return article.title?.toLowerCase().includes(searchTerm) ||
           article.summary?.toLowerCase().includes(searchTerm) ||
           article.source_name?.toLowerCase().includes(searchTerm);
  });

  return (
    <div className="home-page">
      <div className="home-header">
        <h1>Daily Scribe</h1>
        <p>Your curated news articles from trusted sources</p>
      </div>

      <div className="home-content">
        {/* Filters Sidebar */}
        <aside className={`filters-sidebar ${state.showFilters ? 'expanded' : 'collapsed'}`}>
          <div className="filters-header">
            <h2>Filters</h2>
            <button
              className="toggle-filters-btn"
              onClick={() => setState(prev => ({ ...prev, showFilters: !prev.showFilters }))}
            >
              {state.showFilters ? '←' : '→'}
            </button>
          </div>

          {state.showFilters && (
            <div className="filters-content">
              {/* Active filters summary */}
              {getActiveFilterCount() > 0 && (
                <div className="active-filters">
                  <div className="filter-summary">
                    <span>{getActiveFilterCount()} filter(s) active</span>
                    <button onClick={clearAllFilters} className="clear-all-btn">
                      Clear All
                    </button>
                  </div>
                </div>
              )}

              {/* Search filter */}
              <div className="filter-section">
                <div className="section-header">
                  <h3>🔍 Search</h3>
                </div>
                <input
                  type="text"
                  placeholder="Search articles..."
                  value={state.filters.search}
                  onChange={(e) => handleSearchFilter(e.target.value)}
                  className="search-input"
                />
              </div>

              {/* Date filter */}
              <div className="filter-section">
                <div 
                  className="section-header clickable"
                  onClick={() => toggleFilterSection('dates')}
                >
                  <h3>📅 Date Range</h3>
                  <span className={`expand-icon ${state.expandedSections.dates ? 'expanded' : ''}`}>
                    ▼
                  </span>
                </div>
                
                {state.expandedSections.dates && (
                  <div className="filter-options">
                    <div className="date-inputs">
                      <input
                        type="date"
                        placeholder="From date"
                        value={state.filters.dateFrom || ''}
                        onChange={(e) => handleDateFilter(e.target.value, state.filters.dateTo)}
                        className="date-input"
                      />
                      <input
                        type="date"
                        placeholder="To date"
                        value={state.filters.dateTo || ''}
                        onChange={(e) => handleDateFilter(state.filters.dateFrom, e.target.value)}
                        className="date-input"
                      />
                    </div>
                    
                    {/* Quick date options */}
                    <div className="quick-dates">
                      <button
                        onClick={() => {
                          const today = new Date().toISOString().split('T')[0];
                          handleDateFilter(today, today);
                        }}
                        className="quick-date-btn"
                      >
                        Today
                      </button>
                      <button
                        onClick={() => {
                          const today = new Date();
                          const yesterday = new Date(today);
                          yesterday.setDate(yesterday.getDate() - 1);
                          const yesterdayStr = yesterday.toISOString().split('T')[0];
                          handleDateFilter(yesterdayStr, yesterdayStr);
                        }}
                        className="quick-date-btn"
                      >
                        Yesterday
                      </button>
                      <button
                        onClick={() => {
                          const today = new Date();
                          const weekAgo = new Date(today);
                          weekAgo.setDate(weekAgo.getDate() - 7);
                          handleDateFilter(weekAgo.toISOString().split('T')[0], today.toISOString().split('T')[0]);
                        }}
                        className="quick-date-btn"
                      >
                        Last 7 days
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Categories filter */}
              <div className="filter-section">
                <div 
                  className="section-header clickable"
                  onClick={() => toggleFilterSection('categories')}
                >
                  <h3>📂 Categories</h3>
                  <div className="section-info">
                    <span className="selection-count">
                      {state.filters.categories.length} of {state.availableCategories.length}
                    </span>
                    <span className={`expand-icon ${state.expandedSections.categories ? 'expanded' : ''}`}>
                      ▼
                    </span>
                  </div>
                </div>
                
                {state.expandedSections.categories && (
                  <div className="filter-options">
                    {state.availableCategories.map(category => (
                      <label key={category.id} className="filter-option">
                        <input
                          type="checkbox"
                          checked={state.filters.categories.includes(category.id)}
                          onChange={() => handleCategoryFilter(category.id)}
                        />
                        <span className="option-name">{category.name}</span>
                        <span className="option-count">({category.count})</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Sources filter */}
              <div className="filter-section">
                <div 
                  className="section-header clickable"
                  onClick={() => toggleFilterSection('sources')}
                >
                  <h3>📰 Sources</h3>
                  <div className="section-info">
                    <span className="selection-count">
                      {state.filters.sources.length} of {state.availableSources.length}
                    </span>
                    <span className={`expand-icon ${state.expandedSections.sources ? 'expanded' : ''}`}>
                      ▼
                    </span>
                  </div>
                </div>
                
                {state.expandedSections.sources && (
                  <div className="filter-options">
                    {state.availableSources.map(source => (
                      <label key={source.id} className="filter-option">
                        <input
                          type="checkbox"
                          checked={state.filters.sources.includes(source.id)}
                          onChange={() => handleSourceFilter(source.id)}
                        />
                        <span className="option-name">{source.name}</span>
                        <span className="option-count">({source.count})</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </aside>

        {/* Main content */}
        <main role="main" className="articles-main">
          {/* Results header */}
          <div className="results-header">
            <div className="results-info">
              <h2>
                {state.isLoading ? 'Loading...' : `${filteredArticles.length} Articles`}
              </h2>
              {getActiveFilterCount() > 0 && (
                <span className="filter-applied">
                  ({getActiveFilterCount()} filter{getActiveFilterCount() > 1 ? 's' : ''} applied)
                </span>
              )}
            </div>
            
            {/* Sort options */}
            <div className="sort-options">
              <select className="sort-select">
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="title">Title A-Z</option>
                <option value="source">Source A-Z</option>
              </select>
            </div>
          </div>

          {/* Error message */}
          {state.error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {state.error}
            </div>
          )}

          {/* Loading state */}
          {state.isLoading && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading articles...</p>
            </div>
          )}

          {/* Articles grid */}
          {!state.isLoading && filteredArticles.length > 0 && (
            <div className="articles-grid">
              {filteredArticles.map(article => (
                <article key={article.id} className="article-card">
                  <div className="article-header">
                    <h3 className="article-title">
                      <a 
                        href={article.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="article-link"
                      >
                        {article.title}
                      </a>
                    </h3>
                    <div className="article-meta">
                      <span className="article-source">{article.source_name}</span>
                      <span className="article-category">{article.category}</span>
                      <span className="article-date">
                        {formatDate(article.published_date || article.created_at)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="article-content">
                    <p className="article-summary">{article.summary}</p>
                  </div>
                  
                  <div className="article-actions">
                    <a 
                      href={article.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="read-more-btn"
                    >
                      Read Full Article →
                    </a>
                  </div>
                </article>
              ))}
            </div>
          )}

          {/* Empty state */}
          {!state.isLoading && filteredArticles.length === 0 && (
            <div className="empty-state">
              <div className="empty-icon">📰</div>
              <h3>No Articles Found</h3>
              <p>
                {getActiveFilterCount() > 0 
                  ? 'No articles match your current filters. Try adjusting your search criteria.'
                  : 'No articles available at the moment. Please check back later.'
                }
              </p>
              {getActiveFilterCount() > 0 && (
                <button onClick={clearAllFilters} className="clear-filters-btn">
                  Clear All Filters
                </button>
              )}
            </div>
          )}

          {/* Pagination */}
          {!state.isLoading && filteredArticles.length > 0 && getTotalPages() > 1 && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(state.currentPage - 1)}
                disabled={state.currentPage === 1}
                className="pagination-btn"
              >
                ← Previous
              </button>
              
              <div className="pagination-info">
                Page {state.currentPage} of {getTotalPages()}
                <span className="total-articles">
                  ({state.totalArticles} total articles)
                </span>
              </div>
              
              <button
                onClick={() => handlePageChange(state.currentPage + 1)}
                disabled={state.currentPage === getTotalPages()}
                className="pagination-btn"
              >
                Next →
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Home;
