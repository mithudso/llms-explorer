User provided text directly — I'll compress inline following the strict rules.

<!-- hub-reference-banner -->
> **Reference file — part of the `document-formats` hub.** Formerly standalone `pptx` skill.
> Sibling topics = reference files under hubs (`document-formats`) — **not** standalone skills. Ignore "use the X skill" / `related_skills` / SKIP pointers naming bare sibling skills; load `references/<name>.md` from owning hub (see hub's "Cross-hub map").

---

---
name: pptx
version: "1.1.0"
updated: "2026-05-29"
category: developer
tags: [pptx, powerpoint, presentation, slides, openxml, pptxgenjs, python-pptx, report-generation, document-generation, libreoffice]
description: "PowerPoint (.pptx) expert — create, read, edit, and manipulate presentations programmatically using PptxGenJS (Node.js) and python-pptx (Python). TRIGGER: user mentions 'PowerPoint', 'presentation', 'slides', 'deck', '.pptx'; wants to generate slide decks programmatically; build data-driven presentations or automate report generation into slide format; extract content from .pptx files; work with slide masters, layouts, or templates; add charts, tables, or images to slides; convert presentations to PDF; user asks for a 'deck', 'presentation', 'slides', or 'pitch' as a .pptx file. SKIP: Google Slides API, Keynote, LibreOffice Impress API (unless converting .pptx), or general document generation where slides are not the deliverable."
related_skills: [docx, xlsx, pdf]
license: Proprietary
---

# Programmatic PowerPoint (.pptx) Creation, Reading, and Manipulation

**Contents**
1. Overview
2. Quick Reference
3. File Format Internals (OpenXML / PresentationML)
4. Decision Tree: Which Library to Use
5. Libraries and Tools
6. Practical Patterns
7. Anti-Patterns and Pitfalls
8. Troubleshooting
9. Integration Patterns for Automated Reporting
10. References


## Overview

.pptx = ZIP archive of XML (OOXML/PresentationML, ECMA-376, ISO/IEC 29500). Node.js + Python libs provide high-level APIs — no PowerPoint install needed.

## Quick Reference

| Task | Node.js | Python |
|------|---------|--------|
| Create from scratch | PptxGenJS | python-pptx |
| Template-based generation | pptx-automizer | python-pptx |
| Read/extract content | pptx-automizer, unzip+XML | python-pptx |
| PDF conversion | LibreOffice headless | LibreOffice headless / comtypes (Windows) |
| Commercial (full-featured) | Aspose.Slides for Node.js | Aspose.Slides for Python |

---

## File Format Internals (OpenXML / PresentationML)

### ZIP Container Structure

```
presentation.pptx (ZIP archive)
├── [Content_Types].xml          # MIME type registry for all parts
├── _rels/
│   └── .rels                    # Package-level relationships
├── ppt/
│   ├── presentation.xml         # Root presentation part (slide list, sizes)
│   ├── _rels/
│   │   └── presentation.xml.rels  # Relationships to slides, masters, themes
│   ├── slides/
│   │   ├── slide1.xml           # Individual slide content (<p:sld>)
│   │   ├── slide2.xml
│   │   └── _rels/
│   │       ├── slide1.xml.rels  # Slide-to-layout relationship
│   │       └── slide2.xml.rels
│   ├── slideMasters/
│   │   └── slideMaster1.xml     # Master slide (<p:sldMaster>)
│   ├── slideLayouts/
│   │   ├── slideLayout1.xml     # Layout definitions (<p:sldLayout>)
│   │   └── slideLayout2.xml
│   ├── theme/
│   │   └── theme1.xml           # Color schemes, fonts, effects
│   ├── media/
│   │   ├── image1.png           # Embedded images
│   │   └── image2.jpg
│   ├── charts/
│   │   └── chart1.xml           # Embedded chart definitions
│   ├── notesMaster/
│   ├── notesSlides/
│   └── presProps.xml            # Presentation properties
└── docProps/
    ├── app.xml                  # Application metadata
    └── core.xml                 # Dublin Core metadata (author, title)
```

### Key Concepts

- **[Content_Types].xml**: Maps parts to MIME types. Update when adding new part types.
- **Relationship files (.rels)**: Connect parts via `rId` references. Each source part has `_rels/<name>.rels`.
- **Slide hierarchy**: Master → Layout → Slide. Properties inherit down (master = defaults, layout overrides, slide overrides further). Slide refs layout via relationship; layout refs master.
- **Placeholders**: Typed containers (title, body, date, footer, slide number) inherited master→layout→slide. Accessed by `idx`, not position.
- **EMU (English Metric Units)**: Internal unit. 1 inch = 914400 EMU. 1 cm = 360000 EMU. 1 pt = 12700 EMU.

---

## Decision Tree: Which Library to Use

```
Need to generate .pptx?
├── Using Node.js / JavaScript?
│   ├── Creating slides from scratch (data-driven)?
│   │   └── PptxGenJS (best API, zero deps, works in browser too)
│   ├── Starting from existing branded .pptx template?
│   │   └── pptx-automizer (reads/merges real .pptx templates, wraps PptxGenJS for new elements)
│   └── Need advanced features (animations, transitions, SmartArt)?
│       └── Aspose.Slides for Node.js (commercial)
├── Using Python?
│   ├── Any use case (read, write, template-based)?
│   │   └── python-pptx (mature, well-documented, template-first idiom)
│   └── Need unsupported chart types or animations?
│       └── Aspose.Slides for Python (commercial) or SlideForge API
└── Need PDF output only (no editable .pptx)?
    └── Generate .pptx first, then convert via LibreOffice headless
```

---

## Libraries and Tools

### PptxGenJS (Node.js) -- Primary Recommendation

**Version**: 4.0.1 | **Weekly downloads**: ~1.8M | **License**: MIT
**GitHub**: https://github.com/gitbrent/PptxGenJS

Zero deps. Works in Node.js, browsers, React, Vite, Electron. Dual ESM/CJS. Ships TypeScript defs (`types/index.d.ts`).

#### Installation
```bash
npm install pptxgenjs
```

#### Core API Pattern
```javascript
import PptxGenJS from 'pptxgenjs';

const pptx = new PptxGenJS();
pptx.layout = 'LAYOUT_WIDE';  // 13.33 x 7.5 inches
pptx.author = 'Report Generator';
pptx.title = 'Monthly Report';

// Define a master slide
pptx.defineSlideMaster({
  title: 'MASTER_SLIDE',
  background: { color: 'FFFFFF' },
  objects: [
    { rect: { x: 0, y: 6.9, w: '100%', h: 0.6, fill: { color: '003B75' } } },
    { text: { text: 'Company Name', options: { x: 0.5, y: 7.0, w: 4, h: 0.4, color: 'FFFFFF', fontSize: 10 } } },
    { image: { x: 11.0, y: 0.2, w: 2.0, h: 0.8, path: './logo.png' } }
  ],
  slideNumber: { x: 12.5, y: 7.0, color: 'FFFFFF', fontSize: 10 }
});

// Add a slide using the master
const slide = pptx.addSlide({ masterName: 'MASTER_SLIDE' });

// Text
slide.addText('Quarterly Results', { x: 0.5, y: 0.5, w: 8, h: 1, fontSize: 28, bold: true, color: '003B75' });

// Table
const rows = [
  [{ text: 'Metric', options: { bold: true, fill: { color: '003B75' }, color: 'FFFFFF' } }, { text: 'Value', options: { bold: true, fill: { color: '003B75' }, color: 'FFFFFF' } }],
  ['Revenue', '$1.2M'],
  ['Growth', '+15%']
];
slide.addTable(rows, { x: 0.5, y: 2.0, w: 6, h: 2, border: { type: 'solid', pt: 1, color: 'CFCFCF' } });

// Chart
const chartData = [
  { name: 'Q1', labels: ['Jan', 'Feb', 'Mar'], values: [100, 120, 150] },
  { name: 'Q2', labels: ['Apr', 'May', 'Jun'], values: [130, 140, 180] }
];
slide.addChart(pptx.charts.BAR, chartData, { x: 7, y: 2, w: 5.5, h: 4, showTitle: true, title: 'Revenue by Quarter' });

// Image
slide.addImage({ path: './chart-screenshot.png', x: 1, y: 4, w: 5, h: 3 });
// Or base64:
slide.addImage({ data: 'data:image/png;base64,iVBOR...', x: 1, y: 4, w: 5, h: 3 });

// Save
await pptx.writeFile({ fileName: 'report.pptx' });
// Or get as Buffer/Blob:
const buffer = await pptx.write({ outputType: 'nodebuffer' });
```

#### Supported Chart Types
`AREA`, `BAR`, `BAR3D`, `BUBBLE`, `DOUGHNUT`, `LINE`, `PIE`, `RADAR`, `SCATTER`

#### Key Options
- **Slide sizes**: `LAYOUT_16x9`, `LAYOUT_16x10`, `LAYOUT_4x3`, `LAYOUT_WIDE`, or custom `{ width, height }`
- **Output types**: `'nodebuffer'`, `'base64'`, `'arraybuffer'`, `'blob'`, `'uint8array'`, or `writeFile()`
- **RTL text**: `{ rtlMode: true }` on text options
- **Hyperlinks**: `{ hyperlink: { url: 'https://...', tooltip: 'Click' } }`
- **Slide transitions**: `slide.transition = { type: 'fade', speed: 'slow' }`

---

### python-pptx (Python) -- Primary Recommendation

**Version**: 1.0.0 | **License**: MIT
**Docs**: https://python-pptx.readthedocs.io

Reads/writes .pptx. Template-based workflow idiomatic.

#### Installation
```bash
pip install python-pptx
```

#### Core API Pattern
```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.enum.text import PP_ALIGN
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor

# Create from scratch or load template
prs = Presentation()  # blank
# prs = Presentation('template.pptx')  # from template

# Set slide dimensions (default is 10x7.5 inches)
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Add slide using a layout
slide_layout = prs.slide_layouts[5]  # Blank layout (index varies by template)
slide = prs.slides.add_slide(slide_layout)

# Text box
txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
tf = txBox.text_frame
tf.text = 'Quarterly Results'
tf.paragraphs[0].font.size = Pt(28)
tf.paragraphs[0].font.bold = True
tf.paragraphs[0].font.color.rgb = RGBColor(0x00, 0x3B, 0x75)

# Table
rows, cols = 3, 2
table_shape = slide.shapes.add_table(rows, cols, Inches(1), Inches(2.5), Inches(6), Inches(2))
table = table_shape.table
table.cell(0, 0).text = 'Metric'
table.cell(0, 1).text = 'Value'
table.cell(1, 0).text = 'Revenue'
table.cell(1, 1).text = '$1.2M'
table.cell(2, 0).text = 'Growth'
table.cell(2, 1).text = '+15%'

# Chart
chart_data = CategoryChartData()
chart_data.categories = ['Jan', 'Feb', 'Mar']
chart_data.add_series('Revenue', (100, 120, 150))
chart_data.add_series('Costs', (80, 90, 110))
slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(7), Inches(2), Inches(5.5), Inches(4),
    chart_data
)

# Image
slide.shapes.add_picture('chart.png', Inches(1), Inches(5), width=Inches(4))

# Save
prs.save('report.pptx')
```

#### Template-Based Pattern (Preferred for Production)
```python
from pptx import Presentation

prs = Presentation('branded_template.pptx')

# Access placeholders by idx (not position)
slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title + Content layout
title = slide.placeholders[0]  # Title placeholder
body = slide.placeholders[1]   # Body/content placeholder

title.text = 'Q3 Financial Summary'
tf = body.text_frame
tf.text = 'Revenue exceeded targets by 15%'
p = tf.add_paragraph()
p.text = 'Key drivers: enterprise expansion, new product line'
p.level = 1  # Indented bullet

prs.save('quarterly_report.pptx')
```

#### Supported Chart Types
`COLUMN_CLUSTERED`, `BAR_CLUSTERED`, `LINE`, `PIE`, `AREA`, `SCATTER`, `DOUGHNUT`, `RADAR`, `BUBBLE`

Not supported natively: waterfall, funnel, treemap, sunburst, heatmap, Gantt.

---

### pptx-automizer (Node.js) -- Template-First Approach

**Version**: 0.8.1 | **Weekly downloads**: ~10K | **License**: MIT
**GitHub**: https://github.com/singerla/pptx-automizer

Server-side only. Reads .pptx templates, merges slides, modifies via XML callbacks. Wraps PptxGenJS for from-scratch elements in templates.

```javascript
import Automizer from 'pptx-automizer';

const automizer = new Automizer({
  templateDir: './templates',
  outputDir: './output'
});

const pres = automizer.loadRoot('base.pptx')
  .load('charts.pptx', 'charts')
  .load('tables.pptx', 'tables');

// Copy slide from template and modify
pres.addSlide('charts', 1, (slide) => {
  slide.modifyElement('ChartTitle', (element) => {
    element.setText('Updated Revenue Chart');
  });
});

await pres.write('final-report.pptx');
```

---

### officegen (Node.js) -- Legacy, Not Recommended

**Version**: 0.6.5 | Last published 5+ years ago. Unmaintained. Use PptxGenJS instead.

---

### Commercial Options

| Library | Platform | Notes |
|---------|----------|-------|
| Aspose.Slides | Node.js, Python, Java, .NET | Full-featured, handles advanced charts, animations. Paid license. |
| SlideForge | REST API + MCP | Hosted service, 35 composable components, handles python-pptx limitations internally. |
| GrapeCity (Wijmo) | JavaScript | UI-focused, enterprise licensing. |

---

## Practical Patterns

### 1. Data-Driven Report Generation (Node.js)
```javascript
import PptxGenJS from 'pptxgenjs';

async function generateReport(data) {
  const pptx = new PptxGenJS();
  pptx.layout = 'LAYOUT_WIDE';

  // Title slide
  const titleSlide = pptx.addSlide();
  titleSlide.addText(data.title, { x: 1, y: 2, w: 11, h: 2, fontSize: 36, align: 'center' });
  titleSlide.addText(`Generated: ${new Date().toLocaleDateString()}`, { x: 1, y: 4.5, w: 11, h: 1, fontSize: 14, align: 'center', color: '666666' });

  // One slide per section
  for (const section of data.sections) {
    const slide = pptx.addSlide();
    slide.addText(section.heading, { x: 0.5, y: 0.3, w: 10, h: 0.8, fontSize: 24, bold: true });

    if (section.type === 'chart') {
      slide.addChart(pptx.charts.BAR, section.chartData, { x: 0.5, y: 1.5, w: 12, h: 5.5 });
    } else if (section.type === 'table') {
      slide.addTable(section.rows, { x: 0.5, y: 1.5, w: 12, h: 5.5, autoPage: true });
    } else if (section.type === 'bullets') {
      slide.addText(section.items.map(i => ({ text: i, options: { bullet: true } })), { x: 0.5, y: 1.5, w: 11, h: 5 });
    }
  }

  return pptx.write({ outputType: 'nodebuffer' });
}
```

### 2. Template-Based Batch Generation (Python)
```python
import json
from pptx import Presentation
from pptx.util import Inches, Pt

def generate_account_deck(template_path, accounts, output_path):
    """Generate one slide per account from a branded template."""
    prs = Presentation(template_path)
    layout = prs.slide_layouts[1]  # Title + Content

    for account in accounts:
        slide = prs.slides.add_slide(layout)
        slide.placeholders[0].text = account['name']
        tf = slide.placeholders[1].text_frame
        tf.clear()
        for metric, value in account['metrics'].items():
            p = tf.add_paragraph()
            p.text = f"{metric}: {value}"
            p.font.size = Pt(14)

    prs.save(output_path)

# Usage
with open('accounts.json') as f:
    accounts = json.load(f)
generate_account_deck('brand_template.pptx', accounts, 'all_accounts.pptx')
```

### 3. Express API Endpoint (Node.js)
```javascript
import express from 'express';
import PptxGenJS from 'pptxgenjs';

const app = express();
app.use(express.json());

app.post('/api/generate-deck', async (req, res) => {
  try {
    const { title, slides } = req.body;
    const pptx = new PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE';

    for (const slideData of slides) {
      const slide = pptx.addSlide();
      slide.addText(slideData.title, { x: 0.5, y: 0.3, fontSize: 24, bold: true });
      if (slideData.body) {
        slide.addText(slideData.body, { x: 0.5, y: 1.5, w: 12, h: 5, fontSize: 14 });
      }
    }

    const buffer = await pptx.write({ outputType: 'nodebuffer' });
    res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.presentationml.presentation');
    const safeTitle = title.replace(/[^a-zA-Z0-9_\- ]/g, '_');
    res.setHeader('Content-Disposition', `attachment; filename="${safeTitle}.pptx"`);
    res.send(buffer);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
```

### 4. PDF Conversion via LibreOffice Headless
```bash
# Convert single file
libreoffice --headless --convert-to pdf --outdir ./output report.pptx

# Node.js wrapper
npm install libreoffice-convert
```

```javascript
import { convert } from 'libreoffice-convert';
import { readFile, writeFile } from 'fs/promises';

async function pptxToPdf(inputPath, outputPath) {
  const input = await readFile(inputPath);
  const pdf = await new Promise((resolve, reject) => {
    convert(input, '.pdf', undefined, (err, result) => {
      if (err) reject(err);
      else resolve(result);
    });
  });
  await writeFile(outputPath, pdf);
}
```

```python
# Python: subprocess approach
import subprocess

def pptx_to_pdf(input_path, output_dir):
    subprocess.run([
        'libreoffice', '--headless', '--convert-to', 'pdf',
        '--outdir', output_dir, input_path
    ], check=True)
```

### 5. Combining with Chart Libraries
```javascript
// Generate chart as PNG with a charting library, embed in slide
import { ChartJSNodeCanvas } from 'chartjs-node-canvas';
import PptxGenJS from 'pptxgenjs';

const chartCanvas = new ChartJSNodeCanvas({ width: 800, height: 400 });

async function addChartImageSlide(pptx, chartConfig, title) {
  const imageBuffer = await chartCanvas.renderToBuffer(chartConfig);
  const base64 = `data:image/png;base64,${imageBuffer.toString('base64')}`;

  const slide = pptx.addSlide();
  slide.addText(title, { x: 0.5, y: 0.3, fontSize: 22, bold: true });
  slide.addImage({ data: base64, x: 1, y: 1.2, w: 10, h: 5.5 });
}
```

---

## Anti-Patterns and Pitfalls

### Memory Issues
- **python-pptx** holds full .pptx as lxml tree. 1000+ slides → RSS peaks ~1.7GB.
  - **Workaround**: Split into smaller decks, merge after. Or parallelize with asyncio.
  - **Alternative**: `gentle-python-pptx` caches parsed properties for large files.
- **PptxGenJS** more memory-efficient (streaming ZIP), but large image-heavy decks can exhaust Node.js heap.
  - **Workaround**: Batch process, increase `--max-old-space-size`, stream images from disk vs base64.

### Font Embedding Gotchas
- Programmatic libs DO NOT embed fonts.
- Each font family adds 500KB–2MB.
- Commercial fonts often have licensing metadata blocking embed.
- **Best practice**: Use system fonts (Calibri, Arial, Aptos, Segoe UI) pre-installed on Windows/Mac — eliminates rendering differences.
- Custom fonts needed? Tell users to install, or export PDF.

### Cross-Platform Rendering Differences
- Text reflow differs Windows/macOS/LibreOffice (font metrics).
- Charts render with platform fonts + anti-aliasing.
- EMF/WMF Windows-only; use PNG/SVG cross-platform.
- **Mitigation**: Test all target platforms. Fixed-width text boxes + padding. PNG over vector for pixel-perfect.

### Common Mistakes
1. **Shapes outside slide bounds**: No validation — content clips during render.
2. **Ignoring placeholder inheritance**: Manual text box position → inconsistent styling.
3. **Hardcoding layout indices**: Indices vary by template. Enumerate and match by name.
4. **Missing `.rels` updates**: Direct XML manipulation without updating `.rels` corrupts archive.
5. **Large base64 images**: Pass file paths, not base64, where possible.
6. **No `autoPage` for tables**: Large tables overflow without `autoPage: true` (PptxGenJS) or manual pagination.
7. **Forgetting `[Content_Types].xml`**: New media types (SVG, video) need content types registry update.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "The file is corrupt" on open | Malformed XML or missing relationship | Unzip .pptx, validate XML, check all rId refs exist in .rels |
| Images not showing | Wrong relationship target or missing content type | Verify media path in .rels matches file in media/ |
| Slide appears blank | Content outside visible area | Check x/y/w/h within slide dimensions |
| Charts show "Chart not available" | Chart XML refs missing data part | Ensure chart data worksheets (embedded Excel) included |
| Text overlaps or truncates | No autofit/shrink, text exceeds box | Enable `shrinkText: true` (PptxGenJS) or `tf.auto_size = MSO_AUTO_SIZE.BEST_FIT` (python-pptx, import from `pptx.enum.text`) |
| File opens in "repair" mode | ZIP structure or XML namespace error | Ensure proper XML declarations, no BOM in XML files |
| python-pptx OOM on large decks | Full DOM tree in memory | Split generation, merge after |
| PptxGenJS hangs on write | Large base64 images blocking event loop | Use file paths, stream writes, or Worker threads |
| Layout mismatch after template change | Hardcoded layout index shifted | Enumerate layouts by name: `prs.slide_layouts` iteration |
| LibreOffice PDF looks different | Font substitution | Install matching fonts on server, or embed in .pptx first |

---

## Integration Patterns for Automated Reporting

### Pipeline Architecture
```
Data Source (DB/API) --> Transform (shape data for slides)
  --> Generate PPTX (PptxGenJS / python-pptx)
  --> [Optional] Convert to PDF (LibreOffice headless)
  --> Distribute (email / S3 / Slack / dashboard)
```

### Cron-Based Report Generation
```javascript
// Node.js scheduled job
import cron from 'node-cron';
import { generateWeeklyDeck } from './report-generator.js';
import { uploadToS3 } from './storage.js';

cron.schedule('0 8 * * MON', async () => {
  const buffer = await generateWeeklyDeck();
  await uploadToS3(buffer, `reports/weekly-${Date.now()}.pptx`);
});
```

### LLM-Driven Slide Generation
```javascript
// Generate slide content with LLM, render with PptxGenJS
async function llmToSlides(prompt, llmClient) {
  const response = await llmClient.chat({
    messages: [{ role: 'user', content: prompt }],
    response_format: { type: 'json_object' }  // structured output
  });

  const slideSpec = JSON.parse(response.content);
  // slideSpec = { title, slides: [{ heading, bullets, chartData }] }

  const pptx = new PptxGenJS();
  for (const s of slideSpec.slides) {
    const slide = pptx.addSlide();
    slide.addText(s.heading, { x: 0.5, y: 0.3, fontSize: 24, bold: true });
    // ... render based on slide type
  }
  return pptx.write({ outputType: 'nodebuffer' });
}
```

---

## References

- [PptxGenJS Documentation](https://gitbrent.github.io/PptxGenJS/)
- [PptxGenJS GitHub](https://github.com/gitbrent/PptxGenJS)
- [PptxGenJS npm](https://www.npmjs.com/package/pptxgenjs)
- [PptxGenJS Charts API](https://gitbrent.github.io/PptxGenJS/docs/api-charts/)
- [PptxGenJS Masters and Placeholders](https://gitbrent.github.io/PptxGenJS/docs/masters/)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/en/latest/)
- [python-pptx Getting Started](https://python-pptx.readthedocs.io/en/latest/user/quickstart.html)
- [python-pptx Charts](https://python-pptx.readthedocs.io/en/latest/user/charts.html)
- [python-pptx Tables](https://python-pptx.readthedocs.io/en/latest/user/table.html)
- [python-pptx Placeholders](https://python-pptx.readthedocs.io/en/latest/user/placeholders-using.html)
- [pptx-automizer GitHub](https://github.com/singerla/pptx-automizer)
- [pptx-automizer npm](https://www.npmjs.com/package/pptx-automizer)
- [OpenXML PresentationML Anatomy](http://officeopenxml.com/anatomyofOOXML-pptx.php)
- [Microsoft Learn: PresentationML Structure](https://learn.microsoft.com/en-us/office/open-xml/presentation/structure-of-a-presentationml-document)
- [Microsoft Learn: Open XML SDK](https://learn.microsoft.com/en-us/office/open-xml/about-the-open-xml-sdk)
- [python-pptx Packaging Internals](https://python-pptx.readthedocs.io/en/latest/dev/resources/about_packaging.html)
- [PPTX File Anatomy (SlideModel)](https://slidemodel.com/anatomy-of-a-pptx-file/)
- [10 python-pptx Limitations in Production (SlideForge)](https://slideforge.dev/blog/python-pptx-limitations-we-solved)
- [gentle-python-pptx (memory-optimized)](https://github.com/ktsstudio/gentle-python-pptx)
- [SlideForge Presentation API](https://slideforge.dev/)
- [libreoffice-convert npm](https://www.npmjs.com/package/libreoffice-convert)
- [Aspose.Slides for Node.js](https://docs.aspose.com/slides/nodejs-java/)