"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { UploadCloud, FileSpreadsheet, FileText } from "lucide-react";
import { importLeadsFromFile } from "@/lib/csvImporter";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

interface CsvImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CsvImportDialog({ open, onOpenChange }: CsvImportDialogProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const queryClient = useQueryClient();

  const isExcel = file?.name.endsWith(".xlsx") || file?.name.endsWith(".xls");

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const result = await importLeadsFromFile(file);
      const lines = [
        `Importati: ${result.success}`,
        result.duplicates > 0 ? `Gia presenti (saltati): ${result.duplicates}` : null,
        result.failed > 0 ? `Errori: ${result.failed}` : null,
        result.errors.length > 0
          ? '\nDettaglio errori:\n' + result.errors.slice(0, 5).join('\n') + (result.errors.length > 5 ? '\n...' : '')
          : null,
      ].filter(Boolean).join('\n');
      toast.success("Importazione completata", { description: lines, duration: 8000 });
      if (result.success > 0) {
        queryClient.invalidateQueries({ queryKey: ["leads"] });
      }
      onOpenChange(false);
    } catch (error: unknown) {
      console.error(error);
      const message = error instanceof Error ? error.message : String(error);
      toast.error("Errore durante l'importazione", { description: message });
    } finally {
      setLoading(false);
      setFile(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Importa Lead</DialogTitle>
          <DialogDescription>
            Carica un file CSV o Excel (.xlsx). Il sistema rileva automaticamente le colonne: email, nome, cognome, azienda, telefono, tag.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg p-10 mt-4 bg-muted/10 hover:bg-muted/20 transition-colors cursor-pointer"
          onClick={() => document.getElementById('file-import')?.click()}
        >
          {file ? (
            <div className="flex items-center gap-2 text-sm">
              {isExcel ? (
                <FileSpreadsheet className="h-5 w-5 text-emerald-500" />
              ) : (
                <FileText className="h-5 w-5 text-blue-500" />
              )}
              <span className="font-medium">{file.name}</span>
              <span className="text-muted-foreground">({(file.size / 1024).toFixed(0)} KB)</span>
            </div>
          ) : (
            <>
              <UploadCloud className="h-10 w-10 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground mb-2">Trascina il file oppure clicca per selezionare</p>
            </>
          )}
          <Input
            id="file-import"
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>

        <DialogFooter className="mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
          <Button onClick={handleUpload} disabled={!file || loading}>
            {loading ? "Importazione..." : "Importa Lead"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}