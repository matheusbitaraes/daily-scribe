import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import axios from 'axios';
import EmailVerificationPage from '../pages/EmailVerificationPage';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock environment variable
const originalEnv = process.env;

beforeEach(() => {
  jest.resetAllMocks();
  process.env = { ...originalEnv };
  process.env.REACT_APP_API_URL = 'http://localhost:8000';
});

afterEach(() => {
  process.env = originalEnv;
});

// Helper function to render component with router and search params
const renderWithRouter = (searchParams = '') => {
  const initialEntries = searchParams ? [`/verify-email?${searchParams}`] : ['/verify-email'];
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <EmailVerificationPage />
    </MemoryRouter>
  );
};

describe('EmailVerificationPage', () => {
  describe('Loading State', () => {
    test('shows loading state when verifying token', async () => {
      mockSearchParams = 'token=valid-token-123';
      
      // Mock a delayed response
      let resolvePromise;
      const mockPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockedAxios.get.mockReturnValueOnce(mockPromise);
      
      renderWithRouter('token=valid-token-123');
      
      // Should show loading state initially
      expect(screen.getByText('Verifying Your Email')).toBeInTheDocument();
      expect(screen.getByText('Please wait while we confirm your subscription...')).toBeInTheDocument();
      expect(screen.getByRole('generic', { hidden: true })).toHaveClass('loading-spinner');
      
      // Resolve the promise
      resolvePromise({ status: 200, data: { email: 'test@example.com' } });
    });

    test('makes API call with correct token', async () => {
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=test-token-456');
      
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          'http://localhost:8000/api/verify-email',
          {
            params: { token: 'test-token-456' },
            timeout: 10000
          }
        );
      });
    });
  });

  describe('Success State', () => {
    test('shows success message after successful verification', async () => {
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'success@example.com' } 
      });
      
      renderWithRouter('token=valid-token');
      
      await waitFor(() => {
        expect(screen.getByText('Email Verified Successfully!')).toBeInTheDocument();
        expect(screen.getByText(/Thank you for subscribing to Daily Scribe/)).toBeInTheDocument();
        expect(screen.getByText('Verified Email: success@example.com')).toBeInTheDocument();
      });
    });

    test('shows success elements and actions', async () => {
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=valid-token');
      
      await waitFor(() => {
        expect(screen.getByText('Email Verified Successfully!')).toBeInTheDocument();
      });
      
      // Check success elements
      expect(screen.getByText("What's Next?")).toBeInTheDocument();
      expect(screen.getByText(/You'll receive our daily digest/)).toBeInTheDocument();
      expect(screen.getByText('Browse Articles')).toBeInTheDocument();
      expect(screen.getByText('Contact Support')).toBeInTheDocument();
    });

    test('browse articles button is clickable', async () => {
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=valid-token');
      
      await waitFor(() => {
        expect(screen.getByText('Browse Articles')).toBeInTheDocument();
      });
      
      const browseButton = screen.getByText('Browse Articles');
      expect(browseButton).not.toBeDisabled();
      await userEvent.click(browseButton);
      // Note: Navigation testing would require more complex router mocking
    });
  });

  describe('Error States', () => {
    test('shows error when no token provided', async () => {
      renderWithRouter(''); // No token
      
      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
        expect(screen.getByText('No verification token provided. Please check your email link.')).toBeInTheDocument();
      });
    });

    test('handles 400 error (invalid token)', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 400,
          data: { detail: 'Invalid verification token.' }
        }
      });
      
      renderWithRouter('token=invalid-token');
      
      await waitFor(() => {
        expect(screen.getByText('Verification Failed')).toBeInTheDocument();
        expect(screen.getByText('Invalid verification token.')).toBeInTheDocument();
      });
    });

    test('handles 404 error (token not found)', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 404,
          data: { detail: 'Token not found' }
        }
      });
      
      renderWithRouter('token=not-found-token');
      
      await waitFor(() => {
        expect(screen.getByText('Verification token not found or has expired.')).toBeInTheDocument();
      });
    });

    test('handles 410 error (expired token)', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 410,
          data: { detail: 'Token expired' }
        }
      });
      
      renderWithRouter('token=expired-token');
      
      await waitFor(() => {
        expect(screen.getByText('This verification link has expired. Please subscribe again.')).toBeInTheDocument();
      });
    });

    test('handles 500 error (server error)', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      });
      
      renderWithRouter('token=server-error-token');
      
      await waitFor(() => {
        expect(screen.getByText('Server error. Please try again later.')).toBeInTheDocument();
      });
    });

    test('handles network error', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        request: {},
        message: 'Network Error'
      });
      
      renderWithRouter('token=network-error-token');
      
      await waitFor(() => {
        expect(screen.getByText('Network error. Please check your connection and try again.')).toBeInTheDocument();
      });
    });

    test('shows error help information', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        response: {
          status: 400,
          data: { detail: 'Invalid token' }
        }
      });
      
      renderWithRouter('token=error-token');
      
      await waitFor(() => {
        expect(screen.getByText('Common Issues:')).toBeInTheDocument();
        expect(screen.getByText(/Expired Link.*expire after 24 hours/)).toBeInTheDocument();
        expect(screen.getByText(/Already Verified.*already confirmed/)).toBeInTheDocument();
        expect(screen.getByText(/Broken Link.*may have been corrupted/)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation Actions', () => {
    test('subscribe again button navigates correctly', async () => {
      mockSearchParams = 'token=error-token';
      mockedAxios.get.mockRejectedValueOnce({
        response: { status: 400, data: { detail: 'Invalid token' } }
      });
      
      renderWithRouter('token=error-token');
      
      await waitFor(() => {
        expect(screen.getByText('Subscribe Again')).toBeInTheDocument();
      });
      
      const subscribeButton = screen.getByText('Subscribe Again');
      await userEvent.click(subscribeButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/#subscribe');
    });

    test('retry verification button works', async () => {
      mockSearchParams = 'token=retry-token';
      
      // First call fails
      mockedAxios.get.mockRejectedValueOnce({
        response: { status: 400, data: { detail: 'Invalid token' } }
      });
      
      renderWithRouter('token=retry-token');
      
      await waitFor(() => {
        expect(screen.getByText('Retry Verification')).toBeInTheDocument();
      });
      
      // Second call succeeds
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'retry@example.com' } 
      });
      
      const retryButton = screen.getByText('Retry Verification');
      await userEvent.click(retryButton);
      
      // Should show loading state again
      expect(screen.getByText('Verifying Your Email')).toBeInTheDocument();
      
      // Should make another API call
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });

    test('go to home button works from error state', async () => {
      mockSearchParams = 'token=error-token';
      mockedAxios.get.mockRejectedValueOnce({
        response: { status: 400, data: { detail: 'Invalid token' } }
      });
      
      renderWithRouter('token=error-token');
      
      await waitFor(() => {
        expect(screen.getByText('Go to Home')).toBeInTheDocument();
      });
      
      const homeButton = screen.getByText('Go to Home');
      await userEvent.click(homeButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  describe('Footer Navigation', () => {
    test('footer back to daily scribe button works', async () => {
      mockSearchParams = 'token=valid-token';
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=valid-token');
      
      await waitFor(() => {
        expect(screen.getByText('Back to Daily Scribe')).toBeInTheDocument();
      });
      
      const backButton = screen.getByText('Back to Daily Scribe');
      await userEvent.click(backButton);
      
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });

    test('footer contains support information', async () => {
      renderWithRouter('token=test');
      
      await waitFor(() => {
        expect(screen.getByText(/Having trouble/)).toBeInTheDocument();
        expect(screen.getByText('Contact our support team')).toBeInTheDocument();
        expect(screen.getByText('Privacy Policy')).toBeInTheDocument();
        expect(screen.getByText('Terms of Service')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper heading structure', async () => {
      mockSearchParams = 'token=valid-token';
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=valid-token');
      
      await waitFor(() => {
        const heading = screen.getByRole('heading', { level: 1 });
        expect(heading).toHaveTextContent('Email Verified Successfully!');
      });
    });

    test('buttons have appropriate roles and are focusable', async () => {
      mockSearchParams = 'token=valid-token';
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=valid-token');
      
      await waitFor(() => {
        const browseButton = screen.getByRole('button', { name: 'Browse Articles' });
        expect(browseButton).toBeInTheDocument();
        expect(browseButton).not.toBeDisabled();
      });
    });

    test('error messages are properly announced', async () => {
      mockSearchParams = 'token=error-token';
      mockedAxios.get.mockRejectedValueOnce({
        response: { status: 400, data: { detail: 'Invalid token' } }
      });
      
      renderWithRouter('token=error-token');
      
      await waitFor(() => {
        const errorMessage = screen.getByText('Invalid token');
        expect(errorMessage).toBeInTheDocument();
        // Error message should be in an element that's accessible
        expect(errorMessage.closest('.error-message')).toBeInTheDocument();
      });
    });
  });

  describe('API Configuration', () => {
    test('uses environment variable for API URL', async () => {
      process.env.REACT_APP_API_URL = 'https://api.example.com';
      mockSearchParams = 'token=env-test-token';
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=env-test-token');
      
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          'https://api.example.com/api/verify-email',
          expect.any(Object)
        );
      });
    });

    test('falls back to localhost when no environment variable', async () => {
      delete process.env.REACT_APP_API_URL;
      mockSearchParams = 'token=localhost-test-token';
      mockedAxios.get.mockResolvedValueOnce({ 
        status: 200, 
        data: { email: 'test@example.com' } 
      });
      
      renderWithRouter('token=localhost-test-token');
      
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          'http://localhost:8000/api/verify-email',
          expect.any(Object)
        );
      });
    });
  });
});
