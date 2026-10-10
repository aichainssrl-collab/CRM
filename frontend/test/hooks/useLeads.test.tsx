import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useLeads, useLead, useCreateLead, useUpdateLead, useDeleteLead } from '@/hooks/useLeads';
import { apiFetch } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('useLeads hooks', () => {
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

  it('useLeads fetches leads list', async () => {
    const mockLeads = [{ id: '1', email: 'test@example.com', pipelineStage: 'new', leadScore: 50 }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockLeads);

    const { result } = renderHook(() => useLeads(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockLeads);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads?limit=100');
  });

  it('useLead fetches single lead', async () => {
    const mockLead = { id: '1', email: 'test@example.com', pipelineStage: 'new', leadScore: 50 };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockLead);

    const { result } = renderHook(() => useLead('1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockLead);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/1');
  });

  it('useCreateLead creates lead and invalidates', async () => {
    const mockLead = { id: '2', email: 'new@example.com' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockLead);

    const { result } = renderHook(() => useCreateLead(), { wrapper });

    result.current.mutate({ email: 'new@example.com' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads', {
      method: 'POST',
      body: JSON.stringify({ email: 'new@example.com' }),
    });
  });

  it('useUpdateLead updates lead and invalidates', async () => {
    const mockLead = { id: '1', email: 'test@example.com', pipelineStage: 'contacted' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockLead);

    const { result } = renderHook(() => useUpdateLead(), { wrapper });

    result.current.mutate({ id: '1', data: { pipelineStage: 'contacted' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/1', {
      method: 'PATCH',
      body: JSON.stringify({ pipelineStage: 'contacted' }),
    });
  });

  it('useDeleteLead deletes lead and invalidates', async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({ success: true });

    const { result } = renderHook(() => useDeleteLead(), { wrapper });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/1', {
      method: 'DELETE',
    });
  });
});
