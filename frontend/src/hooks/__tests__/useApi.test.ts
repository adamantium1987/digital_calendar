import { renderHook, waitFor } from '@testing-library/react';
import { useApiGet, useApiPost, useApiPolling } from '../useApi';
import * as api from '../../utils/api';

jest.mock('../../utils/api');

describe('useApiGet', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches data successfully on mount', async () => {
    const mockData = { id: 1, name: 'Test' };
    (api.get as jest.Mock).mockResolvedValue(mockData);

    const { result } = renderHook(() => useApiGet('/test-endpoint'));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(api.get).toHaveBeenCalledWith('/test-endpoint', undefined);
  });

  it('handles errors correctly', async () => {
    const mockError = new Error('API Error');
    (api.get as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useApiGet('/test-endpoint'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe(mockError);
  });

  it('does not fetch when skip option is true', async () => {
    const { result } = renderHook(() =>
      useApiGet('/test-endpoint', { skip: true })
    );

    expect(result.current.loading).toBe(false);
    expect(api.get).not.toHaveBeenCalled();
  });

  it('refetches data when refetch is called', async () => {
    const mockData1 = { id: 1, name: 'First' };
    const mockData2 = { id: 2, name: 'Second' };
    (api.get as jest.Mock)
      .mockResolvedValueOnce(mockData1)
      .mockResolvedValueOnce(mockData2);

    const { result } = renderHook(() => useApiGet('/test-endpoint'));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData1);
    });

    await result.current.refetch();

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData2);
    });

    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it('refetches when dependencies change', async () => {
    const mockData1 = { id: 1, name: 'First' };
    const mockData2 = { id: 2, name: 'Second' };
    (api.get as jest.Mock)
      .mockResolvedValueOnce(mockData1)
      .mockResolvedValueOnce(mockData2);

    let dep = 'value1';
    const { rerender } = renderHook(() =>
      useApiGet('/test-endpoint', { dependencies: [dep] })
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(1);
    });

    dep = 'value2';
    rerender();

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });
  });
});

describe('useApiPost', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('posts data successfully', async () => {
    const mockResponse = { success: true, id: 1 };
    (api.post as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApiPost('/test-endpoint'));

    expect(result.current.loading).toBe(false);

    const postData = { name: 'Test' };
    const response = await result.current.execute(postData);

    expect(response).toEqual(mockResponse);
    expect(result.current.data).toEqual(mockResponse);
    expect(result.current.error).toBeNull();
    expect(api.post).toHaveBeenCalledWith('/test-endpoint', postData, undefined);
  });

  it('handles post errors correctly', async () => {
    const mockError = new Error('Post failed');
    (api.post as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() => useApiPost('/test-endpoint'));

    await expect(result.current.execute({ data: 'test' })).rejects.toThrow(
      'Post failed'
    );

    await waitFor(() => {
      expect(result.current.error).toBe(mockError);
    });
  });

  it('calls onSuccess callback when post succeeds', async () => {
    const mockResponse = { success: true };
    const onSuccess = jest.fn();
    (api.post as jest.Mock).mockResolvedValue(mockResponse);

    const { result } = renderHook(() =>
      useApiPost('/test-endpoint', { onSuccess })
    );

    await result.current.execute({ data: 'test' });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it('calls onError callback when post fails', async () => {
    const mockError = new Error('Post failed');
    const onError = jest.fn();
    (api.post as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(() =>
      useApiPost('/test-endpoint', { onError })
    );

    await expect(result.current.execute({ data: 'test' })).rejects.toThrow();

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });
});

describe('useApiPolling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('polls endpoint at specified interval', async () => {
    const mockData = { id: 1, status: 'active' };
    (api.get as jest.Mock).mockResolvedValue(mockData);

    renderHook(() => useApiPolling('/test-endpoint', { interval: 5000 }));

    // Initial fetch
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(1);
    });

    // Advance time by 5 seconds
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });

    // Advance time by another 5 seconds
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(3);
    });
  });

  it('stops polling when enabled is false', async () => {
    const mockData = { id: 1 };
    (api.get as jest.Mock).mockResolvedValue(mockData);

    const { rerender } = renderHook(
      ({ enabled }) => useApiPolling('/test-endpoint', { interval: 5000, enabled }),
      { initialProps: { enabled: true } }
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(1);
    });

    // Disable polling
    rerender({ enabled: false });

    jest.advanceTimersByTime(10000);

    // Should not have made additional calls
    expect(api.get).toHaveBeenCalledTimes(1);
  });

  it('cleans up polling on unmount', async () => {
    const mockData = { id: 1 };
    (api.get as jest.Mock).mockResolvedValue(mockData);

    const { unmount } = renderHook(() =>
      useApiPolling('/test-endpoint', { interval: 5000 })
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(1);
    });

    unmount();

    jest.advanceTimersByTime(10000);

    // Should not have made additional calls after unmount
    expect(api.get).toHaveBeenCalledTimes(1);
  });
});
