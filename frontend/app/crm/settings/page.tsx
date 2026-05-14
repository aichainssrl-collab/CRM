"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { toast } from "sonner";
import { useCurrentUser } from "@/hooks/useUsers";
import { useUpdateUser } from "@/hooks/useUsers";

export default function SettingsPage() {
  const { data: currentUser } = useCurrentUser();
  const updateUser = useUpdateUser();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  useEffect(() => {
    if (currentUser?.displayName) {
      const parts = currentUser.displayName.split(" ");
      setFirstName(parts[0] ?? "");
      setLastName(parts.slice(1).join(" "));
    }
  }, [currentUser]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!currentUser?.uid) return;
    const displayName = [firstName, lastName].filter(Boolean).join(" ");
    try {
      await updateUser.mutateAsync({ uid: currentUser.uid, data: { displayName } });
      toast.success("Profile saved successfully.");
    } catch {
      toast.error("Failed to save profile. Please try again.");
    }
  }

  function handleDiscard() {
    if (currentUser?.displayName) {
      const parts = currentUser.displayName.split(" ");
      setFirstName(parts[0] ?? "");
      setLastName(parts.slice(1).join(" "));
    } else {
      setFirstName("");
      setLastName("");
    }
  }

  const initials = [firstName[0], lastName[0]].filter(Boolean).join("").toUpperCase() || "??";

  return (
    <main className="max-w-6xl mx-auto p-container_padding flex flex-col md:flex-row gap-8">
      <aside className="w-full md:w-64 shrink-0">
        <nav className="space-y-1">
          <a
            className="flex items-center gap-3 px-3 py-2.5 rounded bg-surface-container-high text-primary font-body-medium text-body-medium"
            href="#"
          >
            <span className="material-symbols-outlined">person</span>
            Profile
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2.5 rounded text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface font-body text-body transition-colors"
            href="#"
          >
            <span className="material-symbols-outlined">notifications</span>
            Notifications
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2.5 rounded text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface font-body text-body transition-colors"
            href="#"
          >
            <span className="material-symbols-outlined">security</span>
            Security
          </a>
          <a
            className="flex items-center gap-3 px-3 py-2.5 rounded text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface font-body text-body transition-colors"
            href="#"
          >
            <span className="material-symbols-outlined">integration_instructions</span>
            Integrations
          </a>
        </nav>
      </aside>

      <div className="flex-1 space-y-8">
        <div>
          <h3 className="font-h2 text-h2 mb-1 text-on-surface">Profile Settings</h3>
          <p className="font-body text-body text-on-surface-variant">
            Manage your personal information and how it is displayed across the workspace.
          </p>
        </div>

        <Card className="bg-surface border-outline-variant shadow-sm">
          <CardContent className="p-6">
            <div className="flex items-center gap-6 mb-8">
              <div className="relative group cursor-pointer">
                <Avatar className="h-20 w-20 border-2 border-outline-variant group-hover:opacity-80 transition-opacity">
                  <AvatarFallback className="bg-surface-container-high text-on-surface-variant font-display text-display">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute inset-0 bg-primary/40 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="material-symbols-outlined text-on-primary">photo_camera</span>
                </div>
              </div>
              <div>
                <div className="flex gap-3">
                  <Button className="h-input_height px-4 bg-primary text-on-primary hover:bg-primary/90 font-body-medium">
                    Upload Avatar
                  </Button>
                  <Button variant="outline" className="h-input_height px-4 border-outline-variant text-on-surface hover:bg-surface-container-low font-body-medium">
                    Remove
                  </Button>
                </div>
                <p className="font-small text-small text-on-surface-variant mt-2">
                  JPG, GIF or PNG. 1MB max.
                </p>
              </div>
            </div>

            <form onSubmit={handleSave} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="block font-small-medium text-small-medium text-on-surface">
                    First Name
                  </label>
                  <Input
                    className="w-full h-input_height border-outline-variant bg-surface font-body focus-visible:ring-primary"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="block font-small-medium text-small-medium text-on-surface">
                    Last Name
                  </label>
                  <Input
                    className="w-full h-input_height border-outline-variant bg-surface font-body focus-visible:ring-primary"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="block font-small-medium text-small-medium text-on-surface">
                  Email Address
                </label>
                <Input
                  className="w-full h-input_height border-outline-variant bg-surface-container-low font-body text-on-surface-variant cursor-not-allowed"
                  disabled
                  type="email"
                  value={currentUser?.email ?? ""}
                />
                <p className="font-small text-small text-on-surface-variant mt-1">
                  Email cannot be changed directly. Contact IT admin for updates.
                </p>
              </div>

              <div className="space-y-2">
                <label className="block font-small-medium text-small-medium text-on-surface">
                  Timezone
                </label>
                <Select defaultValue="gmt+1">
                  <SelectTrigger className="w-full h-input_height border-outline-variant bg-surface font-body focus:ring-primary">
                    <SelectValue placeholder="Select timezone" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="gmt-8">(GMT-08:00) Pacific Time (US & Canada)</SelectItem>
                    <SelectItem value="gmt-5">(GMT-05:00) Eastern Time (US & Canada)</SelectItem>
                    <SelectItem value="gmt+0">(GMT+00:00) Greenwich Mean Time</SelectItem>
                    <SelectItem value="gmt+1">(GMT+01:00) Central European Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-outline-variant/50">
                <Button
                  type="button"
                  variant="outline"
                  className="h-input_height px-4 border-outline-variant text-on-surface hover:bg-surface-container-low font-body-medium"
                  onClick={handleDiscard}
                >
                  Discard
                </Button>
                <Button
                  type="submit"
                  className="h-input_height px-4 bg-primary text-on-primary hover:bg-primary/90 font-body-medium"
                  disabled={updateUser.isPending}
                >
                  {updateUser.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
