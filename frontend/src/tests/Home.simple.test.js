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
  }
];

const mockCategories = [
  { name: 'technology', display_name: 'Technology', article_count: 45 }
];

const mockSources = [
  { id: 1, name: 'TechCrunch', article_count: 25 }
];

const mockDates = {
  dates: [
    { date: '2025-09-07', article_count: 25 }
  ]
};

describe('Home Component - Basic Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
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

  test('renders home page correctly', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
    expect(screen.getByText('Your curated news articles from trusted sources')).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  test('loads articles on mount', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });
    
    expect(mockedAxios.get).toHaveBeenCalledWith(
      expect.stringContaining('/articles')
    );
  });

  test('search functionality works', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });
    
    const searchInput = screen.getByPlaceholderText('Search articles...');
    
    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'Test Article' } });
    });
    
    expect(screen.getByText('Test Article 1')).toBeInTheDocument();
  });

  test('category filter section is present', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('📂 Categories')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  test('handles API errors gracefully', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'));
    
    await act(async () => {
      render(<Home />);
    });
    
    await waitFor(() => {
      expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
    });
  });

  test('filter sidebar can be toggled', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    const sidebar = screen.getByRole('complementary');
    expect(sidebar).toHaveClass('expanded');
    
    const toggleButton = screen.getByText('←');
    
    await act(async () => {
      fireEvent.click(toggleButton);
    });
    
    expect(sidebar).toHaveClass('collapsed');
  });

  test('article links have correct attributes', async () => {
    await act(async () => {
      render(<Home />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });
    
    const articleLink = screen.getByText('Test Article 1').closest('a');
    expect(articleLink).toHaveAttribute('target', '_blank');
    expect(articleLink).toHaveAttribute('rel', 'noopener noreferrer');
    expect(articleLink).toHaveAttribute('href', 'https://example.com/article1');
  });

  test('displays empty state when no articles', async () => {
    mockedAxios.get.mockImplementation((url) => {
      if (url.includes('/articles')) {
        return Promise.resolve({
          data: { articles: [], total: 0 }
        });
      }
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
    
    await act(async () => {
      render(<Home />);
    });
    
    await waitFor(() => {
      expect(screen.getByText('No Articles Found')).toBeInTheDocument();
    });
  });
});
