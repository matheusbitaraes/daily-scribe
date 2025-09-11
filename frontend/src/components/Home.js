import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import SubscriptionForm from './SubscriptionForm';
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

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  const loadFilterOptions = useCallback(async () => {
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
  }, [API_BASE_URL]);

  // Load filter options on component mount
  useEffect(() => {
    loadFilterOptions();
  }, [loadFilterOptions]);

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
  }, [API_BASE_URL, state.filters, state.currentPage, state.articlesPerPage]);

  // Load articles when filters or pagination changes
  useEffect(() => {
    loadArticles();
  }, [loadArticles]);

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

      {/* Newsletter Subscription Section */}
      <section className="subscription-section">
        <SubscriptionForm 
          variant="inline"
          className="home-subscription-form"
          onSuccess={(email) => {
            console.log('User subscribed successfully:', email);
            // Could add analytics tracking here
          }}
        />
      </section>


      <div className="home-content">
        <main role="main" className="articles-main">
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
