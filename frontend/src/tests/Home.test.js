import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import Home from '../components/Home';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock data
const mockArticles = [
  {
    id: 1,
    title: 'Test Article 1',
    summary: 'This is a test article summary',
    url: 'https://example.com/article1',
    published_date: '2025-09-07T08:00:00Z',
    category: 'technology',
    source_name: 'TechCrunch'
  },
  {
    id: 2,
    title: 'Test Article 2',
    summary: 'Another test article summary',
    url: 'https://example.com/article2',
    published_date: '2025-09-06T10:00:00Z',
    category: 'business',
    source_name: 'BBC News'
  }
];

const mockCategories = [
  { name: 'technology', display_name: 'Technology', article_count: 45 },
  { name: 'business', display_name: 'Business', article_count: 32 }
];

const mockSources = [
  { id: 1, name: 'TechCrunch', article_count: 25 },
  { id: 2, name: 'BBC News', article_count: 42 }
];

const mockDates = {
  dates: [
    { date: '2025-09-07', article_count: 25 },
    { date: '2025-09-06', article_count: 18 }
  ]
};

describe('Home Component', () => {
  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
    
    // Setup default mock responses
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/categories')) {
        return Promise.resolve({ data: mockCategories });
      }
      if (url.includes('/sources')) {
        return Promise.resolve({ data: mockSources });
      }
      if (url.includes('/digest/available-dates')) {
        return Promise.resolve({ data: mockDates });
      }
      if (url.includes('/articles')) {
        return Promise.resolve({
          data: {
            articles: mockArticles,
            total: mockArticles.length
          }
        });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });
  });

  test('renders home page with title and description', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
    expect(screen.getByText('Your curated news articles from trusted sources')).toBeInTheDocument();
  });

  test('loads and displays articles on mount', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    // Wait for articles to load
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      expect(screen.getByText('Test Article 2')).toBeInTheDocument();
    });
    
    // Check that API was called
    expect(mockedAxios.get).toHaveBeenCalledWith(
      expect.stringContaining('/articles')
    );
  });

  test('loads filter options on mount', async () => {
    render(<Home />);
    
    // Wait for filter options to load
    await waitFor(() => {
      expect(screen.getByText('Technology')).toBeInTheDocument();
      expect(screen.getByText('Business')).toBeInTheDocument();
      expect(screen.getByText('TechCrunch')).toBeInTheDocument();
      expect(screen.getByText('BBC News')).toBeInTheDocument();
    });
    
    // Check that filter APIs were called
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/categories');
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/sources');
    expect(mockedAxios.get).toHaveBeenCalledWith('http://localhost:8000/digest/available-dates');
  });

  test('search functionality filters articles', async () => {
    render(<Home />);
    
    // Wait for articles to load
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      expect(screen.getByText('Test Article 2')).toBeInTheDocument();
    });
    
    // Find and use search input
    const searchInput = screen.getByPlaceholderText('Search articles...');
    fireEvent.change(searchInput, { target: { value: 'Test Article 1' } });
    
    // Should show only matching articles
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      expect(screen.queryByText('Test Article 2')).not.toBeInTheDocument();
    });
  });

  test('category filter works correctly', async () => {
    render(<Home />);
    
    // Wait for filters to load
    await waitFor(() => {
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });
    
    // Click on technology category
    const technologyCheckbox = screen.getByLabelText(/Technology/);
    fireEvent.click(technologyCheckbox);
    
    // Should trigger API call with category filter
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('category=technology')
      );
    });
  });

  test('source filter works correctly', async () => {
    render(<Home />);
    
    // Wait for filters to load and expand sources section
    await waitFor(() => {
      expect(screen.getByText('📰 Sources')).toBeInTheDocument();
    });
    
    // Expand sources section
    fireEvent.click(screen.getByText('📰 Sources'));
    
    await waitFor(() => {
      expect(screen.getByText('TechCrunch')).toBeInTheDocument();
    });
    
    // Click on TechCrunch source
    const techcrunchCheckbox = screen.getByLabelText(/TechCrunch/);
    fireEvent.click(techcrunchCheckbox);
    
    // Should trigger API call with source filter
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('source_id=1')
      );
    });
  });

  test('date range filter works correctly', async () => {
    render(<Home />);
    
    // Wait for page to load and expand dates section
    await waitFor(() => {
      expect(screen.getByText('📅 Date Range')).toBeInTheDocument();
    });
    
    // Expand dates section
    fireEvent.click(screen.getByText('📅 Date Range'));
    
    // Set date range
    const fromDateInput = screen.getByDisplayValue('');
    fireEvent.change(fromDateInput, { target: { value: '2025-09-06' } });
    
    // Should trigger API call with date filter
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('start_date=2025-09-06')
      );
    });
  });

  test('quick date options work correctly', async () => {
    render(<Home />);
    
    // Wait for page to load and expand dates section
    await waitFor(() => {
      expect(screen.getByText('📅 Date Range')).toBeInTheDocument();
    });
    
    // Expand dates section
    fireEvent.click(screen.getByText('📅 Date Range'));
    
    // Click "Today" quick option
    const todayButton = screen.getByText('Today');
    fireEvent.click(todayButton);
    
    // Should trigger API call with today's date
    const today = new Date().toISOString().split('T')[0];
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining(`start_date=${today}`)
      );
    });
  });

  test('clear all filters functionality works', async () => {
    render(<Home />);
    
    // Wait for filters to load
    await waitFor(() => {
      expect(screen.getByText('Technology')).toBeInTheDocument();
    });
    
    // Apply a filter
    const technologyCheckbox = screen.getByLabelText(/Technology/);
    fireEvent.click(technologyCheckbox);
    
    // Wait for filter to be applied and clear all button to appear
    await waitFor(() => {
      expect(screen.getByText('Clear All')).toBeInTheDocument();
    });
    
    // Click clear all
    fireEvent.click(screen.getByText('Clear All'));
    
    // Should trigger API call without filters
    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenLastCalledWith(
        expect.not.stringContaining('category=')
      );
    });
  });

  test('handles API errors gracefully', async () => {
    // Mock API error
    mockedAxios.get.mockRejectedValue(new Error('API Error'));
    
    render(<Home />);
    
    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
    });
  });

  test('article links open in new tab', async () => {
    render(<Home />);
    
    // Wait for articles to load
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });
    
    // Check that article link has correct attributes
    const articleLink = screen.getByText('Test Article 1').closest('a');
    expect(articleLink).toHaveAttribute('target', '_blank');
    expect(articleLink).toHaveAttribute('rel', 'noopener noreferrer');
    expect(articleLink).toHaveAttribute('href', 'https://example.com/article1');
  });

  test('filter sidebar can be collapsed and expanded', async () => {
    render(<Home />);
    
    // Find the toggle button
    const toggleButton = screen.getByText('←');
    
    // Click to collapse
    fireEvent.click(toggleButton);
    
    // Should change to expand icon
    expect(screen.getByText('→')).toBeInTheDocument();
    
    // Click to expand
    fireEvent.click(screen.getByText('→'));
    
    // Should change back to collapse icon
    expect(screen.getByText('←')).toBeInTheDocument();
  });

  test('displays empty state when no articles found', async () => {
    // Mock empty response
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/articles')) {
        return Promise.resolve({
          data: {
            articles: [],
            total: 0
          }
        });
      }
      // Return default mocks for other endpoints
      if (url.includes('/categories')) {
        return Promise.resolve({ data: mockCategories });
      }
      if (url.includes('/sources')) {
        return Promise.resolve({ data: mockSources });
      }
      if (url.includes('/digest/available-dates')) {
        return Promise.resolve({ data: mockDates });
      }
      return Promise.reject(new Error('Unknown endpoint'));
    });
    
    render(<Home />);
    
    // Should show empty state
    await waitFor(() => {
      expect(screen.getByText('No Articles Found')).toBeInTheDocument();
      expect(screen.getByText(/No articles available at the moment/)).toBeInTheDocument();
    });
  });

  test('loading state is displayed correctly', () => {
    // Mock loading state by delaying response
    mockedAxios.get.mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    );
    
    render(<Home />);
    
    // Should show loading state
    expect(screen.getByText('Loading articles...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument();
  });
});
