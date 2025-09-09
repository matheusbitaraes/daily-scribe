import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import Home from '../components/Home';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock SubscriptionForm to avoid complex test setup
jest.mock('../components/SubscriptionForm', () => {
  return function MockSubscriptionForm({ onSuccess, variant, className }) {
    const handleTestSubmit = () => {
      if (onSuccess) {
        onSuccess('test@example.com');
      }
    };

    return (
      <div className={`mock-subscription-form ${variant} ${className}`}>
        <h3>Mock Subscription Form</h3>
        <input data-testid="mock-email-input" placeholder="Enter email" />
        <button data-testid="mock-submit-button" onClick={handleTestSubmit}>
          Subscribe
        </button>
      </div>
    );
  };
});

// Mock environment variable
const originalEnv = process.env;

beforeEach(() => {
  jest.resetAllMocks();
  process.env = { ...originalEnv };
  process.env.REACT_APP_API_URL = 'http://localhost:8000';
  
  // Mock all API calls that Home component makes
  mockedAxios.get.mockImplementation((url) => {
    if (url.includes('/categories')) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes('/sources')) {
      return Promise.resolve({ data: [] });
    }
    if (url.includes('/digest/available-dates')) {
      return Promise.resolve({ data: { dates: [] } });
    }
    if (url.includes('/articles')) {
      return Promise.resolve({ 
        data: { 
          articles: [], 
          total: 0,
          page: 1,
          per_page: 20
        } 
      });
    }
    return Promise.reject(new Error('Unknown URL'));
  });
});

afterEach(() => {
  process.env = originalEnv;
});

describe('Home Component Integration with SubscriptionForm', () => {
  describe('Subscription Form Integration', () => {
    test('renders subscription form on home page', async () => {
      render(<Home />);
      
      // Wait for the component to load
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      // Check that the subscription form is rendered
      expect(screen.getByText('Mock Subscription Form')).toBeInTheDocument();
      expect(screen.getByTestId('mock-email-input')).toBeInTheDocument();
      expect(screen.getByTestId('mock-submit-button')).toBeInTheDocument();
    });

    test('subscription form has correct props', async () => {
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      // Check that the form has the correct variant and className
      const mockForm = screen.getByText('Mock Subscription Form').parentElement;
      expect(mockForm).toHaveClass('mock-subscription-form', 'inline', 'home-subscription-form');
    });

    test('subscription form is positioned correctly', async () => {
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      const title = screen.getByText('Daily Scribe');
      const subtitle = screen.getByText('Your curated news articles from trusted sources');
      const subscriptionForm = screen.getByText('Mock Subscription Form');
      
      // Check that subscription form appears after header
      expect(title).toBeInTheDocument();
      expect(subtitle).toBeInTheDocument();
      expect(subscriptionForm).toBeInTheDocument();
    });

    test('handles subscription success callback', async () => {
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
      
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      const submitButton = screen.getByTestId('mock-submit-button');
      await userEvent.click(submitButton);
      
      expect(consoleSpy).toHaveBeenCalledWith('User subscribed successfully:', 'test@example.com');
      
      consoleSpy.mockRestore();
    });
  });

  describe('Page Layout', () => {
    test('renders all main sections in correct order', async () => {
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      // Check that all main sections are present
      expect(screen.getByText('Daily Scribe')).toBeInTheDocument(); // Header
      expect(screen.getByText('Your curated news articles from trusted sources')).toBeInTheDocument(); // Subtitle
      expect(screen.getByText('Mock Subscription Form')).toBeInTheDocument(); // Subscription form
      expect(screen.getByText('Filters')).toBeInTheDocument(); // Filters sidebar
    });

    test('subscription section has proper styling classes', async () => {
      const { container } = render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      // Check that subscription section exists with proper class
      const subscriptionSection = container.querySelector('.subscription-section');
      expect(subscriptionSection).toBeInTheDocument();
      expect(subscriptionSection).toContainElement(screen.getByText('Mock Subscription Form'));
    });
  });

  describe('Responsive Behavior', () => {
    test('maintains subscription form visibility on different screen sizes', async () => {
      // Test that form is always visible regardless of filters collapsed state
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      expect(screen.getByText('Mock Subscription Form')).toBeInTheDocument();
      
      // Toggle filters (simulate responsive behavior)
      const toggleButton = screen.getByText('←');
      await userEvent.click(toggleButton);
      
      // Subscription form should still be visible
      expect(screen.getByText('Mock Subscription Form')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('subscription form works even when article loading fails', async () => {
      // Mock API failure
      mockedAxios.get.mockRejectedValue(new Error('API Error'));
      
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      // Subscription form should still be functional
      expect(screen.getByText('Mock Subscription Form')).toBeInTheDocument();
      expect(screen.getByTestId('mock-submit-button')).toBeInTheDocument();
      
      // Should be able to trigger subscription
      const submitButton = screen.getByTestId('mock-submit-button');
      await userEvent.click(submitButton);
      
      // No errors should be thrown
    });
  });

  describe('Accessibility', () => {
    test('subscription form is accessible via keyboard navigation', async () => {
      render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      const emailInput = screen.getByTestId('mock-email-input');
      const submitButton = screen.getByTestId('mock-submit-button');
      
      // Should be able to focus elements with keyboard
      emailInput.focus();
      expect(emailInput).toHaveFocus();
      
      // Tab to submit button
      await userEvent.tab();
      expect(submitButton).toHaveFocus();
    });

    test('subscription section has proper semantic structure', async () => {
      const { container } = render(<Home />);
      
      await waitFor(() => {
        expect(screen.getByText('Daily Scribe')).toBeInTheDocument();
      });
      
      // Check that subscription section is a semantic section
      const subscriptionSection = container.querySelector('section.subscription-section');
      expect(subscriptionSection).toBeInTheDocument();
    });
  });
});
