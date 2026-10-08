"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ShieldCheck, MonitorSmartphone, MapPin } from "lucide-react";

interface ConsentLog {
  id: string;
  leadId: string;
  action: string;
  purpose: string;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
}

export function GdprConsentLog({ logs }: { logs: ConsentLog[] }) {
  if (!logs?.length) {
    return (
      <div className="text-center py-8 text-muted-foreground border border-dashed rounded-lg bg-muted/20">
        No consent logs found.
      </div>
    );
  }

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date & Time</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Purpose</TableHead>
            <TableHead>Source Details</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs.map((log) => (
            <TableRow key={log.id}>
              <TableCell className="text-sm">
                {new Date(log.timestamp).toLocaleString()}
              </TableCell>
              <TableCell>
                <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${
                  log.action === "granted" ? "bg-success-muted text-success" :
                  log.action === "revoked" ? "bg-destructive/10 text-destructive" :
                  "bg-muted text-muted-foreground"
                }`}>
                  <ShieldCheck className="h-3 w-3" />
                  {log.action}
                </span>
              </TableCell>
              <TableCell className="text-sm">{log.purpose}</TableCell>
              <TableCell className="text-xs text-muted-foreground">
                <div className="flex flex-col gap-1">
                  {log.ipAddress && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" /> {log.ipAddress}
                    </div>
                  )}
                  {log.userAgent && (
                    <div className="flex items-center gap-1">
                      <MonitorSmartphone className="h-3 w-3" /> 
                      <span className="truncate max-w-[200px]" title={log.userAgent}>{log.userAgent}</span>
                    </div>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
