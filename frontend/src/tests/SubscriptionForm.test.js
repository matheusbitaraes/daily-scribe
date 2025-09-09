import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import SubscriptionForm from '../components/SubscriptionForm';

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

describe('SubscriptionForm', () => {
  describe('Rendering', () => {
    test('renders subscription form with all elements', () => {
      render(<SubscriptionForm />);
      
      expect(screen.getByText('Stay Updated')).toBeInTheDocument();
      expect(screen.getByText(/Get the latest insights/)).toBeInTheDocument();
      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Enter your email address')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /subscribe/i })).toBeInTheDocument();
      expect(screen.getByText(/We respect your privacy/)).toBeInTheDocument();
    });

    test('renders with custom className', () => {
      const { container } = render(<SubscriptionForm className="custom-class" />);
      expect(container.firstChild).toHaveClass('subscription-form', 'custom-class');
    });

    test('renders with different variants', () => {
      const { container, rerender } = render(<SubscriptionForm variant="compact" />);
      expect(container.firstChild).toHaveClass('subscription-form', 'compact');
      
      rerender(<SubscriptionForm variant="inline" />);
      expect(container.firstChild).toHaveClass('subscription-form', 'inline');
    });
  });

  describe('Form Validation', () => {
    test('displays error for empty email', async () => {
      render(<SubscriptionForm />);
      
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Email address is required')).toBeInTheDocument();
      });
    });

    test('displays error for invalid email format', async () => {
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      await userEvent.type(emailInput, 'invalid-email');
      await userEvent.tab(); // Trigger validation
      
      await waitFor(() => {
        expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
      });
    });

    test('displays error for email that is too long', async () => {
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const longEmail = 'a'.repeat(250) + '@example.com'; // Over 254 characters
      await userEvent.type(emailInput, longEmail);
      await userEvent.tab();
      
      await waitFor(() => {
        expect(screen.getByText('Email address is too long')).toBeInTheDocument();
      });
    });

    test('accepts valid email addresses', async () => {
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      await userEvent.type(emailInput, 'valid@example.com');
      await userEvent.tab();
      
      await waitFor(() => {
        expect(screen.queryByText(/Please enter a valid email address/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Email address is required/)).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    test('submits form with valid email successfully', async () => {
      const mockResponse = { status: 200, data: { message: 'Subscription successful' } };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      const onSuccess = jest.fn();
      render(<SubscriptionForm onSuccess={onSuccess} />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/subscribe',
        { email: 'test@example.com' },
        {
          headers: { 'Content-Type': 'application/json' },
          timeout: 10000
        }
      );
      
      await waitFor(() => {
        expect(screen.getByText('Check Your Email!')).toBeInTheDocument();
        expect(screen.getByText(/We've sent a verification link/)).toBeInTheDocument();
      });
      
      expect(onSuccess).toHaveBeenCalledWith('test@example.com', mockResponse.data);
    });

    test('shows loading state during submission', async () => {
      let resolvePromise;
      const mockPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockedAxios.post.mockReturnValueOnce(mockPromise);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      expect(screen.getByText('Subscribing...')).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
      expect(emailInput).toBeDisabled();
      
      // Resolve the promise
      resolvePromise({ status: 200, data: {} });
    });

    test('handles 400 error (invalid email)', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: 'Invalid email address format.' }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(mockError);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Error:.*Invalid email address format/)).toBeInTheDocument();
      });
    });

    test('handles 409 error (already subscribed)', async () => {
      const mockError = {
        response: {
          status: 409,
          data: { detail: 'Email already subscribed' }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(mockError);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/This email is already subscribed/)).toBeInTheDocument();
      });
    });

    test('handles 500 error (server error)', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(mockError);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Server error.*try again later/)).toBeInTheDocument();
      });
    });

    test('handles network error', async () => {
      const mockError = {
        request: {},
        message: 'Network Error'
      };
      mockedAxios.post.mockRejectedValueOnce(mockError);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Network error.*check your connection/)).toBeInTheDocument();
      });
    });
  });

  describe('Success State', () => {
    test('shows success message and reset button after successful submission', async () => {
      const mockResponse = { status: 200, data: { message: 'Success' } };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Check Your Email!')).toBeInTheDocument();
        expect(screen.getByText(/We've sent a verification link/)).toBeInTheDocument();
        expect(screen.getByText('Subscribe Another Email')).toBeInTheDocument();
      });
      
      // Form should be hidden
      expect(screen.queryByLabelText('Email Address')).not.toBeInTheDocument();
    });

    test('resets form when clicking "Subscribe Another Email"', async () => {
      const mockResponse = { status: 200, data: { message: 'Success' } };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Subscribe Another Email')).toBeInTheDocument();
      });
      
      const resetButton = screen.getByText('Subscribe Another Email');
      await userEvent.click(resetButton);
      
      await waitFor(() => {
        expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /subscribe/i })).toBeInTheDocument();
        expect(screen.queryByText('Check Your Email!')).not.toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe to newsletter/i });
      
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('autoComplete', 'email');
      expect(submitButton).toHaveAttribute('type', 'submit');
    });

    test('associates error messages with inputs', async () => {
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        const errorMessage = screen.getByText('Email address is required');
        expect(errorMessage).toHaveAttribute('role', 'alert');
        expect(emailInput).toHaveAttribute('aria-describedby', 'email-error');
      });
    });

    test('error messages have alert role', async () => {
      const mockError = {
        response: {
          status: 400,
          data: { detail: 'Invalid email' }
        }
      };
      mockedAxios.post.mockRejectedValueOnce(mockError);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      await waitFor(() => {
        const errorAlert = screen.getByRole('alert');
        expect(errorAlert).toHaveTextContent('Invalid email');
      });
    });
  });

  describe('API Configuration', () => {
    test('uses environment variable for API URL', async () => {
      process.env.REACT_APP_API_URL = 'https://api.example.com';
      const mockResponse = { status: 200, data: {} };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'https://api.example.com/api/subscribe',
        expect.any(Object),
        expect.any(Object)
      );
    });

    test('falls back to localhost when no environment variable', async () => {
      delete process.env.REACT_APP_API_URL;
      const mockResponse = { status: 200, data: {} };
      mockedAxios.post.mockResolvedValueOnce(mockResponse);
      
      render(<SubscriptionForm />);
      
      const emailInput = screen.getByLabelText('Email Address');
      const submitButton = screen.getByRole('button', { name: /subscribe/i });
      
      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.click(submitButton);
      
      expect(mockedAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/subscribe',
        expect.any(Object),
        expect.any(Object)
      );
    });
  });
});
