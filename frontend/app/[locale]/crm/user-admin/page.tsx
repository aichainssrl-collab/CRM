"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { Plus, Search, MoreHorizontal, UserCheck, Users, ShieldCheck } from "lucide-react";

function getInitials(user: CRMUser): string {
  if (user.displayName) {
    const parts = user.displayName.split(" ");
    return parts.slice(0, 2).map((p) => p[0]).join("").toUpperCase();
  }
  return user.email.slice(0, 2).toUpperCase();
}

export default function UserAdminPage() {
  const t = useTranslations("userAdmin");
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
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
        </div>
        <Button onClick={() => setAddOpen(true)} className="gap-2 self-start sm:self-auto">
          <Plus className="h-4 w-4" />
          {t("addUser")}
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{t("totalUsers")}</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-12" /> : <div className="text-2xl font-bold">{totalUsers}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{t("activeAdmins")}</CardTitle>
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-8 w-12" /> : <div className="text-2xl font-bold">{activeAdmins}</div>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{t("pendingInvites")}</CardTitle>
            <UserCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">0</div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <div className="flex items-center gap-3 px-4 py-3 border-b">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder={t("searchUsers")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("user")}</TableHead>
                <TableHead>{t("role")}</TableHead>
                <TableHead>{t("status")}</TableHead>
                <TableHead>{t("createdAt")}</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading
                ? Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
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
                      <TableCell />
                    </TableRow>
                  ))
                : filtered.map((user) => (
                    <TableRow key={user.uid} className="group">
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="h-8 w-8">
                            <AvatarFallback className="text-xs">{getInitials(user)}</AvatarFallback>
                          </Avatar>
                          <div className="flex flex-col">
                            <span className="text-sm font-medium">{user.displayName ?? "—"}</span>
                            <span className="text-xs text-muted-foreground">{user.email}</span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">{user.role}</Badge>
                      </TableCell>
                      <TableCell>
                        {user.isActive ? (
                          <Badge variant="secondary" className="gap-1.5 text-success bg-success-muted border-success/20 hover:bg-success-muted">
                            <span className="h-1.5 w-1.5 rounded-full bg-success" />
                            {t("active")}
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="text-warning bg-warning-muted hover:bg-warning-muted">
                            {t("inactive")}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(user.createdAt).toLocaleDateString("it-IT")}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger render={<Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100" />}>
                            <MoreHorizontal className="h-4 w-4" />
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleChangeRole(user.uid, user.role === "admin" ? "sales" : "admin")}>
                              {user.role === "admin" ? t("setSales") : t("setAdmin")}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleChangeRole(user.uid, "readonly")}>
                              {t("setReadonly")}
                            </DropdownMenuItem>
                            {user.isActive && (
                              <DropdownMenuItem variant="destructive" onClick={() => handleDeactivate(user.uid)}>
                                {t("deactivate")}
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

        <div className="px-4 py-3 border-t">
          <span className="text-xs text-muted-foreground">
            {isLoading ? t("loading") : t("userCount", { filtered: filtered.length, total: totalUsers })}
          </span>
        </div>
      </Card>

      {/* Add User Sheet */}
      <Sheet open={addOpen} onOpenChange={setAddOpen}>
        <SheetContent className="sm:max-w-md">
          <SheetHeader>
            <SheetTitle>{t("addUser")}</SheetTitle>
          </SheetHeader>
          <div className="flex flex-col gap-4 py-6">
            <div className="space-y-2">
              <Label htmlFor="new-uid">Firebase UID</Label>
              <Input
                id="new-uid"
                placeholder="Firebase UID"
                value={newUser.uid}
                onChange={(e) => setNewUser((p) => ({ ...p, uid: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-email">{t("email")}</Label>
              <Input
                id="new-email"
                placeholder="user@example.com"
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser((p) => ({ ...p, email: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-name">{t("fullName")}</Label>
              <Input
                id="new-name"
                placeholder="Mario Rossi"
                value={newUser.displayName}
                onChange={(e) => setNewUser((p) => ({ ...p, displayName: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-role">{t("role")}</Label>
              <Select value={newUser.role} onValueChange={(v) => setNewUser((p) => ({ ...p, role: v ?? p.role }))}>
                <SelectTrigger id="new-role">
                  <SelectValue placeholder={t("selectRole")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="sales">Sales</SelectItem>
                  <SelectItem value="readonly">Readonly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <SheetFooter>
            <Button variant="outline" onClick={() => setAddOpen(false)}>Annulla</Button>
            <Button onClick={handleCreateUser} disabled={createUser.isPending}>
              {createUser.isPending ? t("creating") : t("createUser")}
            </Button>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}