/**
 * PDF document download helpers — triggers browser download with auth.
 */
export type PdfLang = "it" | "en";

export async function downloadDocumentPdf(
  kind: "proposals" | "invoices",
  id: string,
  lang: PdfLang = "it",
  fallbackName?: string
) {
  const { getAuthToken } = await import("@/lib/auth");

  const url = `/api/v1/${kind}/${id}/pdf?lang=${lang}`;
  const token = await getAuthToken();
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) throw new Error("PDF download failed");

  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1] || fallbackName || `${id}_${lang}.pdf`;

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = downloadUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}
