"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useLeads, useCreateLead, useUpdateLead, useDeleteLead, Lead } from "@/hooks/useLeads";
import { LeadTable } from "@/components/crm/LeadTable";
import { LeadFilters } from "@/components/crm/LeadFilters";
import { LeadForm } from "@/components/crm/LeadForm";
import { CsvImportDialog } from "@/components/crm/CsvImportDialog";
import { Plus, Download } from "lucide-react";

export default function LeadsPage() {
  const router = useRouter();
  
  // State per i filtri
  const [filters, setFilters] = useState<Record<string, string>>({});
  
  // State per la modale e il form
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  // Hooks
  const { data: leads = [], isLoading } = useLeads(filters);
  const createLead = useCreateLead();
  const updateLead = useUpdateLead();
  const deleteLead = useDeleteLead();

  const handleFilterChange = (key: string, value: string | undefined) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === undefined) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
  };

  const handleCreateNew = () => {
    setSelectedLead(null);
    setIsFormOpen(true);
  };

  const handleEdit = (lead: Lead) => {
    setSelectedLead(lead);
    setIsFormOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm("Sei sicuro di voler eliminare questo lead?")) {
      await deleteLead.mutateAsync(id);
    }
  };

  const handleView = (id: string) => {
    router.push(`/crm/leads/${id}`);
  };

  const handleFormSubmit = async (data: Partial<Lead>) => {
    if (selectedLead) {
      await updateLead.mutateAsync({ id: selectedLead.id, data });
    } else {
      await createLead.mutateAsync(data);
    }
  };

  return (
    <main className="flex-1 overflow-auto bg-surface flex relative h-[calc(100vh-56px)]">
      <div className="flex-1 flex flex-col p-container_padding min-w-0">
        
        {/* Page Header & Actions */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="font-h1 text-h1 text-on-surface">
            Leads <span className="text-on-surface-variant font-normal">({leads.length})</span>
          </h2>
          <div className="flex items-center gap-3">
            <Button 
              variant="outline" 
              onClick={() => setIsImportOpen(true)}
              className="h-input_height px-4 border-outline-variant text-primary font-body-medium flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Importa CSV
            </Button>
            <Button 
              onClick={handleCreateNew}
              className="bg-primary text-on-primary h-input_height px-4 font-body-medium flex items-center gap-2 hover:bg-primary/90"
            >
              <Plus className="h-4 w-4" />
              Nuovo Lead
            </Button>
          </div>
        </div>

        {/* Filters */}
        <LeadFilters filters={filters} onChange={handleFilterChange} />

        {/* Data Table */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded flex-1 flex flex-col overflow-hidden">
          <LeadTable 
            leads={leads} 
            isLoading={isLoading} 
            onEdit={handleEdit}
            onDelete={handleDelete}
            onView={handleView}
          />
        </div>
        
      </div>

      {/* Dialogs and Sheets */}
      <LeadForm 
        open={isFormOpen} 
        onOpenChange={setIsFormOpen} 
        lead={selectedLead} 
        onSubmit={handleFormSubmit} 
      />
      <CsvImportDialog 
        open={isImportOpen} 
        onOpenChange={setIsImportOpen} 
      />
    </main>
  );
}
