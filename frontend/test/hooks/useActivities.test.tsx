import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useActivities, useCreateActivity } from '@/hooks/useActivities';
import { apiFetch } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('useActivities hooks', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('useActivities fetches activities list', async () => {
    const mockActivities = [{ id: '1', type: 'note', title: 'test note' }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockActivities);

    const { result } = renderHook(() => useActivities('lead1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockActivities);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/lead1/activities');
  });

  it('useCreateActivity creates activity and invalidates', async () => {
    const mockActivity = { id: '2', type: 'note' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockActivity);

    const { result } = renderHook(() => useCreateActivity('lead1'), { wrapper });

    result.current.mutate({ type: 'note' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/lead1/activities', {
      method: 'POST',
      body: JSON.stringify({ type: 'note' }),
    });
  });
});
