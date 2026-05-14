import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useBookingSlots, useBookings, useCreateBooking, useUpdateBooking } from '@/hooks/useBookings';
import { apiFetch } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('useBookings hooks', () => {
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

  it('useBookingSlots fetches slots list', async () => {
    const mockSlots = [{ id: '1', startTime: '2023-01-01T10:00:00Z' }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockSlots);

    const { result } = renderHook(() => useBookingSlots('2023-01-01'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockSlots);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/booking-slots?date=2023-01-01');
  });

  it('useBookings fetches bookings list', async () => {
    const mockBookings = [{ id: '1', status: 'confirmed' }];
    vi.mocked(apiFetch).mockResolvedValueOnce(mockBookings);

    const { result } = renderHook(() => useBookings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockBookings);
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/bookings');
  });

  it('useCreateBooking creates booking and invalidates', async () => {
    const mockBooking = { id: '2', status: 'confirmed' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockBooking);

    const { result } = renderHook(() => useCreateBooking(), { wrapper });

    result.current.mutate({ status: 'confirmed' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/bookings', {
      method: 'POST',
      body: JSON.stringify({ status: 'confirmed' }),
    });
  });

  it('useUpdateBooking updates booking and invalidates', async () => {
    const mockBooking = { id: '1', status: 'cancelled' };
    vi.mocked(apiFetch).mockResolvedValueOnce(mockBooking);

    const { result } = renderHook(() => useUpdateBooking(), { wrapper });

    result.current.mutate({ id: '1', data: { status: 'cancelled' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiFetch).toHaveBeenCalledWith('/api/v1/bookings/1', {
      method: 'PATCH',
      body: JSON.stringify({ status: 'cancelled' }),
    });
  });
});
