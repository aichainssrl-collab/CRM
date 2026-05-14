"use client";

import { useState } from "react";
import { Lead } from "@/hooks/useLeads";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet";

interface LeadFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  lead?: Lead | null;
  onSubmit: (data: Partial<Lead>) => Promise<void>;
}

export function LeadForm({ open, onOpenChange, lead, onSubmit }: LeadFormProps) {
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    
    try {
      if (lead) {
        // Edit mode: backend LeadUpdate schema doesn't accept email or pipelineStage
        const updateData = {
          firstName: formData.get("firstName") as string,
          lastName: formData.get("lastName") as string,
          companyName: formData.get("companyName") as string,
          phone: formData.get("phone") as string,
        };
        await onSubmit(updateData);
      } else {
        // Create mode: needs email and pipelineStage
        const createData = {
          email: formData.get("email") as string,
          firstName: formData.get("firstName") as string,
          lastName: formData.get("lastName") as string,
          companyName: formData.get("companyName") as string,
          phone: formData.get("phone") as string,
          pipelineStage: "new",
          status: "new"
        };
        await onSubmit(createData);
      }
      onOpenChange(false);
    } catch (error) {
      console.error(error);
      alert("Errore durante il salvataggio del lead.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="sm:max-w-md overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{lead ? "Edit Lead" : "Add New Lead"}</SheetTitle>
          <SheetDescription>
            {lead ? "Update lead details below." : "Fill in the details to create a new lead."}
          </SheetDescription>
        </SheetHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6 py-6">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">Email *</label>
            <Input 
              id="email" 
              name="email" 
              type="email" 
              required 
              defaultValue={lead?.email} 
              disabled={!!lead}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="firstName" className="text-sm font-medium">First Name</label>
              <Input id="firstName" name="firstName" defaultValue={lead?.firstName} />
            </div>
            <div className="space-y-2">
              <label htmlFor="lastName" className="text-sm font-medium">Last Name</label>
              <Input id="lastName" name="lastName" defaultValue={lead?.lastName} />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="companyName" className="text-sm font-medium">Company</label>
            <Input id="companyName" name="companyName" defaultValue={lead?.companyName} />
          </div>

          <div className="space-y-2">
            <label htmlFor="phone" className="text-sm font-medium">Phone</label>
            <Input id="phone" name="phone" type="tel" defaultValue={lead?.phone} />
          </div>

          <SheetFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
