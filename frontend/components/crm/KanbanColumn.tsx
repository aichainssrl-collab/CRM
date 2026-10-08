"use client";

import { Deal } from "@/hooks/useDeals";
import { KanbanCard } from "@/components/crm/KanbanCard";
import { Badge } from "@/components/ui/badge";
import { Droppable } from "@hello-pangea/dnd";

export function KanbanColumn({ stage, deals }: { stage: { id: string, title: string }, deals: Deal[] }) {
  return (
    <div className="flex flex-col min-w-0 bg-muted/30 rounded-lg overflow-hidden">
      <div className="p-3 font-semibold text-sm border-b flex items-center justify-between gap-2 min-w-0">
        <span className="truncate">{stage.title}</span>
        <Badge variant="secondary" className="text-xs tabular-nums">
          {deals.length}
        </Badge>
      </div>
      <Droppable droppableId={stage.id}>
        {(provided, snapshot) => (
          <div
            {...provided.droppableProps}
            ref={provided.innerRef}
            className={`flex-1 p-2 space-y-2 min-h-[150px] transition-colors rounded-b-lg ${snapshot.isDraggingOver ? "bg-primary/5 ring-1 ring-primary/20 ring-inset" : ""}`}
          >
            {deals.map((deal, index) => (
              <KanbanCard key={deal.id} deal={deal} index={index} />
            ))}
            {deals.length === 0 && !snapshot.isDraggingOver && (
              <div className="flex items-center justify-center h-20 text-xs text-muted-foreground/50">
                Trascina qui
              </div>
            )}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </div>
  );
}
