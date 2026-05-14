"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { UploadCloud } from "lucide-react";
import { importLeadsFromCSV } from "@/lib/csvImporter";
import { useQueryClient } from "@tanstack/react-query";

interface CsvImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CsvImportDialog({ open, onOpenChange }: CsvImportDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const result = await importLeadsFromCSV(file);
      alert(`Importazione completata:\n- Successo: ${result.success}\n- Falliti: ${result.failed}\n${result.failed > 0 ? '\nErrori:\n' + result.errors.slice(0, 5).join('\n') + (result.errors.length > 5 ? '\n...' : '') : ''}`);
      if (result.success > 0) {
        queryClient.invalidateQueries({ queryKey: ["leads"] });
      }
      onOpenChange(false);
    } catch (error: unknown) {
      console.error(error);
      const message = error instanceof Error ? error.message : String(error);
      alert("Errore durante l'importazione: " + message);
    } finally {
      setLoading(false);
      setFile(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Import Leads from CSV</DialogTitle>
          <DialogDescription>
            Upload a CSV file containing your leads. Make sure it has columns like &quot;email&quot;, &quot;firstName&quot;, &quot;lastName&quot;.
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex flex-col items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg p-10 mt-4 bg-muted/10">
          <UploadCloud className="h-10 w-10 text-muted-foreground mb-4" />
          <Input 
            type="file" 
            accept=".csv" 
            className="max-w-[250px]"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleUpload} disabled={!file || loading}>
            {loading ? "Importing..." : "Import Leads"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
