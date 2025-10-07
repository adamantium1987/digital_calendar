import { ApiException, RequestConfig } from '../types/api';

const API_BASE = process.env.REACT_APP_API_BASE || '/api';
const DEFAULT_TIMEOUT = 30000;
const DEFAULT_RETRIES = 3;
const DEFAULT_RETRY_DELAY = 1000;

/**
 * Sleep utility for retry delays
 */
const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Fetch with timeout support
 */
const fetchWithTimeout = async (
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
};

/**
 * Fetch with retry logic
 */
const fetchWithRetry = async (
  url: string,
  options: RequestInit,
  config: RequestConfig
): Promise<Response> => {
  const { timeout = DEFAULT_TIMEOUT, retries = DEFAULT_RETRIES, retryDelay = DEFAULT_RETRY_DELAY } = config;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, options, timeout);

      // Don't retry on client errors (4xx), only server errors (5xx) and network issues
      if (response.ok || (response.status >= 400 && response.status < 500)) {
        return response;
      }

      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      lastError = error as Error;

      // Don't retry on abort (timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiException(408, 'Request timeout');
      }
    }

    // Wait before retrying (exponential backoff)
    if (attempt < retries) {
      await sleep(retryDelay * Math.pow(2, attempt));
    }
  }

  throw lastError || new ApiException(500, 'Request failed after retries');
};

/**
 * Handle API response and errors
 */
const handleResponse = async <T>(response: Response): Promise<T> => {
  if (!response.ok) {
    let errorMessage = `API error: ${response.status}`;
    let errorDetails: Record<string, unknown> | undefined;

    try {
      const errorData = await response.json();
      errorMessage = errorData.message || errorData.error || errorMessage;
      errorDetails = errorData;
    } catch {
      // Failed to parse error response
    }

    throw new ApiException(response.status, errorMessage, errorDetails);
  }

  try {
    return await response.json();
  } catch (error) {
    throw new ApiException(500, 'Failed to parse response JSON');
  }
};

export const api = {
  /**
   * Perform GET request
   */
  async get<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetchWithRetry(url, { method: 'GET' }, config);
    return handleResponse<T>(response);
  },

  /**
   * Perform POST request with JSON body
   */
  async post<T>(endpoint: string, data: unknown = {}, config: RequestConfig = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetchWithRetry(
      url,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      },
      config
    );
    return handleResponse<T>(response);
  },

  /**
   * Perform PUT request with JSON body
   */
  async put<T>(endpoint: string, data: unknown = {}, config: RequestConfig = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetchWithRetry(
      url,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      },
      config
    );
    return handleResponse<T>(response);
  },

  /**
   * Perform DELETE request
   */
  async delete<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const response = await fetchWithRetry(url, { method: 'DELETE' }, config);
    return handleResponse<T>(response);
  },

  /**
   * Submit form data (URL encoded)
   */
  async submitForm(endpoint: string, data: Record<string, string>): Promise<Response> {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(data),
    });
    return response;
  },

  /**
   * Delete account (legacy method - should use api.delete)
   */
  async deleteAccount(accountId: string): Promise<boolean> {
    try {
      await this.post(`/accounts/${accountId}/remove`, {});
      return true;
    } catch {
      return false;
    }
  },
};