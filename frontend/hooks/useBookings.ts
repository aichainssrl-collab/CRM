import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface BookingSlot {
  id: string;
  startTime: string;
  endTime: string;
  isAvailable: boolean;
}

export interface Booking {
  id: string;
  leadId: string;
  slotId: string;
  startTime: string;
  endTime: string;
  status: string;
  notes?: string;
  meetingLink?: string;
}

export function useBookingSlots(dateStr?: string) {
  return useQuery({
    queryKey: ["booking-slots", dateStr],
    queryFn: async () => {
      const qs = dateStr ? `?date=${dateStr}` : "";
      return apiFetch(`/api/v1/booking-slots${qs}`) as Promise<BookingSlot[]>;
    },
  });
}

export function useBookings(leadId?: string) {
  return useQuery({
    queryKey: leadId ? ["bookings", "lead", leadId] : ["bookings"],
    queryFn: async () => {
      const endpoint = leadId ? `/api/v1/leads/${leadId}/bookings` : `/api/v1/bookings`;
      return apiFetch(endpoint) as Promise<Booking[]>;
    },
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Booking>) => {
      return apiFetch("/api/v1/bookings", {
        method: "POST",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["booking-slots"] });
    },
  });
}

export function useUpdateBooking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Booking> }) => {
      return apiFetch(`/api/v1/bookings/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      queryClient.invalidateQueries({ queryKey: ["booking-slots"] });
    },
  });
}
