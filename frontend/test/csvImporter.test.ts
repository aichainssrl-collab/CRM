import { describe, it, expect, vi, beforeEach } from 'vitest';
import { importLeadsFromCSV } from '../lib/csvImporter';
import * as api from '../lib/api';

vi.mock('../lib/api', () => ({
  apiFetch: vi.fn(),
}));

describe('csvImporter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should parse CSV and send valid rows to API', async () => {
    const csvContent = `firstName,lastName,email,companyName
John,Doe,john@example.com,Acme
Jane,Smith,jane@example.com,Global
NoEmail,User,,BadCorp`;

    const file = new File([csvContent], 'leads.csv', { type: 'text/csv' });
    
    // Mock successful API response for John and Jane
    (api.apiFetch as any).mockResolvedValueOnce({ id: '1' });
    (api.apiFetch as any).mockResolvedValueOnce({ id: '2' });

    const result = await importLeadsFromCSV(file);

    expect(result.success).toBe(2);
    expect(result.failed).toBe(1);
    expect(result.errors.length).toBe(1);
    expect(result.errors[0]).toContain('Email is required');

    expect(api.apiFetch).toHaveBeenCalledTimes(2);
    expect(api.apiFetch).toHaveBeenNthCalledWith(1, '/api/v1/leads', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com',
        companyName: 'Acme',
        source: 'csv_import',
        pipelineStage: 'new',
        status: 'new'
      })
    }));

    expect(api.apiFetch).toHaveBeenNthCalledWith(2, '/api/v1/leads', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        firstName: 'Jane',
        lastName: 'Smith',
        email: 'jane@example.com',
        companyName: 'Global',
        source: 'csv_import',
        pipelineStage: 'new',
        status: 'new'
      })
    }));
  });

  it('should handle API errors during import', async () => {
    const csvContent = `email\nbad@example.com`;
    const file = new File([csvContent], 'leads.csv', { type: 'text/csv' });
    
    (api.apiFetch as any).mockRejectedValueOnce(new Error('Email already exists'));

    const result = await importLeadsFromCSV(file);

    expect(result.success).toBe(0);
    expect(result.failed).toBe(1);
    expect(result.errors[0]).toContain('Email already exists');
  });
});
