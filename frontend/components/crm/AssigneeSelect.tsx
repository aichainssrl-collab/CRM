"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface AssigneeSelectProps {
  value?: string;
  onChange: (val: string | null) => void;
  disabled?: boolean;
}

// In a real app, this would come from a useUsers() hook
const MOCK_TEAM = [
  { id: "user_1", name: "Alice Rossi", email: "alice@aichain.it" },
  { id: "user_2", name: "Bob Verdi", email: "bob@aichain.it" },
  { id: "user_3", name: "Charlie Bianchi", email: "charlie@aichain.it" },
];

export function AssigneeSelect({ value, onChange, disabled }: AssigneeSelectProps) {
  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select Assignee" />
      </SelectTrigger>
      <SelectContent>
        {MOCK_TEAM.map((user) => (
          <SelectItem key={user.id} value={user.id}>
            <div className="flex items-center gap-2">
              <Avatar className="h-6 w-6">
                <AvatarFallback className="text-[10px]">{user.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <span className="text-sm">{user.name}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
