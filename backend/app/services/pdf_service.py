"""
PDF export for proposals and invoices (fpdf2, pure Python).
IT/EN labels, branded AiChain header, VAT line (default 22%).
"""
from datetime import datetime
from typing import Literal
from fpdf import FPDF
import re

from app.config import settings

Lang = Literal["it", "en"]

NAVY = (30, 58, 110)
GRAY = (90, 90, 90)
LIGHT = (245, 246, 250)
DARK = (20, 20, 20)

LABELS: dict[str, dict[str, str]] = {
    "it": {
        "proposal": "PREVENTIVO",
        "invoice": "FATTURA",
        "date": "Data",
        "due": "Scadenza",
        "valid_until": "Valido fino al",
        "status": "Stato",
        "client": "CLIENTE",
        "subject": "OGGETTO",
        "description": "Descrizione",
        "qty": "Qta",
        "unit_price": "Prezzo",
        "line_total": "Totale",
        "subtotal": "Imponibile",
        "vat": "IVA",
        "total": "TOTALE",
        "notes": "NOTE",
        "payments": "PAGAMENTI",
        "generated": "documento generato il",
        "page": "Pagina",
    },
    "en": {
        "proposal": "QUOTE",
        "invoice": "INVOICE",
        "date": "Date",
        "due": "Due date",
        "valid_until": "Valid until",
        "status": "Status",
        "client": "BILL TO",
        "subject": "SUBJECT",
        "description": "Description",
        "qty": "Qty",
        "unit_price": "Unit price",
        "line_total": "Total",
        "subtotal": "Subtotal",
        "vat": "VAT",
        "total": "TOTAL",
        "notes": "NOTES",
        "payments": "PAYMENT DETAILS",
        "generated": "document generated on",
        "page": "Page",
    },
}


def labels(lang: str) -> dict[str, str]:
    return LABELS.get(lang if lang in LABELS else "it")


def _clean(text: str) -> str:
    """fpdf core fonts are latin-1 — strip unsupported glyphs."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u20ac", "EUR")
    return text.encode("latin-1", "replace").decode("latin-1")


def _money(n: float, lang: str = "it") -> str:
    """IT: 1.234,56 · EN: 1,234.56 · always EUR."""
    n = float(n or 0)
    if lang == "en":
        body = f"{n:,.2f}"
    else:
        body = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{body} EUR"


def _tax_rate(doc: dict) -> float:
    """Default IVA 22% when the document has taxable lines but no rate set."""
    rate = doc.get("taxRate")
    if rate is None or rate == "":
        return 22.0
    return float(rate)


class DocPDF(FPDF):
    lang: str = "it"

    def header(self):
        L = labels(self.lang)
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 30, "F")
        self.set_xy(15, 7)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 7, _clean(settings.COMPANY_NAME), ln=1)
        self.set_x(15)
        self.set_font("Helvetica", "", 8)
        line = f"{settings.COMPANY_ADDRESS}  ·  {settings.COMPANY_EMAIL}"
        if settings.COMPANY_VAT_ID:
            line += f"  ·  P.IVA {settings.COMPANY_VAT_ID}"
        self.cell(0, 5, _clean(line), ln=1)
        self.set_text_color(*NAVY)
        self.ln(6)
        self._labels = L  # noqa: SLF001 — used by footer

    def footer(self):
        L = labels(self.lang)
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        stamp = datetime.now().strftime("%d/%m/%Y")
        self.cell(
            0,
            8,
            _clean(f"{settings.COMPANY_NAME}  -  {L['generated']} {stamp}"),
            align="C",
        )


def _label_value(pdf: FPDF, label: str, value: str, y: float | None = None):
    if y is not None:
        pdf.set_y(y)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*GRAY)
    pdf.cell(35, 5, _clean(label), ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(0, 5, _clean(value or "-"))


def _render_document(pdf: DocPDF, doc: dict, kind: str) -> bytes:
    """
    kind: 'proposal' | 'invoice'
    """
    lang = pdf.lang
    L = labels(lang)
    is_invoice = kind == "invoice"
    title = L["invoice"] if is_invoice else L["proposal"]
    number = doc.get("number") or ""
    rate = _tax_rate(doc)

    pdf.add_page()
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, _clean(f"{title}  {number}"), ln=1)

    y_top = pdf.get_y() + 2
    pdf.set_xy(15, y_top)
    issue = doc.get("issueDate") or (doc.get("createdAt") or "")[:10]
    _label_value(pdf, L["date"], issue or "-")
    if is_invoice:
        _label_value(pdf, L["due"], doc.get("dueDate") or "-")
    else:
        _label_value(pdf, L["valid_until"], doc.get("validUntil") or "-")
    _label_value(pdf, L["status"], (doc.get("status") or "").upper())

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, _clean(L["client"]), ln=1)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 6, _clean(doc.get("clientName") or "-"), ln=1)
    pdf.set_font("Helvetica", "", 10)
    if doc.get("clientEmail"):
        pdf.cell(0, 5, _clean(doc.get("clientEmail")), ln=1)

    if doc.get("title"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*GRAY)
        pdf.cell(0, 6, _clean(L["subject"]), ln=1)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 5, _clean(doc.get("title")))

    pdf.ln(3)
    pdf.set_fill_color(*LIGHT)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 8, _clean(L["description"]), border=0, fill=True)
    pdf.cell(25, 8, _clean(L["qty"]), border=0, fill=True, align="R")
    pdf.cell(35, 8, _clean(L["unit_price"]), border=0, fill=True, align="R")
    pdf.cell(35, 8, _clean(L["line_total"]), border=0, fill=True, align="R", ln=1)

    pdf.set_text_color(*DARK)
    pdf.set_font("Helvetica", "", 9)
    for item in doc.get("items") or []:
        name = _clean(item.get("name") or item.get("description") or "-")
        qty = float(item.get("quantity") or 1)
        unit = float(item.get("unitPrice") or 0)
        total = float(item.get("total") or (qty * unit))
        pdf.cell(80, 7, name[:50], border=0)
        pdf.cell(25, 7, f"{qty:g}", border=0, align="R")
        pdf.cell(35, 7, _money(unit, lang), border=0, align="R")
        pdf.cell(35, 7, _money(total, lang), border=0, align="R", ln=1)

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    right = 110
    pdf.set_x(right)
    pdf.cell(40, 6, _clean(L["subtotal"]), align="L")
    pdf.cell(45, 6, _money(float(doc.get("subtotal") or 0), lang), align="R", ln=1)
    pdf.set_x(right)
    pdf.cell(40, 6, _clean(f"{L['vat']} {rate:g}%"), align="L")
    pdf.cell(45, 6, _money(float(doc.get("taxAmount") or 0), lang), align="R", ln=1)
    pdf.set_x(right)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*NAVY)
    pdf.cell(40, 8, _clean(L["total"]), align="L")
    pdf.cell(45, 8, _money(float(doc.get("total") or 0), lang), align="R", ln=1)

    notes = doc.get("notes")
    if notes:
        pdf.ln(4)
        pdf.set_text_color(*GRAY)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, _clean(L["notes"]), ln=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        pdf.multi_cell(0, 5, _clean(notes))

    if settings.COMPANY_IBAN:
        pdf.ln(4)
        pdf.set_text_color(*GRAY)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(0, 5, _clean(L["payments"]), ln=1)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*DARK)
        pdf.cell(0, 5, _clean(f"IBAN {settings.COMPANY_IBAN}"), ln=1)

    return bytes(pdf.output())


def _make_pdf(lang: str) -> DocPDF:
    pdf = DocPDF(format="A4")
    pdf.lang = lang if lang in LABELS else "it"
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_compression(False)
    return pdf


def proposal_pdf(proposal: dict, lang: str = "it") -> bytes:
    return _render_document(_make_pdf(lang), proposal, "proposal")


def invoice_pdf(invoice: dict, lang: str = "it") -> bytes:
    return _render_document(_make_pdf(lang), invoice, "invoice")
