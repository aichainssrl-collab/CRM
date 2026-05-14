import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDashboardMetrics } from '@/hooks/useDashboard';
import { apiFetch } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('useDashboard hooks', () => {
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

  it('useDashboardMetrics fetches metrics', async () => {
    const mockMetrics = { totalLeads: 100, pipelineValue: 50000 };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockMetrics);

    const { result } = renderHook(() => useDashboardMetrics('30d'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockMetrics);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/dashboard/metrics?timeRange=30d');
  });
});
