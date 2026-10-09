/**
 * CSV Export helpers — triggers browser download.
 */
export async function downloadCSV(type: "leads" | "deals" | "contacts", params?: Record<string, string>) {
  const { getAuthToken } = await import("@/lib/auth");

  const searchParams = new URLSearchParams(params);
  const qs = searchParams.toString();
  const url = `/api/v1/export/${type}${qs ? `?${qs}` : ""}`;

  const token = await getAuthToken();
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) throw new Error("Export fallito");

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = `${type}_export.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}