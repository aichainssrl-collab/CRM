"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useUsers, useUpdateUser, useCreateUser, type CRMUser } from "@/hooks/useUsers";

function getInitials(user: CRMUser): string {
  if (user.displayName) {
    const parts = user.displayName.split(" ");
    return parts
      .slice(0, 2)
      .map((p) => p[0])
      .join("")
      .toUpperCase();
  }
  return user.email.slice(0, 2).toUpperCase();
}

export default function UserAdminPage() {
  const { data: users, isLoading } = useUsers();
  const updateUser = useUpdateUser();
  const createUser = useCreateUser();

  const [search, setSearch] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [newUser, setNewUser] = useState({ uid: "", email: "", displayName: "", role: "sales" });

  const filtered = (users ?? []).filter((u) => {
    const q = search.toLowerCase();
    return (
      u.email.toLowerCase().includes(q) ||
      (u.displayName ?? "").toLowerCase().includes(q)
    );
  });

  const totalUsers = users?.length ?? 0;
  const activeAdmins = (users ?? []).filter((u) => u.role === "admin" && u.isActive).length;

  function handleChangeRole(uid: string, role: string) {
    updateUser.mutate({ uid, data: { role } });
  }

  function handleDeactivate(uid: string) {
    updateUser.mutate({ uid, data: { isActive: false } });
  }

  async function handleCreateUser() {
    if (!newUser.uid || !newUser.email) return;
    await createUser.mutateAsync(newUser);
    setNewUser({ uid: "", email: "", displayName: "", role: "sales" });
    setAddOpen(false);
  }

  return (
    <main className="p-container_padding max-w-[1200px] mx-auto flex flex-col gap-stack_gap">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="font-display text-display text-on-background">User Management</h2>
          <p className="font-body text-body text-on-surface-variant mt-1">
            Manage system access, roles, and invitations.
          </p>
        </div>
        <Button
          onClick={() => setAddOpen(true)}
          className="bg-[#4f46e5] hover:bg-[#6366f1] text-white h-input_height px-4 font-body-medium flex gap-2"
        >
          <span className="material-symbols-outlined text-[18px]">add</span>
          Add User
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-4">
        <Card className="bg-surface border-outline-variant shadow-none">
          <CardContent className="p-6 flex flex-col">
            <span className="font-small-medium text-small-medium text-on-surface-variant uppercase tracking-wider mb-2">
              Total Users
            </span>
            <div className="flex items-end gap-3">
              {isLoading ? (
                <Skeleton className="h-9 w-16" />
              ) : (
                <span className="font-display text-display">{totalUsers}</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface border-outline-variant shadow-none">
          <CardContent className="p-6 flex flex-col">
            <span className="font-small-medium text-small-medium text-on-surface-variant uppercase tracking-wider mb-2">
              Active Admins
            </span>
            <div className="flex items-end gap-3">
              {isLoading ? (
                <Skeleton className="h-9 w-12" />
              ) : (
                <span className="font-display text-display">{activeAdmins}</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-surface border-outline-variant shadow-none">
          <CardContent className="p-6 flex flex-col">
            <span className="font-small-medium text-small-medium text-on-surface-variant uppercase tracking-wider mb-2">
              Pending Invites
            </span>
            <div className="flex items-end gap-3">
              <span className="font-display text-display">0</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-surface border-outline-variant shadow-none overflow-hidden flex flex-col">
        <div className="p-4 border-b border-outline-variant flex flex-col sm:flex-row gap-4 justify-between bg-surface">
          <div className="flex gap-2 items-center">
            <div className="relative w-64">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[16px]">
                search
              </span>
              <Input
                className="w-full h-input_height pl-8 pr-3 border-outline-variant focus-visible:ring-[#4f46e5] bg-surface font-small"
                placeholder="Search users..."
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button variant="outline" className="h-input_height border-outline-variant text-on-surface font-small-medium flex gap-2">
              <span className="material-symbols-outlined text-[16px]">filter_list</span>
              Filter
            </Button>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" className="h-input_height border-outline-variant text-on-surface font-small-medium flex gap-2">
              <span className="material-symbols-outlined text-[16px]">download</span>
              Export
            </Button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <TableHeader className="bg-surface">
              <TableRow className="border-b border-outline-variant hover:bg-transparent">
                <TableHead className="font-small-medium text-on-surface-variant uppercase tracking-wider">User</TableHead>
                <TableHead className="font-small-medium text-on-surface-variant uppercase tracking-wider">Role</TableHead>
                <TableHead className="font-small-medium text-on-surface-variant uppercase tracking-wider">Status</TableHead>
                <TableHead className="font-small-medium text-on-surface-variant uppercase tracking-wider">Created</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody className="font-body">
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i} className="border-outline-variant/50">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Skeleton className="h-8 w-8 rounded-full" />
                          <div className="flex flex-col gap-1">
                            <Skeleton className="h-4 w-32" />
                            <Skeleton className="h-3 w-40" />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                      <TableCell><Skeleton className="h-5 w-16" /></TableCell>
                      <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      <TableCell></TableCell>
                    </TableRow>
                  ))
                : filtered.map((user) => (
                    <TableRow key={user.uid} className="hover:bg-surface-container-low border-outline-variant/50 group">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-8 w-8 border border-outline-variant">
                            <AvatarFallback className="bg-surface-container-highest text-on-surface font-small-medium">
                              {getInitials(user)}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex flex-col">
                            <span className="font-body-medium text-on-surface">{user.displayName ?? "—"}</span>
                            <span className="font-small text-on-surface-variant">{user.email}</span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-small-medium text-on-surface border-outline-variant bg-surface rounded capitalize">
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {user.isActive ? (
                          <Badge variant="secondary" className="font-small-medium text-[#0f5132] bg-[#d1e7dd] hover:bg-[#d1e7dd] rounded-full gap-1.5 px-2.5 py-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#0f5132]"></span> Active
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="font-small-medium text-[#664d03] bg-[#fff3cd] hover:bg-[#fff3cd] rounded-full gap-1.5 px-2.5 py-0.5">
                            Inactive
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-on-surface-variant font-mono text-mono">
                        {new Date(user.createdAt).toLocaleDateString("it-IT")}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8 text-on-surface-variant hover:text-on-surface opacity-0 group-hover:opacity-100 transition-opacity">
                              <span className="material-symbols-outlined">more_horiz</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleChangeRole(user.uid, user.role === "admin" ? "sales" : "admin")}>
                              <span className="material-symbols-outlined text-[16px]">manage_accounts</span>
                              {user.role === "admin" ? "Set as Sales" : "Set as Admin"}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleChangeRole(user.uid, "readonly")}>
                              <span className="material-symbols-outlined text-[16px]">visibility</span>
                              Set as Readonly
                            </DropdownMenuItem>
                            {user.isActive && (
                              <DropdownMenuItem
                                variant="destructive"
                                onClick={() => handleDeactivate(user.uid)}
                              >
                                <span className="material-symbols-outlined text-[16px]">person_off</span>
                                Deactivate
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
            </TableBody>
          </Table>
        </div>

        <div className="p-4 border-t border-outline-variant bg-surface flex items-center justify-between">
          <span className="font-small text-on-surface-variant">
            {isLoading ? "Loading..." : `Showing ${filtered.length} of ${totalUsers} users`}
          </span>
        </div>
      </Card>

      <Sheet open={addOpen} onOpenChange={setAddOpen}>
        <SheetContent side="right" className="p-0 flex flex-col gap-0">
          <SheetHeader className="p-6 border-b border-outline-variant">
            <SheetTitle className="font-h3 text-h3 text-on-surface">Add New User</SheetTitle>
          </SheetHeader>
          <div className="flex flex-col gap-5 p-6 flex-1">
            <div className="space-y-2">
              <label className="block font-small-medium text-small-medium text-on-surface">UID</label>
              <Input
                className="w-full h-input_height border-outline-variant bg-surface font-body focus-visible:ring-[#4f46e5]"
                placeholder="Firebase UID"
                value={newUser.uid}
                onChange={(e) => setNewUser((p) => ({ ...p, uid: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="block font-small-medium text-small-medium text-on-surface">Email</label>
              <Input
                className="w-full h-input_height border-outline-variant bg-surface font-body focus-visible:ring-[#4f46e5]"
                placeholder="user@example.com"
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser((p) => ({ ...p, email: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="block font-small-medium text-small-medium text-on-surface">Display Name</label>
              <Input
                className="w-full h-input_height border-outline-variant bg-surface font-body focus-visible:ring-[#4f46e5]"
                placeholder="Full name"
                value={newUser.displayName}
                onChange={(e) => setNewUser((p) => ({ ...p, displayName: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="block font-small-medium text-small-medium text-on-surface">Role</label>
              <Select
                value={newUser.role}
                onValueChange={(v) => setNewUser((p) => ({ ...p, role: v }))}
              >
                <SelectTrigger className="w-full h-input_height border-outline-variant bg-surface font-body focus:ring-[#4f46e5]">
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="sales">Sales</SelectItem>
                  <SelectItem value="readonly">Readonly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <SheetFooter className="border-t border-outline-variant">
            <Button
              variant="outline"
              className="flex-1 h-input_height border-outline-variant text-on-surface font-body-medium"
              onClick={() => setAddOpen(false)}
            >
              Cancel
            </Button>
            <Button
              className="flex-1 h-input_height bg-[#4f46e5] hover:bg-[#6366f1] text-white font-body-medium"
              onClick={handleCreateUser}
              disabled={createUser.isPending}
            >
              {createUser.isPending ? "Creating..." : "Create User"}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </main>
  );
}
