"use client";

import { useState } from "react";
import { useCreateActivity } from "@/hooks/useActivities";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardFooter } from "@/components/ui/card";

export function AddActivityForm({ leadId }: { leadId: string }) {
  const { mutateAsync: createActivity } = useCreateActivity(leadId);
  const [type, setType] = useState("note");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!body.trim()) return;
    setLoading(true);
    try {
      await createActivity({
        type,
        body,
        title: `${type.charAt(0).toUpperCase() + type.slice(1)} added`,
        metadata: {},
      });
      setBody("");
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardContent className="pt-6 space-y-4">
        <div className="flex items-center gap-4">
          <Select value={type} onValueChange={(val) => val && setType(val)}>
            <SelectTrigger className="w-[150px]">
              <SelectValue placeholder="Activity Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="note">Note</SelectItem>
              <SelectItem value="call">Call</SelectItem>
              <SelectItem value="meeting">Meeting</SelectItem>
              <SelectItem value="email">Email Sent</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Textarea 
          placeholder="Add details..." 
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className="min-h-[100px]"
        />
      </CardContent>
      <CardFooter className="justify-end bg-muted/20 border-t py-3">
        <Button onClick={handleSubmit} disabled={!body.trim() || loading}>
          {loading ? "Adding..." : "Add Activity"}
        </Button>
      </CardFooter>
    </Card>
  );
}
