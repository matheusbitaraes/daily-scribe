/**
 * Performance optimization utilities for mobile and web
 * Includes debouncing, throttling, lazy loading, and memory management
 */
import React from 'react';

/**
 * Debounce function to limit the rate of function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Delay in milliseconds
 * @param {boolean} immediate - Whether to execute immediately on first call
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait, immediate = false) => {
  let timeout;
  
  return function executedFunction(...args) {
    const later = () => {
      timeout = null;
      if (!immediate) func.apply(this, args);
    };
    
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    
    if (callNow) func.apply(this, args);
  };
};

/**
 * Throttle function to limit function execution frequency
 * @param {Function} func - Function to throttle
 * @param {number} delay - Minimum delay between executions
 * @returns {Function} Throttled function
 */
export const throttle = (func, delay) => {
  let inThrottle;
  
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, delay);
    }
  };
};

/**
 * Intersection Observer for lazy loading components
 * @param {Object} options - Observer options
 * @returns {Object} Observer utilities
 */
export const createIntersectionObserver = (options = {}) => {
  const defaultOptions = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    ...options
  };

  let observer;
  const targets = new Map();

  const observe = (element, callback) => {
    if (!observer) {
      observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          const callback = targets.get(entry.target);
          if (callback && entry.isIntersecting) {
            callback(entry);
            observer.unobserve(entry.target);
            targets.delete(entry.target);
          }
        });
      }, defaultOptions);
    }

    targets.set(element, callback);
    observer.observe(element);
  };

  const unobserve = (element) => {
    if (observer) {
      observer.unobserve(element);
      targets.delete(element);
    }
  };

  const disconnect = () => {
    if (observer) {
      observer.disconnect();
      targets.clear();
    }
  };

  return { observe, unobserve, disconnect };
};

/**
 * Lazy loading hook for React components
 * @param {Function} importFunc - Dynamic import function
 * @param {Object} options - Loading options
 * @returns {Object} Component and loading state
 */
export const useLazyLoad = (importFunc, options = {}) => {
  const [component, setComponent] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const load = React.useCallback(async () => {
    if (component || loading) return;

    try {
      setLoading(true);
      setError(null);
      
      const module = await importFunc();
      setComponent(() => module.default || module);
    } catch (err) {
      setError(err);
      console.error('Lazy loading failed:', err);
    } finally {
      setLoading(false);
    }
  }, [importFunc, component, loading]);

  return { component, loading, error, load };
};

/**
 * Performance monitoring utilities
 */
export const performance = {
  /**
   * Measure function execution time
   * @param {Function} func - Function to measure
   * @param {string} label - Performance label
   * @returns {*} Function result
   */
  measure: async (func, label = 'function') => {
    const start = performance.now();
    const result = await func();
    const end = performance.now();
    
    console.log(`${label} took ${(end - start).toFixed(2)}ms`);
    return result;
  },

  /**
   * Mark performance events
   * @param {string} name - Event name
   */
  mark: (name) => {
    if (window.performance && window.performance.mark) {
      window.performance.mark(name);
    }
  },

  /**
   * Measure time between marks
   * @param {string} name - Measure name
   * @param {string} startMark - Start mark name
   * @param {string} endMark - End mark name
   */
  measureBetween: (name, startMark, endMark) => {
    if (window.performance && window.performance.measure) {
      window.performance.measure(name, startMark, endMark);
    }
  }
};

/**
 * Memory management utilities
 */
export const memory = {
  /**
   * Clean up event listeners
   * @param {Array} listeners - Array of listener objects {element, event, handler}
   */
  cleanupListeners: (listeners) => {
    listeners.forEach(({ element, event, handler }) => {
      if (element && element.removeEventListener) {
        element.removeEventListener(event, handler);
      }
    });
  },

  /**
   * Cancel pending requests
   * @param {Array} controllers - Array of AbortController instances
   */
  cancelRequests: (controllers) => {
    controllers.forEach(controller => {
      if (controller && controller.abort) {
        controller.abort();
      }
    });
  },

  /**
   * Clear timeouts and intervals
   * @param {Array} timers - Array of timer IDs
   */
  clearTimers: (timers) => {
    timers.forEach(id => {
      clearTimeout(id);
      clearInterval(id);
    });
  }
};

/**
 * Device detection utilities
 */
export const device = {
  /**
   * Detect if device is mobile
   * @returns {boolean} True if mobile device
   */
  isMobile: () => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );
  },

  /**
   * Detect if device supports touch
   * @returns {boolean} True if touch supported
   */
  isTouch: () => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  },

  /**
   * Get device pixel ratio
   * @returns {number} Device pixel ratio
   */
  getPixelRatio: () => {
    return window.devicePixelRatio || 1;
  },

  /**
   * Get viewport dimensions
   * @returns {Object} Viewport width and height
   */
  getViewport: () => ({
    width: Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0),
    height: Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)
  }),

  /**
   * Detect connection speed
   * @returns {string} Connection type
   */
  getConnectionSpeed: () => {
    if (navigator.connection) {
      return navigator.connection.effectiveType || 'unknown';
    }
    return 'unknown';
  }
};

/**
 * Bundle size optimization utilities
 */
export const bundle = {
  /**
   * Dynamic import with error handling
   * @param {Function} importFunc - Import function
   * @returns {Promise} Import promise
   */
  dynamicImport: async (importFunc) => {
    try {
      return await importFunc();
    } catch (error) {
      console.error('Dynamic import failed:', error);
      throw error;
    }
  },

  /**
   * Preload critical resources
   * @param {Array} urls - URLs to preload
   * @param {string} as - Resource type (script, style, etc.)
   */
  preload: (urls, as = 'script') => {
    urls.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = url;
      link.as = as;
      document.head.appendChild(link);
    });
  },

  /**
   * Code splitting helper
   * @param {Function} loader - Component loader function
   * @returns {React.Component} Lazy component
   */
  lazy: (loader) => {
    return React.lazy(() => loader().catch(err => {
      console.error('Code splitting failed:', err);
      // Return fallback component
      return { default: () => React.createElement('div', null, 'Failed to load component') };
    }));
  }
};

/**
 * API optimization utilities
 */
export const api = {
  /**
   * Create debounced API call
   * @param {Function} apiCall - API function
   * @param {number} delay - Debounce delay
   * @returns {Function} Debounced API function
   */
  debouncedCall: (apiCall, delay = 300) => {
    return debounce(apiCall, delay);
  },

  /**
   * Request deduplication
   */
  requestCache: new Map(),

  /**
   * Deduplicated fetch
   * @param {string} url - Request URL
   * @param {Object} options - Fetch options
   * @returns {Promise} Fetch promise
   */
  deDupedFetch: (url, options = {}) => {
    const key = `${url}${JSON.stringify(options)}`;
    
    if (api.requestCache.has(key)) {
      return api.requestCache.get(key);
    }

    const request = fetch(url, options)
      .finally(() => {
        // Remove from cache after completion
        setTimeout(() => api.requestCache.delete(key), 1000);
      });

    api.requestCache.set(key, request);
    return request;
  }
};

/**
 * Animation optimization utilities
 */
export const animation = {
  /**
   * Request animation frame with fallback
   * @param {Function} callback - Animation callback
   * @returns {number} Animation frame ID
   */
  requestFrame: (callback) => {
    if (window.requestAnimationFrame) {
      return window.requestAnimationFrame(callback);
    }
    return setTimeout(callback, 16); // ~60fps fallback
  },

  /**
   * Cancel animation frame
   * @param {number} id - Animation frame ID
   */
  cancelFrame: (id) => {
    if (window.cancelAnimationFrame) {
      window.cancelAnimationFrame(id);
    } else {
      clearTimeout(id);
    }
  },

  /**
   * Smooth scroll utility
   * @param {Element} element - Target element
   * @param {Object} options - Scroll options
   */
  smoothScroll: (element, options = {}) => {
    if (element.scrollIntoView) {
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'nearest',
        ...options
      });
    }
  }
};

/**
 * Form optimization utilities
 */
export const form = {
  /**
   * Auto-save form data
   * @param {string} key - Storage key
   * @param {Object} data - Form data
   * @param {number} delay - Save delay
   */
  autoSave: debounce((key, data) => {
    try {
      localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.warn('Auto-save failed:', error);
    }
  }, 1000),

  /**
   * Restore form data
   * @param {string} key - Storage key
   * @returns {Object|null} Restored data
   */
  restore: (key) => {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.warn('Restore failed:', error);
      return null;
    }
  },

  /**
   * Clear saved form data
   * @param {string} key - Storage key
   */
  clearSaved: (key) => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.warn('Clear saved data failed:', error);
    }
  }
};
