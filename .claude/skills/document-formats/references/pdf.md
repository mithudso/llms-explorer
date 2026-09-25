<!-- hub-reference-banner -->
> **Reference file — part of the `document-formats` hub.** Formerly the standalone `pdf` skill.
> Sibling topics in this family are now reference files under the hubs (`document-formats`) — **not** standalone
> skills. Ignore any "use the X skill" / `related_skills` / SKIP pointers below that name a bare sibling
> skill; load that topic's `references/<name>.md` from the owning hub (see the hub's "Cross-hub map").

---

---
name: pdf
title: "PDF Expert"
version: "1.1.1"
updated: "2026-05-31"
category: developer
tags: [pdf, pdf-lib, pdfkit, pdfmake, jspdf, pypdf, reportlab, weasyprint, fpdf2, pikepdf, pymupdf, pdfplumber, puppeteer, playwright, gotenberg, pdfa, pdfua, ocr, digital-signature, acroform, linearization]
description: "PDF expert — create, parse, manipulate, merge, split, watermark, encrypt, sign, validate, and convert PDF files in Python and Node.js. TRIGGER: user mentions '.pdf', 'PDF generation', 'HTML to PDF', pdf-lib, PDFKit, pdfmake, jsPDF, pypdf, ReportLab, WeasyPrint, fpdf2, pikepdf, PyMuPDF, pdfplumber, camelot, tabula, Puppeteer PDF, Playwright PDF, Gotenberg, PDF/A, PDF/UA, pdftotext, ghostscript, qpdf, pdftk, mutool, AcroForm, PAdES, veraPDF, OCR, linearized PDF; or user wants to produce reports, invoices, or documents as PDF; or user needs to extract text or tables from PDFs, fill PDF forms, add digital signatures, validate PDF/A compliance, or optimize PDF performance. SKIP: Word documents (.docx) — use docx skill; spreadsheets (.xlsx) — use xlsx skill; general image processing unrelated to PDF."
whenToUse:
  - "generate a PDF report, invoice, or document from Python or Node.js"
  - "convert HTML/CSS to PDF (Puppeteer, Playwright, WeasyPrint, Gotenberg)"
  - "extract text or tables from an existing PDF"
  - "merge, split, watermark, or rotate PDF pages"
  - "fill or flatten AcroForm fields"
  - "encrypt, decrypt, or digitally sign a PDF (PAdES)"
  - "validate or convert to PDF/A or PDF/UA"
  - "linearize or compress a PDF for web delivery"
related_skills: [docx, xlsx, pptx]
---

<context>
# PDF Expert Reference

**Contents**
1. Overview
2. Core Concepts
3. Generation (by language/runtime)
4. Parsing and Text Extraction
5. Security
6. Archival and Compliance
7. Forms
8. Performance
9. CLI Tools
10. Anti-Patterns
11. Troubleshooting
12. References


## Overview

PDF (Portable Document Format) is a file format standardized as ISO 32000, designed to present documents consistently across hardware, operating systems, and software. The current version, PDF 2.0 (ISO 32000-2:2020), extends earlier specifications with native UTF-8 text support, improved structure elements for accessibility (Aside, Hn, Title, FENote, Sub, Em, Strong), black-point compensation for color rendering, and standardized rounding rules for color value calculations. The standard is available at no cost from the PDF Association and spans approximately 1,000 pages.

PDF documents contain eight fundamental object types — booleans, integers/reals, strings, names, arrays, dictionaries, streams, and null — assembled into a four-section physical structure: header, body, cross-reference table (xref), and trailer. Unlike PostScript (a Turing-complete programming language), PDF is a structured binary description language. Content on a page is encoded as a stream of operators; the PDF engine executes those operators in order, painting text and graphics onto an abstract canvas that is later rasterized for display or print.

The ecosystem has matured into dozens of production-ready libraries across Python and JavaScript/Node.js, plus a rich set of CLI tools. Choosing the right tool requires understanding the three distinct workloads: generation (creating new PDFs from code), parsing/extraction (reading data out of existing PDFs), and manipulation (modifying an existing PDF without full re-render). Each workload has different performance characteristics, dependency weights, and accuracy trade-offs, covered in depth below.

---

## Core Concepts

### PDF Structure and Internals

A valid PDF file has four physical sections in order:

```
%PDF-1.7                           ← Header: version string
%âãÏÓ                             ← Optional 4-byte comment (signals binary content)

1 0 obj                            ← Body: numbered indirect objects
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

xref                               ← Cross-reference table
0 4
0000000000 65535 f                 ← Free object (always first)
0000000009 00000 n                 ← Object 1 at byte offset 9
0000000058 00000 n
0000000115 00000 n

trailer                            ← Trailer dictionary
<< /Size 4 /Root 1 0 R >>
startxref
203                                ← Byte offset of xref table
%%EOF
```

**Cross-reference streams** (PDF 1.5+) replace the ASCII xref table with a compressed binary stream, dramatically reducing file size for large documents.

**Incremental updates** append a new body section, new xref, and new trailer to the end of a file without rewriting it. This is how digital signatures are applied — the signed byte range is frozen, and the signature dictionary is appended.

**Object types quick reference:**

| Type | Syntax example | Notes |
|------|---------------|-------|
| Boolean | `true` / `false` | |
| Integer | `42` | |
| Real | `3.14` | |
| String | `(Hello)` or `<48656c6c6f>` | Literal or hex |
| Name | `/Type` | Always starts with `/` |
| Array | `[1 2 3]` | |
| Dictionary | `<< /Key value >>` | |
| Stream | `<< /Length 42 >> stream...endstream` | Binary data |
| Null | `null` | |
| Indirect ref | `2 0 R` | Points to object 2, generation 0 |

### PDF Versions and Standards

| Version | ISO equivalent | Key additions |
|---------|---------------|---------------|
| PDF 1.0–1.3 | Pre-ISO | Basic structure, Type 1 fonts, RC4-40 encryption |
| PDF 1.4 | — | Transparency, RC4-128 encryption (PDF/A-1 base) |
| PDF 1.5 | — | Cross-reference streams, optional-content groups |
| PDF 1.6 | — | AES-128 encryption, 3D annotations |
| PDF 1.7 | ISO 32000-1:2008 | AES-256, XFA forms (PDF/A-2 and PDF/A-3 base) |
| PDF 2.0 | ISO 32000-2:2020 | UTF-8 text strings, enhanced accessibility tags, unencrypted wrappers |

PDF/A, PDF/UA, PDF/X (print), and PDF/E (engineering) are all profiles on top of the base specification. They add restrictions or requirements rather than new features.

### Content Streams and Rendering

A page's visual content lives in its content stream. Operators are written as PostScript-style tokens:

```
BT                          % Begin text block
/F1 12 Tf                   % Set font F1 at 12pt
72 720 Td                   % Move to (72, 720) in user units
(Hello, PDF!) Tj            % Show string
ET                          % End text block

q                           % Save graphics state
0.5 0 0 0.5 100 100 cm      % Scale/translate CTM
/Im1 Do                     % Paint image XObject named Im1
Q                           % Restore graphics state
```

**Text rendering modes** (Tr operator, integer 0–7):

| Value | Mode | Usage |
|-------|------|-------|
| 0 | Fill | Normal visible text |
| 1 | Stroke | Outlined text |
| 2 | Fill then stroke | |
| 3 | Invisible | Searchable hidden text (PDF OCR layer) |
| 4–7 | Clipping variants | Clip paths from glyph outlines |

**Important font facts:**
- Fonts must be **embedded** for reliable cross-platform rendering
- Variable fonts must be instantiated to a static instance before embedding
- Subset embedding reduces file size but can break extraction if ToUnicode CMap is missing

---

## Generation (by language/runtime)

### Node.js Libraries

#### PDFKit — Low-level canvas API, streaming-first

```javascript
const PDFDocument = require('pdfkit');
const fs = require('fs');

const doc = new PDFDocument({ margin: 50, size: 'A4' });
doc.pipe(fs.createWriteStream('output.pdf'));

// Text
doc.font('Helvetica-Bold').fontSize(24).text('Invoice', { align: 'center' });
doc.moveDown();
doc.font('Helvetica').fontSize(12).text('Bill To: Acme Corp');

// Custom font
doc.registerFont('Brand', 'fonts/Brand.otf');
doc.font('Brand').fontSize(18).text('Branded heading');

// Images
doc.image('logo.png', 50, 50, { width: 150 });
doc.image('photo.jpg', { fit: [200, 200], align: 'center', valign: 'center' });

// Vector graphics
doc.rect(50, 200, 400, 100).fillAndStroke('#e0e0e0', '#333333');
doc.circle(250, 400, 50).fill('#ff0000');

// Encryption and permissions
const secureDoc = new PDFDocument({
  userPassword: 'user123',
  ownerPassword: 'owner456',
  permissions: {
    printing: 'lowResolution',
    modifying: false,
    copying: false,
    annotating: true,
    fillingForms: true,
    contentAccessibility: true,
    documentAssembly: false,
  },
});

doc.end(); // MUST call end() to finalize the stream

// Express.js streaming
app.get('/pdf', (req, res) => {
  const doc = new PDFDocument();
  res.setHeader('Content-Type', 'application/pdf');
  res.setHeader('Content-Disposition', 'inline; filename="report.pdf"');
  doc.pipe(res);
  doc.fontSize(20).text('Dynamic Report');
  doc.end();
});
```

#### pdf-lib — TypeScript-first, modify existing PDFs

```javascript
import { PDFDocument, StandardFonts, rgb, degrees, PageSizes } from 'pdf-lib';
import fs from 'fs/promises';

// Create from scratch
async function createPDF() {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
  const page = pdfDoc.addPage(PageSizes.A4);
  const { width, height } = page.getSize();
  page.drawText('Hello, pdf-lib!', {
    x: 50, y: height - 80, size: 30, font, color: rgb(0, 0.53, 0.71),
  });
  await fs.writeFile('output.pdf', await pdfDoc.save());
}

// Merge PDFs
async function mergePDFs(paths) {
  const merged = await PDFDocument.create();
  for (const path of paths) {
    const src = await PDFDocument.load(await fs.readFile(path));
    const pages = await merged.copyPages(src, src.getPageIndices());
    pages.forEach(p => merged.addPage(p));
  }
  return merged.save();
}

// Add watermark
async function addWatermark(inputPath, watermarkText) {
  const pdfDoc = await PDFDocument.load(await fs.readFile(inputPath));
  const font = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
  pdfDoc.getPages().forEach(page => {
    const { width, height } = page.getSize();
    page.drawText(watermarkText, {
      x: width / 4, y: height / 2, size: 60, font,
      color: rgb(0.8, 0.8, 0.8), opacity: 0.3, rotate: degrees(45),
    });
  });
  return pdfDoc.save();
}

// Fill AcroForm fields
async function fillForm(templatePath, fieldValues) {
  const pdfDoc = await PDFDocument.load(await fs.readFile(templatePath));
  const form = pdfDoc.getForm();
  form.getTextField('firstName').setText(fieldValues.firstName);
  form.getCheckBox('agree').check();
  form.getDropdown('country').select(fieldValues.country);
  form.getRadioGroup('paymentMethod').select(fieldValues.payment);
  form.flatten();
  return pdfDoc.save();
}

// Extract page range
async function extractPages(inputPath, startPage, endPage) {
  const src = await PDFDocument.load(await fs.readFile(inputPath));
  const out = await PDFDocument.create();
  const indices = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage - 1 + i);
  const pages = await out.copyPages(src, indices);
  pages.forEach(p => out.addPage(p));
  return out.save();
}
```

#### pdfmake — Declarative document model

```javascript
const PdfPrinter = require('pdfmake');

const fonts = {
  Roboto: {
    normal: 'fonts/Roboto-Regular.ttf',
    bold: 'fonts/Roboto-Medium.ttf',
    italics: 'fonts/Roboto-Italic.ttf',
    bolditalics: 'fonts/Roboto-MediumItalic.ttf',
  },
};

const printer = new PdfPrinter(fonts);

const docDefinition = {
  pageSize: 'A4',
  pageMargins: [40, 60, 40, 60],
  header: { text: 'ACME Corp', alignment: 'right', margin: [0, 20, 40, 0] },
  footer: (currentPage, pageCount) => ({
    text: `${currentPage} / ${pageCount}`, alignment: 'center',
  }),
  content: [
    { text: 'Invoice #1234', style: 'header' },
    {
      table: {
        headerRows: 1,
        widths: ['*', 'auto', 100, 80],
        body: [
          ['Item', 'Qty', 'Unit Price', 'Total'],
          ['Widget A', '2', '$10.00', '$20.00'],
        ],
      },
      layout: 'lightHorizontalLines',
    },
  ],
  styles: {
    header: { fontSize: 22, bold: true, margin: [0, 0, 0, 10] },
  },
};

const pdfDoc = printer.createPdfKitDocument(docDefinition);
pdfDoc.pipe(fs.createWriteStream('invoice.pdf'));
pdfDoc.end();
```

#### jsPDF — Browser-first, dual environment

```javascript
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';

const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
doc.setFontSize(22);
doc.text('Report Title', 105, 20, { align: 'center' });

doc.autoTable({
  head: [['Name', 'Email', 'Role']],
  body: [['Alice', 'alice@example.com', 'Admin']],
  startY: 50,
  theme: 'grid',
  headStyles: { fillColor: [41, 128, 185] },
});

doc.save('report.pdf');
```

### Python Libraries

#### fpdf2 — Lightweight, pure Python, PDF/A capable

```python
from fpdf import FPDF, FontFace

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", style="B", size=15)
        self.cell(0, 10, "Monthly Report", align="C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", style="I", size=8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

pdf = PDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("helvetica", size=12)

# Table with context manager
headings_style = FontFace(emphasis="BOLD", color=255, fill_color=(41, 128, 185))
with pdf.table(col_widths=(60, 40, 50, 40), headings_style=headings_style) as table:
    row = table.row()
    for header in ("Item", "Qty", "Unit Price", "Total"):
        row.cell(header)

# PDF/A compliance
pdf_a = FPDF(enforce_compliance="PDF/A-3B")
pdf_a.set_lang("en-US")
pdf.output("report.pdf")
```

#### ReportLab — Production-grade, maximum control

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

doc = SimpleDocTemplate("report.pdf", pagesize=A4,
    topMargin=20*mm, bottomMargin=20*mm, leftMargin=20*mm, rightMargin=20*mm)
styles = getSampleStyleSheet()
story = []

story.append(Paragraph("Monthly Report", styles['Heading1']))
story.append(Spacer(1, 10*mm))

table_data = [["Item", "Qty", "Price"]] + data_rows
t = Table(table_data, colWidths=[80*mm, 30*mm, 40*mm])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2980b9")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
]))
story.append(t)
doc.build(story)
```

#### WeasyPrint — HTML/CSS to PDF

```python
from weasyprint import HTML, CSS

html = HTML(string="<h1>Report</h1><table>...</table>")
css = CSS(string="@page { size: A4; margin: 15mm; }")
html.write_pdf("output.pdf", stylesheets=[css])

# From URL or file
HTML(url="https://example.com/report").write_pdf("webpage.pdf")
HTML(filename="report.html").write_pdf("report.pdf")
```

#### pikepdf — Low-level PDF surgery (based on QPDF)

```python
import pikepdf

# Linearize
with pikepdf.open("input.pdf") as pdf:
    pdf.save("linearized.pdf", linearize=True)

# Compress
with pikepdf.open("input.pdf") as pdf:
    pdf.save("compressed.pdf", compress_streams=True,
             object_stream_mode=pikepdf.ObjectStreamMode.generate)

# Encrypt (AES-256)
with pikepdf.open("input.pdf") as pdf:
    pdf.save("encrypted.pdf", encryption=pikepdf.Encryption(
        user="userpass", owner="ownerpass", R=6,
        allow=pikepdf.Permissions(print_lowres=True, extract=False)))

# Merge
out = pikepdf.new()
for path in ["doc1.pdf", "doc2.pdf"]:
    with pikepdf.open(path) as src:
        out.pages.extend(src.pages)
out.save("merged.pdf")

# Edit metadata
with pikepdf.open("input.pdf", allow_overwriting_input=True) as pdf:
    with pdf.open_metadata() as meta:
        meta["{http://purl.org/dc/elements/1.1/}title"] = "New Title"
    pdf.save("input.pdf")
```

### HTML-to-PDF Conversion

#### Puppeteer

```javascript
const puppeteer = require('puppeteer');

async function htmlToPDF(htmlContent, outputPath) {
  const browser = await puppeteer.launch({ headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
  await page.pdf({
    path: outputPath, format: 'A4', printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size:10px;width:100%;text-align:right;padding:0 20px;"><span class="title"></span></div>',
    footerTemplate: '<div style="font-size:10px;width:100%;text-align:center;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
    margin: { top: '20mm', right: '15mm', bottom: '20mm', left: '15mm' },
  });
  await browser.close();
}
```

#### Playwright — Preferred modern alternative

```javascript
const { chromium } = require('playwright');

async function generatePDF(htmlOrUrl, outputPath) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  if (htmlOrUrl.startsWith('http')) {
    await page.goto(htmlOrUrl, { waitUntil: 'networkidle' });
  } else {
    await page.setContent(htmlOrUrl, { waitUntil: 'networkidle' });
  }
  await page.emulateMedia({ media: 'print' });
  await page.pdf({
    path: outputPath, format: 'A4', printBackground: true,
    tagged: true, outline: true,
    margin: { top: '35mm', bottom: '30mm', left: '15mm', right: '15mm' },
  });
  await browser.close();
}
```

#### Gotenberg — Dockerized HTTP API

```bash
docker run --rm -p 3000:3000 gotenberg/gotenberg:8

curl -s -X POST 'http://localhost:3000/forms/chromium/convert/html' \
  -F 'files=@index.html' -F 'printBackground=true' -o output.pdf

curl -s -X POST 'http://localhost:3000/forms/pdfengines/merge' \
  -F 'files=@doc1.pdf' -F 'files=@doc2.pdf' -o merged.pdf

curl -s -X POST 'http://localhost:3000/forms/pdfengines/convert' \
  -F 'files=@input.pdf' -F 'pdfa=PDF/A-2b' -o pdfa.pdf
```

**CSS print styles for HTML-to-PDF:**

```css
@media print {
  body { font-size: 11pt; color: #000; }
  .no-print { display: none; }
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

@page { size: A4; margin: 20mm 15mm; }
@page :first { margin-top: 30mm; }

.chapter { break-before: page; }
.figure  { break-inside: avoid; }
p { orphans: 3; widows: 3; }
```

---

## Parsing and Text Extraction

### Node.js

#### pdf-parse — Simplest text extraction

```javascript
const pdfParse = require('pdf-parse');
const fs = require('fs');

async function extractText(pdfPath) {
  const data = await pdfParse(fs.readFileSync(pdfPath), {
    max: 0,
    pagerender: async (pageData) => {
      const textContent = await pageData.getTextContent({ normalizeWhitespace: true });
      return textContent.items.map(item => item.str).join(' ');
    },
  });
  return { text: data.text, numpages: data.numpages, info: data.info };
}
```

#### pdfjs-dist — Full PDF.js in Node.js, positional extraction

```javascript
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.mjs';

async function extractTextWithPositions(pdfPath) {
  const data = new Uint8Array(await fs.readFile(pdfPath));
  const pdfDocument = await pdfjsLib.getDocument({ data }).promise;
  const result = [];
  for (let pageNum = 1; pageNum <= pdfDocument.numPages; pageNum++) {
    const page = await pdfDocument.getPage(pageNum);
    const textContent = await page.getTextContent();
    const viewport = page.getViewport({ scale: 1.0 });
    const pageItems = textContent.items.map(item => ({
      text: item.str,
      x: item.transform[4],
      y: viewport.height - item.transform[5],
      width: item.width, height: item.height,
    }));
    result.push({ page: pageNum, items: pageItems });
  }
  return result;
}
```

### Python

#### pypdf — Pure Python, text + manipulation

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
if reader.is_encrypted:
    reader.decrypt("password")

full_text = ""
for page in reader.pages:
    full_text += page.extract_text(extraction_mode="layout")
```

#### pdfplumber — Rich extraction with bounding boxes

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        words = page.extract_words()
        tables = page.extract_tables()
        region = page.crop((0, 100, 300, 400))
        text_in_region = region.extract_text()
```

#### PyMuPDF / pymupdf4llm — Fastest extraction, LLM-ready

```python
import fitz
import pymupdf4llm

doc = fitz.open("document.pdf")
for page in doc:
    text = page.get_text("text")
    blocks = page.get_text("blocks")
    html = page.get_text("html")

# For LLM / RAG pipelines
md = pymupdf4llm.to_markdown("document.pdf")
chunks = pymupdf4llm.to_markdown("document.pdf", page_chunks=True)
```

### Table Extraction

#### camelot — Best for text-based PDFs with visible grid lines

```python
import camelot

tables = camelot.read_pdf("report.pdf", flavor="lattice", pages="1-5")
for table in tables:
    print(f"Accuracy: {table.accuracy:.1f}%")
    df = table.df
tables[0].to_csv("table.csv")
```

#### tabula-py — Java-powered, good for complex layouts

```python
import tabula
dfs = tabula.read_pdf("report.pdf", pages="all", multiple_tables=True)
dfs = tabula.read_pdf("report.pdf", pages=1, area=[100, 50, 500, 550], lattice=True)
```

### OCR Integration

```javascript
// Tesseract.js (Node.js)
const Tesseract = require('tesseract.js');
const { data: { text } } = await Tesseract.recognize('scanned.png', 'eng');
```

```python
# pytesseract + pdf2image (Python)
import pytesseract
from pdf2image import convert_from_path

pages = convert_from_path("scanned.pdf", dpi=300)
for page_img in pages:
    text = pytesseract.image_to_string(page_img.convert("L"), lang="eng")
```

---

## Security

### Encryption

| Revision | Algorithm | Key bits | Notes |
|---------|-----------|----------|-------|
| R2 | RC4 | 40 | Trivially broken, avoid |
| R3 | RC4 | 128 | Weak, avoid |
| R4 | AES | 128 | Acceptable minimum |
| R5/R6 | AES | 256 | Current standard (PDF 2.0) |

### Digital Signatures (PAdES)

| Level | Name | Embedded |
|-------|------|----------|
| PAdES-B-B | Basic | Signer cert only |
| PAdES-B-T | With Timestamp | Trusted timestamp token |
| PAdES-B-LT | Long-Term | All certs + revocation data |
| PAdES-B-LTA | Long-Term with Archive | Renewable archive timestamp |

```python
# PyHanko — PAdES signatures
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign.signers.pdf_signer import PdfSignatureMetadata

signer = signers.SimpleSigner.load_pkcs12(pfx_file="signer.p12", passphrase=b"pass")
with open("input.pdf", "rb") as inf:
    w = IncrementalPdfFileWriter(inf)
    meta = PdfSignatureMetadata(field_name="Signature1", location="NYC", reason="Approved")
    with open("signed.pdf", "wb") as outf:
        signers.sign_pdf(w, signature_meta=meta, signer=signer, output=outf)
```

### Permissions

PDF permissions are stored as a 32-bit flags integer. **Note:** PDF permissions enforcement is advisory — they are trivially bypassed by tools like qpdf.

---

## Archival and Compliance

### PDF/A Variants

| Standard | Base PDF | Transparency | Embedded Files |
|----------|----------|--------------|---------------|
| PDF/A-1b | PDF 1.4 | No | No |
| PDF/A-2b | PDF 1.7 | Yes | PDF/A only |
| PDF/A-3b | PDF 1.7 | Yes | Any format |
| PDF/A-4 | PDF 2.0 | Yes | Any format |

**Conformance levels:** `b` (visual fidelity), `u` (unicode-mapped text), `a` (full tagged structure)

**Mandatory requirements:** All fonts embedded, no encryption, no JavaScript, no external content references, device-independent color spaces, XMP metadata.

```bash
# Ghostscript conversion to PDF/A-2b
gs -dPDFA=2 -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
   -sProcessColorModel=DeviceRGB -dCompatibilityLevel=1.7 \
   -dPDFACompatibilityPolicy=1 -sOutputFile=output_pdfa.pdf input.pdf
```

### PDF/UA Accessibility

Requires: document tagged with semantic structure tree, all images have alt text, logical reading order, language specified, document title set, table headers properly associated.

### Validation — veraPDF

```bash
verapdf --flavour 2b document.pdf
verapdf --flavour 2b --format json document.pdf > report.json
verapdf --flavour 0 document.pdf  # auto-detect
```

---

## Forms

### AcroForms

| Type | PDF `/FT` | Description |
|------|----------|-------------|
| Text | `/Tx` | Single or multi-line text input |
| Checkbox | `/Btn` with `/Ff` 16384 | Toggle checkbox |
| Radio | `/Btn` with `/Ff` 49152 | Exclusive radio group |
| Dropdown | `/Ch` with `/Ff` 131072 | Dropdown with optional freetext |
| List | `/Ch` | Scrolling list |
| Signature | `/Sig` | Digital signature field |

```python
# Inspect form fields
from pypdf import PdfReader
reader = PdfReader("form.pdf")
for name, field in reader.get_fields().items():
    print(f"{name}: type={field.get('/FT')}, value={field.get('/V')}")
```

### Flattening

```javascript
// pdf-lib
const form = pdfDoc.getForm();
form.flatten();  // Renders all field appearances into page content
```

```python
# pypdf
writer.update_page_form_field_values(writer.pages[0], {}, flatten=True)
```

---

## Performance

### Linearization ("Fast Web View")

```bash
qpdf --linearize input.pdf output.pdf
```

```python
import pikepdf
with pikepdf.open("input.pdf") as pdf:
    pdf.save("linear.pdf", linearize=True)
```

**When to linearize:** PDFs served over HTTP, 5+ pages, cloud storage direct serving. **When not to:** download-only, intermediate processing, small docs.

### Compression with Ghostscript

```bash
gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
   -dPDFSETTINGS=/screen -sOutputFile=small.pdf input.pdf
# Presets: /screen (72dpi), /ebook (150dpi), /printer (300dpi), /prepress (no downsampling)
```

### Large Document Strategies

```python
# Process in chunks
from pypdf import PdfReader, PdfWriter
reader = PdfReader("huge.pdf")
for i in range(0, len(reader.pages), 50):
    writer = PdfWriter()
    for page in reader.pages[i:i+50]:
        writer.add_page(page)
    with open(f"chunk_{i//50}.pdf", "wb") as f:
        writer.write(f)
```

---

## CLI Tools

### poppler-utils

```bash
pdftotext input.pdf -                    # Extract text to stdout
pdftotext -layout input.pdf             # Preserve visual layout
pdfinfo input.pdf                        # Document metadata
pdfimages -all input.pdf output/images  # Extract embedded images
pdfseparate input.pdf page_%d.pdf       # Split into pages
pdfunite doc1.pdf doc2.pdf merged.pdf   # Merge
pdffonts input.pdf                       # Font audit
```

### qpdf

```bash
qpdf --check input.pdf                                  # Validate
qpdf --linearize input.pdf output.pdf                   # Fast web view
qpdf --password=pass --decrypt input.pdf output.pdf     # Decrypt
qpdf --encrypt user owner 256 -- input.pdf output.pdf   # AES-256
qpdf --split-pages input.pdf page_%d.pdf                # Split
qpdf --pages doc1.pdf 1-3 doc2.pdf 5,7 -- /dev/null m.pdf  # Merge selection
qpdf --rotate=90 input.pdf rotated.pdf                  # Rotate
qpdf --json input.pdf                                   # JSON inspection
```

### Ghostscript

```bash
# Compress
gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -sOutputFile=out.pdf in.pdf
# To images
gs -dBATCH -dNOPAUSE -sDEVICE=png16m -r300 -sOutputFile=page_%04d.png input.pdf
# Repair corrupted
gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile=repaired.pdf corrupt.pdf
```

### pdftk

```bash
pdftk doc1.pdf doc2.pdf cat output merged.pdf            # Merge
pdftk input.pdf burst output/page_%04d.pdf               # Split
pdftk input.pdf cat 1-endeast output rotated.pdf         # Rotate 90 CW
pdftk form.pdf fill_form data.fdf output filled.pdf      # Fill form
pdftk filled.pdf output flat.pdf flatten                  # Flatten
pdftk input.pdf attach_files data.csv output attached.pdf # Attach file
```

### mutool (MuPDF)

```bash
mutool draw -F txt input.pdf > text.txt      # Extract text
mutool draw -r 150 -o page_%d.png input.pdf  # To images
mutool merge -o merged.pdf doc1.pdf doc2.pdf  # Merge
mutool clean -l input.pdf linear.pdf          # Linearize
mutool clean -gggg -z input.pdf small.pdf     # Max compress
```

---

## Anti-Patterns

1. **Not embedding fonts** — Files display correctly only on machines with those fonts
2. **Ignoring text layer vs image PDF** — Scanned PDFs return empty text, not an error; check with `pdffonts`
3. **Using XFA forms** — Deprecated in PDF 2.0, unsupported by most tools; use AcroForms
4. **Missing `end()`/`close()`** — Produces truncated files with "%%EOF missing" errors
5. **Synchronous PDF generation in request handlers** — Blocks event loop; use workers or Gotenberg
6. **PDF/A conversion without validation** — Always validate with veraPDF after conversion
7. **Relying on PDF permissions for security** — Advisory only, trivially bypassed
8. **Using PyPDF2 (deprecated)** — Use `pypdf` instead
9. **Non-linearized PDFs for web delivery** — Forces full download before first page renders
10. **Assuming text extraction order = reading order** — PDF is object-order, not visual-reading-order
11. **Modifying signed PDFs without incremental updates** — Breaks all existing signatures
12. **Insufficient margins with displayHeaderFooter** — Set `margin.top >= 35mm`

---

## Troubleshooting

### Text extracts as empty or garbage
- Run `pdffonts input.pdf` — check "emb" column for missing fonts
- If not selectable in viewer → scanned image PDF → apply OCR
- If garbled → broken ToUnicode CMap → try PyMuPDF's `get_text("rawdict")`

### PDF/A conversion produces non-compliant output
- Check stderr for errors, validate with veraPDF
- If transparency errors → flatten first with `-dCompatibilityLevel=1.3`

### Playwright/Puppeteer generates blank pages
- Wait for fonts: `await page.evaluate(() => document.fonts.ready)`
- Use `waitUntil: 'networkidle0'`
- Check `@media print` CSS rules

### Form fill produces invisible text
- Missing appearance stream → call `form.updateFieldAppearances(font)` in pdf-lib
- Set `auto_regenerate=False` in pypdf

### Signatures invalid after modification
- Use `IncrementalPdfFileWriter` (PyHanko) — never rewrite signed files

### PDF testing: detecting visual regressions
```bash
pdftoppm -r 150 reference.pdf ref_page
pdftoppm -r 150 output.pdf out_page
compare -metric AE ref_page-01.ppm out_page-01.ppm diff.ppm
```

---

## References

- [PDF 2.0 (ISO 32000-2:2020) — PDF Association](https://pdfa.org/resource/iso-32000-2/)
- [PDF File Structure — Mapsoft](https://mapsoft.com/posts/pdf-structure.html)
- [PDF Syntax 101 — Nutrient](https://www.nutrient.io/blog/pdf-syntax-101/)
- [PDFKit documentation](https://pdfkit.org/)
- [pdf-lib official site](https://pdf-lib.js.org/)
- [pdfmake documentation](https://pdfmake.github.io/docs/0.1/document-definition-object/)
- [jsPDF + autotable](https://github.com/simonbengtsson/jsPDF-AutoTable)
- [fpdf2 documentation](https://py-pdf.github.io/fpdf2/index.html)
- [ReportLab documentation](https://docs.reportlab.com/)
- [pypdf documentation](https://pypdf.readthedocs.io/)
- [pikepdf documentation](https://pikepdf.readthedocs.io/)
- [PyMuPDF documentation](https://pymupdf.readthedocs.io/)
- [pymupdf4llm](https://pymupdf.io/4llm)
- [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- [Camelot documentation](https://camelot-py.readthedocs.io/)
- [tabula-py PyPI](https://pypi.org/project/tabula-py/)
- [Playwright PDF API](https://playwright.dev/docs/api/class-page)
- [Gotenberg official site](https://gotenberg.dev/)
- [PDF/A compliance guide — PDF4.dev](https://pdf4.dev/blog/pdf-a-compliance-guide)
- [veraPDF official site](https://verapdf.org/home/)
- [PDF accessibility guide — TestParty](https://testparty.ai/blog/pdf-accessibility-guide)
- [PyHanko documentation](https://pyhanko.readthedocs.io/)
- [PDF linearization — Nutrient](https://www.nutrient.io/blog/linearized-pdf/)
- [qpdf documentation](https://qpdf.readthedocs.io/en/stable/cli.html)
- [Ghostscript documentation](https://ghostscript.readthedocs.io/)
- [poppler-utils — freedesktop.org](https://poppler.freedesktop.org/)
- [Tesseract.js](https://tesseract.projectnaptha.com/)
- [WeasyPrint](https://weasyprint.org/)
- [CSS print styles — PDF4.dev](https://pdf4.dev/blog/css-print-styles-pdf-guide)
</context>
