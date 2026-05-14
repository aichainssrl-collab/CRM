"use client";

import { Calendar } from "@/components/ui/calendar";

interface BookingCalendarProps {
  date: Date | undefined;
  setDate: (date: Date | undefined) => void;
}

export function BookingCalendar({ date, setDate }: BookingCalendarProps) {
  return (
    <div className="border rounded-md p-2 bg-card">
      <Calendar
        mode="single"
        selected={date}
        onSelect={setDate}
        className="rounded-md"
        disabled={(date) => date < new Date() || date.getDay() === 0 || date.getDay() === 6}
      />
    </div>
  );
}
