"use client";

import { Deal } from "@/hooks/useDeals";
import { KanbanColumn } from "@/components/crm/KanbanColumn";
import { DragDropContext, DropResult } from "@hello-pangea/dnd";
import { useUpdateDeal } from "@/hooks/useDeals";

const STAGES = [
  { id: "new", title: "New" },
  { id: "contacted", title: "Contacted" },
  { id: "qualified", title: "Qualified" },
  { id: "proposal", title: "Proposal" },
  { id: "won", title: "Won" },
  { id: "lost", title: "Lost" },
];

export function KanbanBoard({ deals }: { deals: Deal[] }) {
  const { mutate: updateDeal } = useUpdateDeal();

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const sourceStage = result.source.droppableId;
    const destStage = result.destination.droppableId;

    if (sourceStage !== destStage) {
      updateDeal({
        id: result.draggableId,
        data: { stage: destStage },
      });
    }
  };

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4 h-full min-h-[500px]">
        {STAGES.map(stage => (
          <KanbanColumn 
            key={stage.id} 
            stage={stage} 
            deals={deals.filter(d => d.stage === stage.id)} 
          />
        ))}
      </div>
    </DragDropContext>
  );
}
