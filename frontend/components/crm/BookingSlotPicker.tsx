"use client";

import { useState } from "react";
import { useBookingSlots, useCreateBooking } from "@/hooks/useBookings";
import { BookingCalendar } from "@/components/crm/BookingCalendar";
import { Button } from "@/components/ui/button";
import { Clock } from "lucide-react";

export function BookingSlotPicker({ leadId }: { leadId?: string }) {
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  
  const dateStr = date ? date.toISOString().split("T")[0] : undefined;
  const { data: slots, isLoading } = useBookingSlots(dateStr);
  const { mutateAsync: createBooking, isPending } = useCreateBooking();

  const handleBook = async () => {
    if (!selectedSlot || !leadId) return;
    try {
      await createBooking({ slotId: selectedSlot, leadId, status: "confirmed" });
      setSelectedSlot(null);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 className="text-sm font-medium mb-4">Select Date</h3>
        <BookingCalendar date={date} setDate={setDate} />
      </div>
      <div>
        <h3 className="text-sm font-medium mb-4">Available Times</h3>
        {isLoading ? (
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map(i => <div key={i} className="h-10 bg-muted rounded-md" />)}
          </div>
        ) : !slots?.length ? (
          <div className="text-sm text-muted-foreground p-4 border border-dashed rounded-md text-center">
            No slots available for this date.
          </div>
        ) : (
          <div className="space-y-2">
            {slots.map(slot => (
              <button
                key={slot.id}
                onClick={() => setSelectedSlot(slot.id)}
                disabled={!slot.isAvailable}
                className={`w-full flex items-center justify-between p-3 rounded-md border text-sm transition-colors ${
                  !slot.isAvailable 
                    ? "opacity-50 cursor-not-allowed bg-muted/50" 
                    : selectedSlot === slot.id
                      ? "border-primary bg-primary/5 text-primary"
                      : "hover:border-primary/50"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  {new Date(slot.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
                {!slot.isAvailable && <span className="text-xs">Booked</span>}
              </button>
            ))}
          </div>
        )}
        
        {selectedSlot && (
          <Button 
            className="w-full mt-6" 
            onClick={handleBook}
            disabled={isPending || !leadId}
          >
            {isPending ? "Confirming..." : "Confirm Booking"}
          </Button>
        )}
      </div>
    </div>
  );
}
