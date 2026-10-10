import { describe, it, expect, vi, beforeEach } from 'vitest';
import { importLeadsFromFile, importLeadsFromCSV } from '../lib/csvImporter';

vi.mock('../lib/auth', () => ({
  getAuthToken: vi.fn(),
}));

import { getAuthToken } from '../lib/auth';

const mockGetAuthToken = vi.mocked(getAuthToken);

function mockFetchOnce(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  return vi.mocked(global.fetch).mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: async () => ({}),
    ...response,
  } as Response);
}

describe('csvImporter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    mockGetAuthToken.mockResolvedValue('test-token');
  });

  it('exports importLeadsFromCSV as alias of importLeadsFromFile', () => {
    expect(importLeadsFromCSV).toBe(importLeadsFromFile);
  });

  it('uploads file as FormData to backend import endpoint', async () => {
    const file = new File(['email\njohn@example.com'], 'leads.csv', { type: 'text/csv' });

    mockFetchOnce({
      ok: true,
      status: 200,
      json: async () => ({ imported: 2, skipped: 1, errors: ['Email is required'] }),
    });

    const result = await importLeadsFromFile(file);

    expect(result.success).toBe(2);
    expect(result.duplicates).toBe(0);
    expect(result.failed).toBe(1);
    expect(result.errors).toEqual(['Email is required']);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = vi.mocked(global.fetch).mock.calls[0];
    expect(String(url)).toContain('/api/v1/leads/import');
    expect(init?.method).toBe('POST');
    expect(init?.headers).toEqual({ Authorization: 'Bearer test-token' });
    expect(init?.body).toBeInstanceOf(FormData);
    expect((init?.body as FormData).get('file')).toBe(file);
  });

  it('maps skipped rows without errors as duplicates', async () => {
    const file = new File(['email\na@b.com'], 'leads.csv', { type: 'text/csv' });

    mockFetchOnce({
      ok: true,
      status: 200,
      json: async () => ({ imported: 0, skipped: 3, errors: [] }),
    });

    const result = await importLeadsFromFile(file);
    expect(result).toEqual({ success: 0, duplicates: 3, failed: 0, errors: [] });
  });

  it('throws when user is not authenticated', async () => {
    mockGetAuthToken.mockResolvedValue(null);
    const file = new File(['x'], 'leads.csv', { type: 'text/csv' });

    await expect(importLeadsFromFile(file)).rejects.toThrow(/autenticato/i);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('throws auth error on 401/403', async () => {
    const file = new File(['x'], 'leads.csv', { type: 'text/csv' });
    mockFetchOnce({ ok: false, status: 401, json: async () => ({}) });

    await expect(importLeadsFromFile(file)).rejects.toThrow(/autenticazione/i);
  });

  it('throws server error message from response detail', async () => {
    const file = new File(['x'], 'leads.csv', { type: 'text/csv' });
    mockFetchOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: 'Email already exists' }),
    });

    await expect(importLeadsFromFile(file)).rejects.toThrow('Email already exists');
  });
});
