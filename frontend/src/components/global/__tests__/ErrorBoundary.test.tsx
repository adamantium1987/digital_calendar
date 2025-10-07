import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ErrorBoundary, APIErrorBoundary } from '../ErrorBoundary';

// Component that throws an error
const ThrowError = ({ error }: { error: Error }) => {
  throw error;
};

// Component that renders successfully
const SuccessComponent = () => <div>Success!</div>;

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Suppress console.error for cleaner test output
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <SuccessComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Success!')).toBeInTheDocument();
  });

  it('renders error UI when child component throws', () => {
    const error = new Error('Test error');
    render(
      <ErrorBoundary>
        <ThrowError error={error} />
      </ErrorBoundary>
    );
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('displays custom fallback when provided', () => {
    const error = new Error('Test error');
    const customFallback = <div>Custom Error Message</div>;

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError error={error} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom Error Message')).toBeInTheDocument();
  });

  it('calls onError callback when error occurs', () => {
    const error = new Error('Test error');
    const onError = jest.fn();

    render(
      <ErrorBoundary onError={onError}>
        <ThrowError error={error} />
      </ErrorBoundary>
    );

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError).toHaveBeenCalledWith(
      error,
      expect.objectContaining({ componentStack: expect.any(String) })
    );
  });

  it('resets error state when reset button is clicked', () => {
    const error = new Error('Test error');
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError error={error} />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();

    const resetButton = screen.getByText(/Try again/i);
    resetButton.click();

    // After reset, re-render with success component
    rerender(
      <ErrorBoundary>
        <SuccessComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText('Success!')).toBeInTheDocument();
  });
});

describe('APIErrorBoundary', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders children when there is no error', () => {
    render(
      <APIErrorBoundary>
        <SuccessComponent />
      </APIErrorBoundary>
    );
    expect(screen.getByText('Success!')).toBeInTheDocument();
  });

  it('displays API-specific error message', () => {
    const error = new Error('Network error');
    render(
      <APIErrorBoundary>
        <ThrowError error={error} />
      </APIErrorBoundary>
    );
    expect(screen.getByText(/Unable to load data/i)).toBeInTheDocument();
    expect(screen.getByText(/Network error/i)).toBeInTheDocument();
  });

  it('shows retry button for API errors', () => {
    const error = new Error('API error');
    render(
      <APIErrorBoundary>
        <ThrowError error={error} />
      </APIErrorBoundary>
    );
    expect(screen.getByText(/Retry/i)).toBeInTheDocument();
  });

  it('calls onRetry callback when retry button is clicked', () => {
    const error = new Error('API error');
    const onRetry = jest.fn();

    render(
      <APIErrorBoundary onRetry={onRetry}>
        <ThrowError error={error} />
      </APIErrorBoundary>
    );

    const retryButton = screen.getByText(/Retry/i);
    retryButton.click();

    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
