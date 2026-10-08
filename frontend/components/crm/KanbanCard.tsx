"use client";

import { Deal } from "@/hooks/useDeals";
import { Draggable } from "@hello-pangea/dnd";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { DollarSign, Calendar } from "lucide-react";

export function KanbanCard({ deal, index }: { deal: Deal, index: number }) {
  return (
    <Draggable draggableId={deal.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          style={{ ...provided.draggableProps.style }}
          className={snapshot.isDragging ? "opacity-80" : ""}
        >
          <Card className="hover:border-primary/50 transition-colors cursor-grab active:cursor-grabbing">
            <CardContent className="p-3">
              <div className="font-medium text-sm mb-2">{deal.title}</div>
              <div className="flex flex-col gap-1.5 mt-2">
                {deal.value !== undefined && (
                  <div className="flex items-center text-xs text-muted-foreground">
                    <DollarSign className="h-3 w-3 mr-1" />
                    {new Intl.NumberFormat("en-US", { style: "currency", currency: "EUR" }).format(deal.value)}
                  </div>
                )}
                {deal.expectedClose && (
                  <div className="flex items-center text-xs text-muted-foreground">
                    <Calendar className="h-3 w-3 mr-1" />
                    {new Date(deal.expectedClose).toLocaleDateString()}
                  </div>
                )}
                <div className="mt-2 flex items-center justify-between">
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0.5">
                    {deal.probability}%
                  </Badge>
                  {deal.assignedTo && (
                    <div className="h-5 w-5 rounded-full bg-muted flex items-center justify-center text-[10px] font-medium">
                      {deal.assignedTo.charAt(0).toUpperCase()}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </Draggable>
  );
}
