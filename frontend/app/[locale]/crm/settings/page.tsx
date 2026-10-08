"use client";

import { useState, useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import { useCurrentUser, useUpdateUser } from "@/hooks/useUsers";
import { useAuth } from "@/hooks/useAuth";
import { User, Bell, Shield, Plug, Loader2 } from "lucide-react";
import { updateProfile } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { getAuthToken } from "@/lib/auth";

export default function SettingsPage() {
  const t = useTranslations("settings");
  const { data: currentUser } = useCurrentUser();
  const { user: firebaseUser } = useAuth();
  const updateUser = useUpdateUser();
  const [activeTab, setActiveTab] = useState("profile");
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarURL, setAvatarURL] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const NAV_ITEMS = [
    { label: t("profile"), icon: User, id: "profile" },
    { label: t("notifications"), icon: Bell, id: "notifications" },
    { label: t("security"), icon: Shield, id: "security" },
    { label: t("integrations"), icon: Plug, id: "integrations" },
  ];

  useEffect(() => {
    if (currentUser?.displayName) {
      const parts = currentUser.displayName.split(" ");
      setFirstName(parts[0] ?? "");
      setLastName(parts.slice(1).join(" "));
    }
  }, [currentUser]);

  useEffect(() => {
    const url = firebaseUser?.photoURL ?? null;
    const isBackendUrl = url && (url.includes("localhost:8088") || url.includes("/api/v1/"));
    setAvatarURL(isBackendUrl ? null : url);
  }, [firebaseUser]);

  async function handleAvatarUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !auth.currentUser) return;
    if (file.size > 1 * 1024 * 1024) {
      toast.error(t("avatarTooLarge"));
      return;
    }
    setAvatarUploading(true);
    try {
      const token = await getAuthToken();
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(
        "/api/v1/users/me/avatar",
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? t("avatarError"));
      }
      const { photoURL } = await res.json();
      await updateProfile(auth.currentUser, { photoURL });
      setAvatarURL(photoURL);
      toast.success(t("avatarUpdated"));
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : t("avatarError"));
    } finally {
      setAvatarUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleAvatarRemove() {
    if (!auth.currentUser) return;
    setAvatarUploading(true);
    try {
      await updateProfile(auth.currentUser, { photoURL: null });
      setAvatarURL(null);
      toast.success(t("avatarRemoved"));
    } catch {
      toast.error(t("avatarRemoveError"));
    } finally {
      setAvatarUploading(false);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!currentUser?.uid) return;
    const displayName = [firstName, lastName].filter(Boolean).join(" ");
    try {
      await updateUser.mutateAsync({ uid: currentUser.uid, data: { displayName } });
      toast.success(t("profileSaved"));
    } catch {
      toast.error(t("profileSaveError"));
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
    <div className="flex flex-col gap-6 p-6 max-w-[1400px] mx-auto w-full">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("title")}</h1>
        <p className="text-sm text-muted-foreground">{t("subtitle")}</p>
      </div>

      <Tabs value={activeTab} onValueChange={(v) => v && setActiveTab(v)} orientation="vertical" className="flex flex-col md:flex-row gap-6 items-start">
        {/* Sidebar nav */}
        <TabsList variant="line" className="w-full md:w-52 shrink-0 flex-col h-auto gap-0.5 bg-transparent p-0">
          {NAV_ITEMS.map((item) => (
            <TabsTrigger
              key={item.id}
              value={item.id}
              className="w-full justify-start gap-3 px-3 py-2 text-sm rounded-md data-active:bg-primary/10 data-active:text-primary"
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>{t("profile")}</CardTitle>
                <CardDescription>
                  {t("profileDesc")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Avatar */}
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarImage src={avatarURL ?? ""} />
                    <AvatarFallback className="text-lg">{initials}</AvatarFallback>
                  </Avatar>
                  <div className="space-y-1">
                    <div className="flex gap-2">
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/jpeg,image/png,image/gif"
                        className="hidden"
                        onChange={handleAvatarUpload}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={avatarUploading}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        {avatarUploading ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : null}
                        {t("uploadAvatar")}
                      </Button>
                      {avatarURL && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-muted-foreground"
                          disabled={avatarUploading}
                          onClick={handleAvatarRemove}
                        >
                          {t("remove")}
                        </Button>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">{t("avatarHint")}</p>
                  </div>
                </div>

                <Separator />

                <form onSubmit={handleSave} className="space-y-4">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">{t("firstName")}</Label>
                      <Input
                        id="firstName"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="Mario"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">{t("lastName")}</Label>
                      <Input
                        id="lastName"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Rossi"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">{t("emailLabel")}</Label>
                    <Input
                      id="email"
                      type="email"
                      disabled
                      value={currentUser?.email ?? ""}
                    />
                    <p className="text-xs text-muted-foreground">
                      {t("emailHint")}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="timezone">{t("timezone")}</Label>
                    <Select defaultValue="gmt+1">
                      <SelectTrigger id="timezone">
                        <SelectValue placeholder={t("selectTimezone")} />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gmt-8">(GMT-08:00) Pacific Time</SelectItem>
                        <SelectItem value="gmt-5">(GMT-05:00) Eastern Time</SelectItem>
                        <SelectItem value="gmt+0">(GMT+00:00) Greenwich Mean Time</SelectItem>
                        <SelectItem value="gmt+1">(GMT+01:00) Central European Time</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator />

                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" onClick={handleDiscard}>
                      {t("discard")}
                    </Button>
                    <Button type="submit" disabled={updateUser.isPending}>
                      {updateUser.isPending ? t("saving") : t("saveChanges")}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {NAV_ITEMS.filter((n) => n.id !== "profile").map((item) => (
            <TabsContent key={item.id} value={item.id}>
              <Card>
                <CardHeader>
                  <CardTitle>{item.label}</CardTitle>
                  <CardDescription>{t("comingSoon")}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center justify-center py-16 text-center gap-3 text-muted-foreground">
                    <item.icon className="h-10 w-10 opacity-30" />
                    <p className="text-sm">{t("comingSoonDetail")}</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </div>
  );
}