import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import PlaybookForm from '@/app/forms/playbook/page';
import ContactForm from '@/app/forms/contact/page';
import AssessmentForm from '@/app/forms/assessment/page';
import BookingForm from '@/app/forms/booking/page';

// Mock fetch
global.fetch = vi.fn();

describe('Public Forms', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('PlaybookForm', () => {
    it('renders and submits successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      } as Response);

      render(<PlaybookForm />);
      
      expect(screen.getByText('Scarica il Playbook')).toBeInTheDocument();
      
      fireEvent.change(screen.getByRole('textbox', { name: 'Nome' }), { target: { value: 'Mario' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Cognome' }), { target: { value: 'Rossi' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Email lavorativa' }), { target: { value: 'mario@test.com' } });
      fireEvent.click(screen.getByRole('checkbox'));
      
      fireEvent.submit(screen.getByRole('button', { name: /Scarica Playbook/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Playbook richiesto con successo!')).toBeInTheDocument();
      });
      
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/forms/playbook'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('mario@test.com')
        })
      );
    });
  });

  describe('ContactForm', () => {
    it('renders and submits successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      } as Response);

      render(<ContactForm />);
      
      expect(screen.getByText('Contattaci')).toBeInTheDocument();
      
      fireEvent.change(screen.getByRole('textbox', { name: 'Nome' }), { target: { value: 'Mario' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Cognome' }), { target: { value: 'Rossi' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Email lavorativa' }), { target: { value: 'mario@test.com' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Messaggio' }), { target: { value: 'Ciao' } });
      fireEvent.click(screen.getByRole('checkbox'));
      
      fireEvent.submit(screen.getByRole('button', { name: /Invia Messaggio/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Richiesta inviata!')).toBeInTheDocument();
      });
    });
  });

  describe('AssessmentForm', () => {
    it('renders and submits successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      } as Response);

      render(<AssessmentForm />);
      
      fireEvent.change(screen.getByRole('textbox', { name: 'Nome' }), { target: { value: 'Mario' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Cognome' }), { target: { value: 'Rossi' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Azienda' }), { target: { value: 'Acme' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Settore' }), { target: { value: 'Tech' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Email lavorativa' }), { target: { value: 'mario@test.com' } });
      fireEvent.change(screen.getByRole('combobox', { name: 'Livello attuale di adozione AI' }), { target: { value: 'exploring' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Qual è la tua sfida principale oggi?' }), { target: { value: 'Optimization' } });
      fireEvent.click(screen.getByRole('checkbox'));
      
      fireEvent.submit(screen.getByRole('button', { name: /Ottieni Risultati/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Assessment Completato!')).toBeInTheDocument();
      });
    });
  });

  describe('BookingForm', () => {
    it('renders and submits successfully', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      } as Response);

      render(<BookingForm />);
      
      fireEvent.change(screen.getByRole('textbox', { name: 'Nome' }), { target: { value: 'Mario' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Cognome' }), { target: { value: 'Rossi' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Azienda' }), { target: { value: 'Acme' } });
      fireEvent.change(screen.getByRole('textbox', { name: 'Email lavorativa' }), { target: { value: 'mario@test.com' } });
      fireEvent.change(screen.getByLabelText('Data Preferita'), { target: { value: '2025-01-01' } });
      fireEvent.change(screen.getByRole('combobox', { name: 'Fascia Oraria' }), { target: { value: 'morning' } });
      fireEvent.click(screen.getByRole('checkbox'));
      
      fireEvent.submit(screen.getByRole('button', { name: /Conferma Prenotazione/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Prenotazione Confermata!')).toBeInTheDocument();
      });
    });
  });
});
