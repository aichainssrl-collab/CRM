import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CsvImportDialog } from '@/components/crm/CsvImportDialog';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('@/lib/firebase', () => ({
  auth: {},
  firestoreDb: {},
  storage: {},
}));

vi.mock('next-intl', () => ({
  useTranslations: () => (key: string) => {
    const dict: Record<string, string> = {
      title: 'Importa Lead',
      description: 'Carica un file CSV o Excel',
      dragDrop: 'Trascina il file oppure clicca per selezionare',
      importBtn: 'Importa Lead',
      importing: 'Importazione...',
      success: 'Importazione completata',
      imported: 'Importati:',
      alreadyPresent: 'Gia presenti (saltati):',
      errors: 'Errori:',
      errorDetail: 'Dettaglio errori:',
      importError: 'Errore durante l\'importazione',
    };
    return dict[key] ?? key;
  },
}));

// Mock del ResizeObserver che manca in jsdom
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock di pointer event per dialog
if (typeof window !== 'undefined') {
  window.HTMLElement.prototype.hasPointerCapture = vi.fn();
  window.HTMLElement.prototype.releasePointerCapture = vi.fn();
}

describe('CsvImportDialog UI', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('renders dialog content with shadcn bg-card surface', async () => {
    render(
      <CsvImportDialog open={true} onOpenChange={vi.fn()} />,
      { wrapper }
    );

    const dialogContent = await screen.findByRole('dialog');

    // Token shadcn (no MD3 surface-*)
    expect(dialogContent.className).toContain('bg-card');
    expect(dialogContent.className).not.toContain('bg-surface');
    expect(dialogContent.className).not.toContain('bg-popover');
  });

  it('renders title and dropzone copy', async () => {
    render(
      <CsvImportDialog open={true} onOpenChange={vi.fn()} />,
      { wrapper }
    );

    expect(await screen.findByRole('heading', { name: 'Importa Lead' })).toBeInTheDocument();
    expect(screen.getByText('Trascina il file oppure clicca per selezionare')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Importa Lead' })).toBeInTheDocument();
  });
});
