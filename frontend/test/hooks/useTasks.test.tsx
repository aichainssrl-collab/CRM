import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useTasks, useCreateTask, useUpdateTask, useDeleteTask } from '@/hooks/useTasks';
import { apiFetch } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('useTasks hooks', () => {
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

  it('useTasks fetches global task list when no leadId is provided', async () => {
    const mockTasks = [{ id: '1', title: 'global task' }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockTasks);

    const { result } = renderHook(() => useTasks(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockTasks);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/tasks');
  });

  it('useTasks fetches tasks list for lead', async () => {
    const mockTasks = [{ id: '1', title: 'task 1' }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockTasks);

    const { result } = renderHook(() => useTasks('lead1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockTasks);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/lead1/tasks');
  });

  it('useCreateTask creates task and invalidates', async () => {
    const mockTask = { id: '2', title: 'new task' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockTask);

    const { result } = renderHook(() => useCreateTask('lead1'), { wrapper });

    result.current.mutate({ title: 'new task' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/lead1/tasks', {
      method: 'POST',
      body: JSON.stringify({ title: 'new task' }),
    });
  });

  it('useUpdateTask updates task and invalidates', async () => {
    const mockTask = { id: '1', title: 'updated task' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockTask);

    const { result } = renderHook(() => useUpdateTask('lead1'), { wrapper });

    result.current.mutate({ id: '1', data: { title: 'updated task' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/lead1/tasks/1', {
      method: 'PATCH',
      body: JSON.stringify({ title: 'updated task' }),
    });
  });

  it('useDeleteTask deletes task and invalidates', async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({ success: true });

    const { result } = renderHook(() => useDeleteTask('lead1'), { wrapper });

    result.current.mutate('1');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/leads/lead1/tasks/1', {
      method: 'DELETE',
    });
  });
});
