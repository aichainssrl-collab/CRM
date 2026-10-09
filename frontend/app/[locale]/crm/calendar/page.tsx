"use client";

import { useState, useMemo } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useCalendarEvents, type CalendarEvent } from "@/hooks/useCalendar";
import {
  ChevronLeft, ChevronRight, Calendar as CalendarIcon,
  CheckSquare, Briefcase, Video,
} from "lucide-react";

const MONTHS = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
  "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"];

const TYPE_STYLES: Record<string, string> = {
  task: "bg-info/15 text-info border-info/20",
  booking: "bg-success/15 text-success border-success/20",
  deal: "bg-warning/15 text-warning border-warning/20",
};

const TYPE_ICONS: Record<string, React.ElementType> = {
  task: CheckSquare,
  booking: Video,
  deal: Briefcase,
};

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month, 0).getDate();
}

function getFirstDayOfWeek(year: number, month: number) {
  // 0 = Monday, 6 = Sunday
  return (new Date(year, month - 1, 1).getDay() + 6) % 7;
}

export default function CalendarPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState<number | null>(today.getDate());

  const { data: events = [], isLoading } = useCalendarEvents(year, month);

  // Group events by day of month
  const eventsByDay = useMemo(() => {
    const map: Record<number, CalendarEvent[]> = {};
    for (const event of events) {
      if (!event.date) continue;
      const d = new Date(event.date);
      const day = d.getDate();
      if (!map[day]) map[day] = [];
      map[day].push(event);
    }
    return map;
  }, [events]);

  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfWeek(year, month);

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(year - 1); }
    else setMonth(month - 1);
    setSelectedDay(null);
  };

  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(year + 1); }
    else setMonth(month + 1);
    setSelectedDay(null);
  };

  const selectedEvents = selectedDay ? (eventsByDay[selectedDay] || []) : [];

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Calendario</h1>
          <p className="text-sm text-muted-foreground">
            Task, demo e scadenze deal in un unico calendario
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Calendar Grid */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CalendarIcon className="h-5 w-5 text-primary" />
                  <CardTitle>{MONTHS[month - 1]} {year}</CardTitle>
                </div>
                <div className="flex gap-1">
                  <Button variant="outline" size="icon" className="h-8 w-8" onClick={prevMonth}>
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" className="h-8 w-8" onClick={nextMonth}>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[400px] w-full rounded-lg" />
              ) : (
                <>
                  {/* Day headers */}
                  <div className="grid grid-cols-7 gap-1 mb-1">
                    {["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"].map(d => (
                      <div key={d} className="text-center text-xs font-medium text-muted-foreground py-2">
                        {d}
                      </div>
                    ))}
                  </div>

                  {/* Calendar cells */}
                  <div className="grid grid-cols-7 gap-1">
                    {/* Empty cells before first day */}
                    {Array.from({ length: firstDay }).map((_, i) => (
                      <div key={`empty-${i}`} className="aspect-square rounded-md bg-muted/20" />
                    ))}

                    {/* Day cells */}
                    {Array.from({ length: daysInMonth }).map((_, i) => {
                      const day = i + 1;
                      const isToday = day === today.getDate() && month === today.getMonth() + 1 && year === today.getFullYear();
                      const isSelected = day === selectedDay;
                      const dayEvents = eventsByDay[day] || [];

                      return (
                        <button
                          key={day}
                          onClick={() => setSelectedDay(day)}
                          className={`aspect-square rounded-md border p-1 text-left transition-all hover:border-primary/50 ${
                            isSelected
                              ? "border-primary bg-primary/5"
                              : isToday
                                ? "border-primary/40 bg-primary/5"
                                : "border-border/50"
                          }`}
                        >
                          <p className={`text-xs font-medium ${isToday ? "text-primary" : ""}`}>
                            {day}
                          </p>
                          {dayEvents.length > 0 && (
                            <div className="mt-0.5 space-y-0.5">
                              {dayEvents.slice(0, 2).map((e, j) => (
                                <div
                                  key={j}
                                  className={`h-1 rounded-full ${TYPE_STYLES[e.type] || "bg-muted"}`}
                                  style={{ width: "80%" }}
                                />
                              ))}
                              {dayEvents.length > 2 && (
                                <p className="text-[8px] text-muted-foreground">+{dayEvents.length - 2}</p>
                              )}
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Legend */}
                  <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-info" /> Task
                    </span>
                    <span className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-success" /> Demo
                    </span>
                    <span className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-warning" /> Scadenze Deal
                    </span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Selected Day Detail */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {selectedDay ? `${selectedDay} ${MONTHS[month - 1]}` : "Seleziona un giorno"}
              </CardTitle>
              <CardDescription>
                {selectedDay
                  ? `${selectedEvents.length} ${selectedEvents.length === 1 ? "evento" : "eventi"}`
                  : "Clicca un giorno per vedere i dettagli"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {selectedDay && selectedEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                  <CalendarIcon className="h-8 w-8 text-muted-foreground/30" />
                  <p className="text-xs">Nessun evento per questo giorno</p>
                </div>
              ) : selectedEvents.length > 0 ? (
                <div className="space-y-2">
                  {selectedEvents.map((event) => {
                    const Icon = TYPE_ICONS[event.type] || CalendarIcon;
                    return (
                      <div
                        key={event.id}
                        className={`flex items-start gap-2.5 rounded-lg border p-3 ${TYPE_STYLES[event.type] || ""}`}
                      >
                        <Icon className="h-4 w-4 mt-0.5 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium">{event.title}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge variant="secondary" className="text-[9px]">
                              {event.type === "task" ? "Task" : event.type === "booking" ? "Demo" : "Deal"}
                            </Badge>
                            {event.value && (
                              <span className="text-[10px] font-medium">€{event.value.toLocaleString()}</span>
                            )}
                            {event.timeSlot && (
                              <span className="text-[10px] text-muted-foreground">{event.timeSlot}</span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 gap-2 text-muted-foreground">
                  <CalendarIcon className="h-8 w-8 text-muted-foreground/30" />
                  <p className="text-xs">Nessun giorno selezionato</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}