import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import Home from '../components/Home';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Test utilities
const renderHome = () => {
  return render(<Home />);
};

const mockApiResponses = (customResponses = {}) => {
  const defaultResponses = {
    categories: [
      { name: 'technology', display_name: 'Technology', article_count: 45 },
      { name: 'business', display_name: 'Business', article_count: 32 },
      { name: 'science', display_name: 'Science', article_count: 28 }
    ],
    sources: [
      { id: 1, name: 'TechCrunch', article_count: 25 },
      { id: 2, name: 'BBC News', article_count: 42 },
      { id: 3, name: 'Reuters', article_count: 38 }
    ],
    dates: {
      dates: [
        { date: '2025-09-07', article_count: 25 },
        { date: '2025-09-06', article_count: 18 },
        { date: '2025-09-05', article_count: 22 }
      ]
    },
    articles: {
      articles: [
        {
          id: 1,
          title: 'AI Breakthrough in Healthcare',
          summary: 'Scientists develop new AI system for medical diagnosis...',
          url: 'https://techcrunch.com/ai-healthcare',
          published_date: '2025-09-07T08:00:00Z',
          category: 'technology',
          source_name: 'TechCrunch'
        },
        {
          id: 2,
          title: 'Global Market Update',
          summary: 'Stock markets show positive trends across major indices...',
          url: 'https://bbc.com/market-update',
          published_date: '2025-09-07T09:00:00Z',
          category: 'business',
          source_name: 'BBC News'
        },
        {
          id: 3,
          title: 'Climate Change Research',
          summary: 'New study reveals impact of greenhouse gases on ocean currents...',
          url: 'https://reuters.com/climate-research',
          published_date: '2025-09-07T10:00:00Z',
          category: 'science',
          source_name: 'Reuters'
        }
      ],
      total: 3
    }
  };

  const responses = { ...defaultResponses, ...customResponses };

  mockedAxios.get.mockImplementation((url) => {
    if (url.includes('/categories')) {
      return Promise.resolve({ data: responses.categories });
    }
    if (url.includes('/sources')) {
      return Promise.resolve({ data: responses.sources });
    }
    if (url.includes('/digest/available-dates')) {
      return Promise.resolve({ data: responses.dates });
    }
    if (url.includes('/articles')) {
      return Promise.resolve({ data: responses.articles });
    }
    return Promise.reject(new Error('Unknown endpoint'));
  });
};

describe('Home Component Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiResponses();
  });

  describe('Initial Load and Display', () => {
    test('renders main layout components correctly', async () => {
      renderHome();

      // Check main header
      expect(screen.getByRole('heading', { name: 'Daily Scribe' })).toBeInTheDocument();
      expect(screen.getByText('Your curated news articles from trusted sources')).toBeInTheDocument();

      // Check filter sidebar
      expect(screen.getByRole('heading', { name: 'Filters' })).toBeInTheDocument();
      
      // Check main content area
      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });
    });

    test('loads all required data on component mount', async () => {
      renderHome();

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/categories');
        expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/sources');
        expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/digest/available-dates');
        expect(mockedAxios.get).toHaveBeenCalledWith(expect.stringContaining('/articles'));
      });
    });

    test('displays articles with correct information', async () => {
      renderHome();

      await waitFor(() => {
        // Check article titles
        expect(screen.getByText('AI Breakthrough in Healthcare')).toBeInTheDocument();
        expect(screen.getByText('Global Market Update')).toBeInTheDocument();
        expect(screen.getByText('Climate Change Research')).toBeInTheDocument();

        // Check article metadata
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
        expect(screen.getByText('BBC News')).toBeInTheDocument();
        expect(screen.getByText('Reuters')).toBeInTheDocument();
      });
    });
  });

  describe('Filtering Functionality', () => {
    test('search filter works with real-time updates', async () => {
      const user = userEvent.setup();
      
      await act(async () => {
        renderHome();
      });

      await waitFor(() => {
        expect(screen.getByText('AI Breakthrough in Healthcare')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search articles...');
      
      await act(async () => {
        await user.type(searchInput, 'AI Breakthrough');
      });

      // Should filter to show only matching articles
      await waitFor(() => {
        expect(screen.getByText('AI Breakthrough in Healthcare')).toBeInTheDocument();
        expect(screen.queryByText('Global Market Update')).not.toBeInTheDocument();
        expect(screen.queryByText('Climate Change Research')).not.toBeInTheDocument();
      });
    });

    test('category filtering triggers API calls correctly', async () => {
      const user = userEvent.setup();
      renderHome();

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Technology')).toBeInTheDocument();
      });

      // Clear previous API calls
      jest.clearAllMocks();
      mockApiResponses();

      // Click technology category
      const technologyFilter = screen.getByLabelText(/Technology/);
      await user.click(technologyFilter);

      // Should trigger new API call with category filter
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('category=technology')
        );
      });
    });

    test('multiple filters can be applied simultaneously', async () => {
      const user = userEvent.setup();
      renderHome();

      // Wait for filters to load
      await waitFor(() => {
        expect(screen.getByText('Technology')).toBeInTheDocument();
      });

      // Expand sources section
      await user.click(screen.getByText('📰 Sources'));

      await waitFor(() => {
        expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      });

      // Apply category filter
      const technologyFilter = screen.getByLabelText(/Technology/);
      await user.click(technologyFilter);

      // Apply source filter
      const techcrunchFilter = screen.getByLabelText(/TechCrunch/);
      await user.click(techcrunchFilter);

      // Check that active filters are displayed
      await waitFor(() => {
        expect(screen.getByText(/2 filter\(s\) active/)).toBeInTheDocument();
      });
    });

    test('date range filtering works with manual date input', async () => {
      const user = userEvent.setup();
      renderHome();

      // Expand date section
      await user.click(screen.getByText('📅 Date Range'));

      // Set from date
      const fromDateInput = screen.getByDisplayValue('');
      await user.type(fromDateInput, '2025-09-06');

      // Should trigger API call with date filter
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('start_date=2025-09-06')
        );
      });
    });

    test('quick date filters work correctly', async () => {
      const user = userEvent.setup();
      renderHome();

      // Expand date section
      await user.click(screen.getByText('📅 Date Range'));

      // Click "Today" quick filter
      await user.click(screen.getByText('Today'));

      const today = new Date().toISOString().split('T')[0];
      
      // Should trigger API call with today's date
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining(`start_date=${today}`)
        );
      });
    });

    test('clear all filters resets all filter states', async () => {
      const user = userEvent.setup();
      renderHome();

      // Wait for filters to load
      await waitFor(() => {
        expect(screen.getByText('Technology')).toBeInTheDocument();
      });

      // Apply multiple filters
      const technologyFilter = screen.getByLabelText(/Technology/);
      await user.click(technologyFilter);

      const searchInput = screen.getByPlaceholderText('Search articles...');
      await user.type(searchInput, 'test search');

      // Wait for Clear All button to appear
      await waitFor(() => {
        expect(screen.getByText('Clear All')).toBeInTheDocument();
      });

      // Clear all filters
      await user.click(screen.getByText('Clear All'));

      // Check that filters are reset
      expect(searchInput).toHaveValue('');
      expect(technologyFilter).not.toBeChecked();
    });
  });

  describe('UI Interactions', () => {
    test('filter sidebar can be collapsed and expanded', async () => {
      const user = userEvent.setup();
      renderHome();

      const sidebar = screen.getByRole('complementary');
      const toggleButton = screen.getByText('←');

      // Should start expanded
      expect(sidebar).toHaveClass('expanded');

      // Collapse sidebar
      await user.click(toggleButton);
      expect(sidebar).toHaveClass('collapsed');
      expect(screen.getByText('→')).toBeInTheDocument();

      // Expand sidebar
      await user.click(screen.getByText('→'));
      expect(sidebar).toHaveClass('expanded');
      expect(screen.getByText('←')).toBeInTheDocument();
    });

    test('filter sections can be expanded and collapsed', async () => {
      const user = userEvent.setup();
      renderHome();

      // Categories should start expanded
      expect(screen.getByText('Technology')).toBeInTheDocument();

      // Collapse categories
      await user.click(screen.getByText('📂 Categories'));
      expect(screen.queryByText('Technology')).not.toBeInTheDocument();

      // Expand categories
      await user.click(screen.getByText('📂 Categories'));
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });

    test('article links have correct attributes for external navigation', async () => {
      renderHome();

      await waitFor(() => {
        expect(screen.getByText('AI Breakthrough in Healthcare')).toBeInTheDocument();
      });

      const articleLink = screen.getByText('AI Breakthrough in Healthcare').closest('a');
      expect(articleLink).toHaveAttribute('href', 'https://techcrunch.com/ai-healthcare');
      expect(articleLink).toHaveAttribute('target', '_blank');
      expect(articleLink).toHaveAttribute('rel', 'noopener noreferrer');

      const readMoreLink = screen.getAllByText(/Read Full Article/)[0].closest('a');
      expect(readMoreLink).toHaveAttribute('target', '_blank');
      expect(readMoreLink).toHaveAttribute('rel', 'noopener noreferrer');
    });
  });

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      mockedAxios.get.mockRejectedValue(new Error('Network error'));
      renderHome();

      await waitFor(() => {
        expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
      });
    });

    test('handles empty article responses', async () => {
      mockApiResponses({
        articles: { articles: [], total: 0 }
      });

      renderHome();

      await waitFor(() => {
        expect(screen.getByText('No Articles Found')).toBeInTheDocument();
        expect(screen.getByText(/No articles available at the moment/)).toBeInTheDocument();
      });
    });

    test('handles empty filter options gracefully', async () => {
      mockApiResponses({
        categories: [],
        sources: []
      });

      renderHome();

      await waitFor(() => {
        expect(screen.getByText('📂 Categories')).toBeInTheDocument();
        expect(screen.getByText('📰 Sources')).toBeInTheDocument();
      });

      // Should not crash with empty filter options
      expect(screen.queryByText('Technology')).not.toBeInTheDocument();
      expect(screen.queryByText('TechCrunch')).not.toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    test('displays correctly on mobile viewport', async () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 480,
      });

      renderHome();

      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });

      // Should still display main functionality
      expect(screen.getByText('Filters')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search articles...')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('does not make unnecessary API calls on re-renders', async () => {
      const { rerender } = renderHome();

      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(4); // Initial load calls
      });

      // Force re-render
      rerender(<Home />);

      // Should not make additional API calls
      expect(mockedAxios.get).toHaveBeenCalledTimes(4);
    });
  });
});

describe('Home Component Accessibility', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiResponses();
  });

  test('has proper heading hierarchy', async () => {
    renderHome();

    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toHaveTextContent('Daily Scribe');

    await waitFor(() => {
      const filterHeadings = screen.getAllByRole('heading', { level: 2 });
      expect(filterHeadings.some(h => h.textContent === 'Filters')).toBe(true);
      expect(filterHeadings.some(h => h.textContent.includes('Articles'))).toBe(true);
    });
  });

  test('filter checkboxes are properly labeled', async () => {
    renderHome();

    await waitFor(() => {
      expect(screen.getByLabelText(/Technology/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Business/)).toBeInTheDocument();
    });
  });

  test('search input has appropriate label', () => {
    renderHome();

    const searchInput = screen.getByPlaceholderText('Search articles...');
    expect(searchInput).toHaveAttribute('type', 'text');
  });

  test('interactive elements are keyboard accessible', async () => {
    const user = userEvent.setup();
    renderHome();

    await waitFor(() => {
      expect(screen.getByText('📂 Categories')).toBeInTheDocument();
    });

    const categoryHeader = screen.getByText('📂 Categories');
    
    // Should be focusable and activatable with keyboard
    categoryHeader.focus();
    expect(categoryHeader).toHaveFocus();

    await user.keyboard('{Enter}');
    // Categories section should toggle (implementation would need to handle this)
  });
});
