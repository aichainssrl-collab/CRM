export interface ImportResult {
  success: number;
  duplicates: number;
  failed: number;
  errors: string[];
}

/**
 * Importa lead da file CSV o XLSX tramite il backend.
 */
export async function importLeadsFromFile(file: File): Promise<ImportResult> {
  const { getAuthToken } = await import('./auth');
  const token = await getAuthToken();

  if (!token) {
    throw new Error('Non sei autenticato. Effettua il login prima di importare.');
  }

  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8088"}/api/v1/leads/import`,
    {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    }
  );

  if (response.status === 401 || response.status === 403) {
    throw new Error('Errore di autenticazione. Effettua nuovamente il login.');
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `Errore server (${response.status})`);
  }

  const data = await response.json();

  return {
    success: data.imported,
    duplicates: Math.max(0, data.skipped - data.errors.length),
    failed: data.errors.length,
    errors: data.errors,
  };
}

// Backward compat alias
export const importLeadsFromCSV = importLeadsFromFile;