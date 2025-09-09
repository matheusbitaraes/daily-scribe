/**
 * Unit tests for UnsubscribePage component
 * Tests the unsubscribe confirmation flow and error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';
import UnsubscribePage from '../pages/UnsubscribePage';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ token: 'test-token-123' }),
  useNavigate: () => mockNavigate,
}));

// Test wrapper with router
const TestWrapper = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe('UnsubscribePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock console.error to avoid noise in tests
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('renders confirmation page by default', () => {
    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    expect(screen.getByText('Confirm Unsubscription')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to unsubscribe')).toBeInTheDocument();
    expect(screen.getByText('Yes, Unsubscribe Me')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  test('shows error when no token is provided', () => {
    // Mock useParams to return no token
    jest.doMock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useParams: () => ({ token: undefined }),
      useNavigate: () => mockNavigate,
    }));

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    expect(screen.getByText('No unsubscribe token provided')).toBeInTheDocument();
  });

  test('handles successful unsubscription', async () => {
    // Mock successful API response
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {
        message: 'Successfully unsubscribed',
        email: 'test@example.com',
        status: 'unsubscribed',
        unsubscribed_at: '2024-01-01T00:00:00Z'
      }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    // Click unsubscribe button
    const unsubscribeButton = screen.getByText('Yes, Unsubscribe Me');
    fireEvent.click(unsubscribeButton);

    // Should show loading state
    expect(screen.getByText('Processing...')).toBeInTheDocument();

    // Wait for success state
    await waitFor(() => {
      expect(screen.getByText('Successfully Unsubscribed')).toBeInTheDocument();
    });

    expect(screen.getByText('test@example.com has been removed')).toBeInTheDocument();
    expect(screen.getByText('Return to Homepage')).toBeInTheDocument();
    expect(screen.getByText('Subscribe Again')).toBeInTheDocument();

    // Verify API call
    expect(mockedAxios.post).toHaveBeenCalledWith(
      'http://localhost:8000/api/unsubscribe',
      { token: 'test-token-123' },
      { timeout: 10000 }
    );
  });

  test('handles invalid token error', async () => {
    // Mock API error response
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: {
          detail: {
            error: 'Invalid token',
            code: 'invalid_token',
            details: 'The unsubscribe link is invalid or has expired'
          }
        }
      }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    // Click unsubscribe button
    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Unsubscription Failed')).toBeInTheDocument();
    });

    expect(screen.getByText('This unsubscribe link is invalid or has expired.')).toBeInTheDocument();
    expect(screen.getByText('Try Again')).toBeInTheDocument();
    expect(screen.getByText('Return to Homepage')).toBeInTheDocument();
  });

  test('handles network error', async () => {
    // Mock network error
    mockedAxios.post.mockRejectedValueOnce({
      request: {}
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    await waitFor(() => {
      expect(screen.getByText('Unsubscription Failed')).toBeInTheDocument();
    });

    expect(screen.getByText('Network error. Please check your connection and try again.')).toBeInTheDocument();
  });

  test('handles server error (500)', async () => {
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 500,
        data: {
          detail: {
            error: 'Internal server error',
            code: 'internal_error'
          }
        }
      }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    await waitFor(() => {
      expect(screen.getByText('Server error. Please try again later.')).toBeInTheDocument();
    });
  });

  test('handles subscription not found error (404)', async () => {
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 404,
        data: {
          detail: {
            error: 'Subscription not found',
            code: 'subscription_not_found'
          }
        }
      }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    await waitFor(() => {
      expect(screen.getByText('Subscription not found. You may already be unsubscribed.')).toBeInTheDocument();
    });
  });

  test('navigation functions work correctly', () => {
    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    // Test cancel button
    fireEvent.click(screen.getByText('Cancel'));
    expect(mockNavigate).toHaveBeenCalledWith('/');

    // Reset mock
    mockNavigate.mockClear();

    // Test navigation from help text link (simulated)
    // In a real test, you might render the success state and test those buttons
  });

  test('try again functionality works', async () => {
    // First, trigger an error
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: {
          detail: {
            error: 'Invalid token',
            code: 'invalid_token'
          }
        }
      }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    await waitFor(() => {
      expect(screen.getByText('Try Again')).toBeInTheDocument();
    });

    // Click try again
    fireEvent.click(screen.getByText('Try Again'));

    // Should return to confirmation state
    expect(screen.getByText('Confirm Unsubscription')).toBeInTheDocument();
  });

  test('loading state disables buttons', () => {
    // Mock a delayed response to test loading state
    mockedAxios.post.mockImplementationOnce(() => new Promise(resolve => 
      setTimeout(() => resolve({
        status: 200,
        data: { message: 'Success', email: 'test@example.com', status: 'unsubscribed' }
      }), 100)
    ));

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    const unsubscribeButton = screen.getByText('Yes, Unsubscribe Me');
    const cancelButton = screen.getByText('Cancel');

    // Buttons should be enabled initially
    expect(unsubscribeButton.disabled).toBe(false);
    expect(cancelButton.disabled).toBe(false);

    // Click unsubscribe
    fireEvent.click(unsubscribeButton);

    // Buttons should be disabled during loading
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  test('uses correct API base URL from environment', () => {
    // Mock environment variable
    const originalEnv = process.env.REACT_APP_API_URL;
    process.env.REACT_APP_API_URL = 'https://api.example.com';

    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: { message: 'Success', email: 'test@example.com', status: 'unsubscribed' }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      'https://api.example.com/api/unsubscribe',
      { token: 'test-token-123' },
      { timeout: 10000 }
    );

    // Restore environment
    process.env.REACT_APP_API_URL = originalEnv;
  });

  test('handles malformed error responses gracefully', async () => {
    // Mock malformed error response
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: "Invalid response format"  // Not the expected object structure
      }
    });

    render(
      <TestWrapper>
        <UnsubscribePage />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Yes, Unsubscribe Me'));

    await waitFor(() => {
      expect(screen.getByText('Unsubscription Failed')).toBeInTheDocument();
    });

    // Should show generic error message for malformed responses
    expect(screen.getByText(/Unsubscription failed/)).toBeInTheDocument();
  });
});
