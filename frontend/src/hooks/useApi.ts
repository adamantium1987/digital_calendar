import { useState, useEffect, useCallback } from 'react';
import { api } from '@/utils/api';
import { ApiException } from '@/types/api';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiException | null;
}

interface UseApiOptions {
  immediate?: boolean;
  onSuccess?: (data: unknown) => void;
  onError?: (error: ApiException) => void;
}

/**
 * Custom hook for API GET requests with loading and error states
 */
export function useApiGet<T>(
  endpoint: string,
  options: UseApiOptions = {}
): UseApiState<T> & { refetch: () => Promise<void> } {
  const { immediate = true, onSuccess, onError } = options;
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  const fetchData = useCallback(async (): Promise<void> => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await api.get<T>(endpoint);
      setState({ data: result, loading: false, error: null });
      if (onSuccess) onSuccess(result);
    } catch (error) {
      const apiError = error instanceof ApiException ? error : new ApiException(500, 'Unknown error');
      setState({ data: null, loading: false, error: apiError });
      if (onError) onError(apiError);
    }
  }, [endpoint, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      void fetchData();
    }
  }, [immediate, fetchData]);

  return {
    ...state,
    refetch: fetchData,
  };
}

/**
 * Custom hook for API POST requests
 */
export function useApiPost<TRequest, TResponse>(): {
  mutate: (endpoint: string, data: TRequest) => Promise<TResponse | null>;
  loading: boolean;
  error: ApiException | null;
  data: TResponse | null;
} {
  const [state, setState] = useState<UseApiState<TResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const mutate = useCallback(async (endpoint: string, data: TRequest): Promise<TResponse | null> => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await api.post<TResponse>(endpoint, data);
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const apiError = error instanceof ApiException ? error : new ApiException(500, 'Unknown error');
      setState({ data: null, loading: false, error: apiError });
      return null;
    }
  }, []);

  return {
    mutate,
    ...state,
  };
}

/**
 * Custom hook for polling API endpoints at intervals
 */
export function useApiPolling<T>(
  endpoint: string,
  intervalMs: number = 30000,
  options: UseApiOptions = {}
): UseApiState<T> & { refetch: () => Promise<void>; stop: () => void; start: () => void } {
  const { immediate = true, onSuccess, onError } = options;
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });
  const [isPolling, setIsPolling] = useState(immediate);

  const fetchData = useCallback(async (): Promise<void> => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await api.get<T>(endpoint);
      setState({ data: result, loading: false, error: null });
      if (onSuccess) onSuccess(result);
    } catch (error) {
      const apiError = error instanceof ApiException ? error : new ApiException(500, 'Unknown error');
      setState({ data: null, loading: false, error: apiError });
      if (onError) onError(apiError);
    }
  }, [endpoint, onSuccess, onError]);

  useEffect(() => {
    if (!isPolling) return;

    void fetchData();
    const interval = setInterval(() => {
      void fetchData();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [isPolling, fetchData, intervalMs]);

  return {
    ...state,
    refetch: fetchData,
    stop: () => setIsPolling(false),
    start: () => setIsPolling(true),
  };
}
