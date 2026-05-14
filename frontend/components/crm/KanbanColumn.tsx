"use client";

import { Deal } from "@/hooks/useDeals";
import { KanbanCard } from "@/components/crm/KanbanCard";
import { Droppable } from "@hello-pangea/dnd";

export function KanbanColumn({ stage, deals }: { stage: { id: string, title: string }, deals: Deal[] }) {
  return (
    <div className="flex flex-col w-80 shrink-0 bg-muted/30 rounded-lg">
      <div className="p-3 font-semibold text-sm border-b flex items-center justify-between">
        {stage.title}
        <span className="bg-muted text-muted-foreground text-xs px-2 py-0.5 rounded-full">
          {deals.length}
        </span>
      </div>
      <Droppable droppableId={stage.id}>
        {(provided, snapshot) => (
          <div 
            {...provided.droppableProps} 
            ref={provided.innerRef}
            className={`flex-1 p-2 space-y-2 min-h-[150px] transition-colors ${snapshot.isDraggingOver ? "bg-muted/50" : ""}`}
          >
            {deals.map((deal, index) => (
              <KanbanCard key={deal.id} deal={deal} index={index} />
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </div>
  );
}
