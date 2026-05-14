import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDeals, useCreateDeal, useUpdateDeal, useDeleteDeal } from '@/hooks/useDeals';
import { apiFetch } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('useDeals hooks', () => {
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

  it('useDeals fetches deals list', async () => {
    const mockDeals = [{ id: '1', title: 'deal 1' }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockDeals);

    const { result } = renderHook(() => useDeals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockDeals);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/deals');
  });

  it('useCreateDeal creates deal and invalidates', async () => {
    const mockDeal = { id: '2', title: 'new deal' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockDeal);

    const { result } = renderHook(() => useCreateDeal(), { wrapper });

    result.current.mutate({ lead_id: 'lead1', title: 'new deal' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/deals?lead_id=lead1', {
      method: 'POST',
      body: JSON.stringify({ title: 'new deal' }),
    });
  });

  it('useUpdateDeal updates deal and invalidates', async () => {
    const mockDeal = { id: '1', title: 'updated deal' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockDeal);

    const { result } = renderHook(() => useUpdateDeal(), { wrapper });

    result.current.mutate({ id: '1', data: { title: 'updated deal' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/deals/1', {
      method: 'PATCH',
      body: JSON.stringify({ title: 'updated deal' }),
    });
  });

  it('useDeleteDeal deletes deal and invalidates', async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({ success: true });

    const { result } = renderHook(() => useDeleteDeal(), { wrapper });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/deals/1', {
      method: 'DELETE',
    });
  });
});
