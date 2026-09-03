<!-- hub-reference-banner -->
> **Reference file — part of the `document-formats` hub.** Formerly standalone `drawio-diagrams` skill.
> Sibling topics now reference files under hubs (`document-formats`) — **not** standalone
> skills. Ignore "use the X skill" / `related_skills` / SKIP pointers naming bare sibling
> skills; load topic's `references/<name>.md` from owning hub (see hub's "Cross-hub map").

---

---
name: drawio-diagrams
title: "Draw.io Programmatic Diagrams"
description: >
  Programmatic draw.io/diagrams.net (.drawio) file creation, parsing, manipulation, and export.
  TRIGGER: user is generating architecture diagrams, flowcharts, or sequence diagrams as .drawio
  XML from code; parsing or transforming existing .drawio files; exporting to SVG/PNG/PDF via
  the draw.io CLI; integrating diagram generation into CI/CD; working with mxGraphModel/mxCell
  XML structure; compressing or decompressing .drawio content; using drawpyo (Python), maxGraph
  (TypeScript), or the drawio-mcp server for AI-assisted diagram generation.
  SKIP: Mermaid, PlantUML, Graphviz DOT, or other text-based diagram DSLs (unless converting
  their output to .drawio format); general SVG/Canvas drawing unrelated to the draw.io file format.
category: developer
version: "1.1.1"
updated: "2026-05-31"
tags: [drawio, diagrams, architecture, xml, mxgraph, visualization, ci-cd]
keywords:
  - draw.io programmatic generation
  - mxGraphModel mxCell XML
  - drawio compression deflate base64
  - drawpyo Python
  - maxGraph TypeScript
  - drawio CLI export SVG PNG PDF
  - drawio CI/CD pipeline
  - mxGeometry edge style
  - drawio-mcp AI diagram generation
  - container group layer page
whenToUse:
  - Generating .drawio architecture or flowchart diagrams from code (Python, JavaScript, Go)
  - Parsing or transforming existing .drawio XML files programmatically
  - Exporting .drawio files to SVG, PNG, or PDF via the draw.io CLI or Docker headless image
  - Integrating diagram generation or export into a CI/CD pipeline
  - Working with mxGraphModel XML structure, mxCell, mxGeometry, and style strings
  - Compressing or decompressing .drawio file content (raw DEFLATE + Base64)
  - Using the drawio-mcp server for AI-assisted diagram creation
  - Building custom shape libraries or stencils for draw.io
whenNotToUse:
  - Mermaid, PlantUML, Graphviz DOT, or other text-based diagram DSLs
  - General SVG or Canvas drawing not targeting the draw.io file format
  - Interactive diagramming UI features in the draw.io editor (not programmatic)
related_skills:
  - devops-infra
  - python-patterns
---

# Draw.io / Diagrams.net Programmatic Reference

**Contents**
1. Overview
2. Core Concepts
3. File Format Details
4. Libraries and Tools
5. Export and Conversion
6. Practical Patterns
7. Custom Shapes and Stencils
8. Anti-Patterns
9. Troubleshooting
10. Integration: draw.io MCP Server
11. References


Expert reference for programmatic draw.io diagram generation and manipulation. Response correct when: produces valid mxGraphModel XML (root cells id="0" and id="1"), uses right encoding for context (uncompressed for Git, compressed for wire), applies style strings that render in draw.io editor.

> **Staleness note:** Library versions (drawpyo, maxGraph, draw.io desktop CLI), drawio-mcp feature set, Docker headless image names current as of May 2026. Verify from each project's releases page before use.

**Navigation by task:**
- XML structure (mxGraphModel, mxCell, mxGeometry, layers, pages) → Core Concepts
- File format (uncompressed vs compressed, mxfile wrapper) → File Format Details
- Generate diagrams in Python → Libraries and Tools → drawpyo
- Generate diagrams in JavaScript/Node.js → Libraries and Tools → Direct XML Generation
- Compress/decompress .drawio content → Libraries and Tools → Compression
- Export to SVG/PNG/PDF → Export and Conversion
- Architecture diagram generator, flowchart from decision tree, git-friendly workflow → Practical Patterns
- Container/group patterns, shape style quick reference, color palettes → Practical Patterns
- Custom shapes and stencils, cloud provider icons → Custom Shapes and Stencils
- CI/CD pipeline for auto-export → Practical Patterns → Git-Friendly Workflow
- AI-assisted generation via drawio-mcp → Integration: draw.io MCP Server
- Anti-patterns and troubleshooting → Anti-Patterns / Troubleshooting

## Overview

Draw.io (diagrams.net) open-source diagramming tool; native file format XML-based (.drawio or .drawio.xml). Format fully documented, can be generated/parsed/manipulated without editor. Suitable for diagram-as-code workflows, CI/CD-generated architecture diagrams, automated documentation pipelines.

Key ecosystem components:
- **File format**: XML with mxGraphModel structure (compressed or uncompressed)
- **Editor**: draw.io desktop (Electron) and web app (diagrams.net)
- **Libraries**: drawpyo (Python), @maxgraph/core (TypeScript), raw XML generation
- **Export**: draw.io CLI, Docker headless, puppeteer-based tools
- **MCP**: jgraph/drawio-mcp for AI-assisted diagram generation

---

## Core Concepts

### Cell Model

Everything in draw.io = **mxCell**. Four roles:

| Role | Attributes | Purpose |
|------|-----------|---------|
| Root cell | `id="0"` | Invisible root of cell hierarchy |
| Layer cell | `id="1" parent="0"` | Default layer; additional layers also have parent="0" |
| Vertex | `vertex="1" parent="1"` | Shapes, text boxes, images, containers |
| Edge | `edge="1" parent="1"` | Connectors between vertices |

Cells **mutually exclusive** -- vertex OR edge, never both.

### Geometry (mxGeometry)

Every vertex has `<mxGeometry>` child:
- `x`, `y` -- top-left corner (absolute or relative inside container)
- `width`, `height` -- dimensions in pixels
- `relative="1"` -- for edge labels (position along edge, 0-1)

Edges use `<mxGeometry>` with `<Array as="points">` for waypoints and `<mxPoint>` for source/target offsets.

### Style Strings

Semicolon-delimited key=value string:
```
rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;fontSize=12;
```

Key style properties:
- **Shape**: `shape=rectangle` (default), `ellipse`, `rhombus`, `hexagon`, `cylinder3`, `mxgraph.aws4.lambda`
- **Colors**: `fillColor=#hex`, `strokeColor=#hex`, `fontColor=#hex`, `gradientColor=#hex`
- **Text**: `fontSize=12`, `fontFamily=Helvetica`, `fontStyle=1` (1=bold, 2=italic, 4=underline, bitwise OR)
- **Layout**: `whiteSpace=wrap`, `html=1`, `align=center`, `verticalAlign=middle`
- **Borders**: `rounded=1`, `arcSize=20`, `strokeWidth=2`, `dashed=1`, `dashPattern=8 4`
- **Containers**: `container=1`, `collapsible=1`, `childLayout=stackLayout`
- **Perimeter**: `perimeter=ellipsePerimeter` (must match shape for proper edge connection)

### Edge Styles

Routing options:
- `edgeStyle=orthogonalEdgeStyle` -- right-angle (most common)
- `edgeStyle=elbowEdgeStyle` -- single bend
- `edgeStyle=entityRelationEdgeStyle` -- ER diagram style
- `edgeStyle=none` or omit -- straight line
- `curved=1` -- smooth curves between waypoints
- `rounded=1` -- rounded corners on orthogonal edges

Arrow markers:
- `startArrow=none`, `endArrow=block` (filled), `endArrow=open`, `endArrow=diamond`, `endArrow=diamondThin`
- `startFill=0`, `endFill=0` -- hollow markers

### Connectors and Source/Target

Edges reference source/target by ID:
```xml
<mxCell id="e1" edge="1" source="v1" target="v2" parent="1">
```

Connection points constrained via `exitX`, `exitY`, `entryX`, `entryY` (0-1 relative to cell bounds) and `exitPerimeter=0` to attach to exact point.

### Layers

Layer = mxCell with `parent="0"` and no vertex/edge attribute:
```xml
<mxCell id="layer2" value="Background" parent="0"/>
```
Assign cells to layer by setting `parent="layer2"`.

### Pages

Multiple pages via multiple `<diagram>` elements inside `<mxfile>`:
```xml
<mxfile>
  <diagram id="page1" name="Architecture">...</diagram>
  <diagram id="page2" name="Sequence">...</diagram>
</mxfile>
```

---

## File Format Details

### Uncompressed Format (Git-Friendly)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2025-01-15T10:00:00.000Z"
        agent="Mozilla/5.0" version="24.0.0" type="device">
  <diagram id="abc123" name="Page-1">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10"
                  guides="1" tooltips="1" connect="1" arrows="1"
                  fold="1" page="1" pageScale="1"
                  pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- vertices and edges here -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### Compressed Format

When compressed, `<diagram>` element contains Base64-encoded deflated content instead of `<mxGraphModel>` child:
```xml
<diagram id="abc123" name="Page-1">
  7V1Zc6M4EP41fkwKxOF9...base64string...
</diagram>
```

**Encoding**: XML string -> `encodeURIComponent()` -> raw DEFLATE (no zlib headers, wbits=-15) -> Base64 encode

**Decoding**: Base64 decode -> raw INFLATE (wbits=-15) -> `decodeURIComponent()` -> XML string

### mxGraphModel Attributes

| Attribute | Default | Purpose |
|-----------|---------|---------|
| `dx`, `dy` | 1200, 800 | Scroll offset |
| `grid` | 1 | Show grid |
| `gridSize` | 10 | Grid spacing in px |
| `page` | 1 | Show page border |
| `pageScale` | 1 | Page scale factor |
| `pageWidth` | 1169 | A4 landscape width |
| `pageHeight` | 827 | A4 landscape height |
| `math` | 0 | Enable LaTeX math |
| `shadow` | 0 | Global shadow |

### Minimal Valid File

Minimum viable structure:
```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>
```

Draw.io accepts just `<mxGraphModel>` without `<mxfile>`/`<diagram>` wrappers.

---

## Libraries and Tools

### Python: drawpyo

Most mature Python library for programmatic draw.io generation.

```bash
pip install drawpyo
```

```python
import drawpyo

# Create file and page
file = drawpyo.File()
file.file_path = "output/"
file.file_name = "architecture.drawio"
page = drawpyo.Page(file=file, name="Main")

# Create shapes
server = drawpyo.diagram.Object(
    page=page, value="Web Server",
    position=(200, 100), width=120, height=60
)
server.base_style = "rounded=1;whiteSpace=wrap;html=1;"

db = drawpyo.diagram.Object(
    page=page, value="Database",
    position=(200, 300), width=120, height=60
)
db.base_style = "shape=cylinder3;whiteSpace=wrap;html=1;"

# Create edge
edge = drawpyo.diagram.Edge(
    page=page, source=server, target=db, label="queries"
)

# Use library shapes
from drawpyo.diagram import object_from_library
process = object_from_library(
    page=page, library="general", obj_name="process", value="ETL"
)

# Write file
file.write()
```

Features: tree diagram generation, flowcharts, shape libraries (General, Flowchart, AWS, Azure, GCP via XML import), automatic layout.

### Python: drawio-diagram-generator

```bash
pip install drawio-diagram-generator
```

Newer alternative with component-based architecture and flexible layout system.

### TypeScript/JavaScript: @maxgraph/core

Maintained successor to mxGraph (EOL Nov 2020). Same graph model as draw.io.

```bash
npm install @maxgraph/core
```

```typescript
import { Graph, InternalEvent } from '@maxgraph/core';

// For headless/programmatic use (no DOM rendering needed for XML generation)
// maxGraph is primarily a rendering library; for pure XML generation,
// direct XML string building or template approaches are often simpler.
```

Note: maxGraph primarily designed for interactive browser-based editors. For pure file generation without rendering, direct XML construction simpler.

### JavaScript: Direct XML Generation (Recommended for Node.js)

```javascript
const { writeFileSync } = require('fs');

function createDrawioFile(cells) {
  const cellsXml = cells.map(c => {
    if (c.type === 'vertex') {
      return `    <mxCell id="${c.id}" value="${escapeXml(c.label)}" ` +
        `style="${c.style}" vertex="1" parent="1">` +
        `<mxGeometry x="${c.x}" y="${c.y}" width="${c.width}" ` +
        `height="${c.height}" as="geometry"/></mxCell>`;
    }
    if (c.type === 'edge') {
      return `    <mxCell id="${c.id}" value="${escapeXml(c.label || '')}" ` +
        `style="${c.style || ''}" edge="1" source="${c.source}" ` +
        `target="${c.target}" parent="1">` +
        `<mxGeometry relative="1" as="geometry"/></mxCell>`;
    }
    return ''; // skip unknown cell types
  }).filter(Boolean).join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram id="diagram1" name="Page-1">
    <mxGraphModel>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
${cellsXml}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;
}

function escapeXml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

// Usage
const xml = createDrawioFile([
  { type: 'vertex', id: 'v1', label: 'Client', x: 100, y: 100,
    width: 120, height: 60, style: 'rounded=1;whiteSpace=wrap;html=1;' },
  { type: 'vertex', id: 'v2', label: 'Server', x: 100, y: 300,
    width: 120, height: 60, style: 'rounded=1;whiteSpace=wrap;html=1;' },
  { type: 'edge', id: 'e1', source: 'v1', target: 'v2', label: 'HTTPS',
    style: 'edgeStyle=orthogonalEdgeStyle;rounded=1;' },
]);
writeFileSync('output.drawio', xml);
```

### Compression/Decompression (Node.js)

```javascript
const pako = require('pako');

// Compress XML for .drawio format
function compressDrawio(xml) {
  const encoded = encodeURIComponent(xml);
  const compressed = pako.deflateRaw(encoded);
  return Buffer.from(compressed).toString('base64');
}

// Decompress .drawio content
function decompressDrawio(base64) {
  const compressed = Buffer.from(base64, 'base64');
  const inflated = pako.inflateRaw(compressed, { to: 'string' });
  return decodeURIComponent(inflated);
}
```

### Compression/Decompression (Python)

```python
import base64, zlib, urllib.parse

def compress_drawio(xml: str) -> str:
    encoded = urllib.parse.quote(xml, safe='~()*!.\'')
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    compressed = compressor.compress(encoded.encode('utf-8')) + compressor.flush()
    return base64.b64encode(compressed).decode('utf-8')

def decompress_drawio(b64: str) -> str:
    compressed = base64.b64decode(b64)
    inflated = zlib.decompress(compressed, -15)  # raw deflate, wbits=-15
    return urllib.parse.unquote(inflated.decode('utf-8'))
```

---

## Export and Conversion

### Draw.io Desktop CLI

```bash
# Basic export
drawio -x -f png -o output.png input.drawio
drawio -x -f svg -o output.svg input.drawio
drawio -x -f pdf -o output.pdf input.drawio

# With options
drawio -x -f png -s 2 -o output@2x.png input.drawio       # 2x scale
drawio -x -f png -t -o output.png input.drawio              # transparent bg
drawio -x -f png -p 0 -o page1.png multi-page.drawio       # specific page (0-indexed)
drawio -x -f png --width 1920 -o wide.png input.drawio     # set width
drawio -x -f png --crop -o cropped.png input.drawio        # crop to content

# Batch export all pages
for i in $(seq 0 9); do
  drawio -x -f png -p $i -o "page_${i}.png" input.drawio 2>/dev/null
done
```

Supported formats: `pdf`, `png`, `jpg`, `svg`, `vsdx`, `xml`

**Platform paths**: macOS binary at `/Applications/draw.io.app/Contents/MacOS/draw.io` (alias as `drawio` in shell profile). Linux: install `.deb`/`.rpm`/`.AppImage` from [releases page](https://github.com/jgraph/drawio-desktop/releases). Windows: installer adds `draw.io` to PATH.

### Headless Export (Linux CI/Docker)

Draw.io desktop is Electron-based, requires display server:

```bash
# With xvfb
xvfb-run -a drawio -x -f png -o output.png input.drawio

# Docker (rlespinasse/drawio-desktop-headless)
docker run --rm -v $(pwd):/data rlespinasse/drawio-desktop-headless \
  -x -f png -o /data/output.png /data/input.drawio
```

### draw.io-export (npm)

```bash
npm install -g draw.io-export
draw.io-export -f png -o output.png input.drawio
```

### drawio-exporter (Rust)

```bash
cargo install drawio-exporter
drawio-exporter -f png input.drawio output/
```

### Puppeteer-based Export

For environments without desktop app, use `puppeteer` to drive diagrams.net export endpoint. Community package `drawio-export` (npm) wraps this. `rlespinasse/drawio-desktop-headless` Docker image (above) more reliable for CI — bundles real Electron draw.io instance with xvfb.

---

## Practical Patterns

### Architecture Diagram Generator

```javascript
function architectureDiagram(services) {
  let id = 2;
  const cells = [];
  const positions = {};

  // Layout services in a grid
  services.forEach((svc, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 100 + col * 200;
    const y = 100 + row * 200;
    const cellId = `svc_${id++}`;
    positions[svc.name] = cellId;

    cells.push({
      type: 'vertex', id: cellId, label: svc.name,
      x, y, width: 140, height: 70,
      style: styleForType(svc.type)
    });
  });

  // Add connections
  services.forEach(svc => {
    (svc.connects_to || []).forEach(target => {
      if (positions[target]) {
        cells.push({
          type: 'edge', id: `edge_${id++}`,
          source: positions[svc.name], target: positions[target],
          style: 'edgeStyle=orthogonalEdgeStyle;rounded=1;'
        });
      }
    });
  });

  return createDrawioFile(cells);
}

function styleForType(type) {
  const styles = {
    service: 'rounded=1;whiteSpace=wrap;html=1;fillColor=#DAE8FC;strokeColor=#6C8EBF;',
    database: 'shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#D5E8D4;strokeColor=#82B366;',
    queue: 'shape=mxgraph.aws4.sqs;fillColor=#E6D0DE;strokeColor=#996185;',
    cache: 'shape=hexagon;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor=#D6B656;',
    loadbalancer: 'shape=mxgraph.aws4.elb;fillColor=#F8CECC;strokeColor=#B85450;',
  };
  return styles[type] || styles.service;
}
```

### Flowchart from Decision Tree

```python
import drawpyo

def decision_tree_to_drawio(tree, filepath):
    file = drawpyo.File()
    file.file_path = filepath
    page = drawpyo.Page(file=file)

    nodes = {}
    y_offset = 0

    def add_node(node, x=300, y=None):
        nonlocal y_offset
        if y is None:
            y = y_offset
            y_offset += 120

        obj = drawpyo.diagram.Object(
            page=page, value=node['label'],
            position=(x, y), width=160, height=60
        )
        if node.get('type') == 'decision':
            obj.base_style = 'rhombus;whiteSpace=wrap;html=1;'
        elif node.get('type') == 'end':
            obj.base_style = 'ellipse;whiteSpace=wrap;html=1;fillColor=#D5E8D4;'
        else:
            obj.base_style = 'rounded=1;whiteSpace=wrap;html=1;'

        nodes[node['id']] = obj

        for child in node.get('children', []):
            child_obj = add_node(child, x + (100 if child == node['children'][-1] else -100))
            drawpyo.diagram.Edge(
                page=page, source=obj, target=child_obj,
                label=child.get('edge_label', '')
            )

        return obj

    add_node(tree)
    file.write()
```

### Git-Friendly Workflow

Store .drawio files uncompressed for meaningful diffs:

1. **Configure draw.io** to save uncompressed: Extras > Preferences > uncheck "Compressed", or set file attribute:
   ```xml
   <mxfile compressed="false">
   ```

2. **.gitattributes** for proper diff handling:
   ```
   *.drawio diff
   *.drawio.svg binary
   *.drawio.png binary
   ```

3. **Pre-commit hook** to auto-export PNG/SVG alongside .drawio:
   ```bash
   #!/bin/bash
   for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.drawio$'); do
     xvfb-run -a drawio -x -f svg -o "${file%.drawio}.svg" "$file"
     git add "${file%.drawio}.svg"
   done
   ```

4. **CI/CD pipeline** for automated diagram rendering:
   ```yaml
   # .github/workflows/diagrams.yml
   name: Export Diagrams
   on:
     push:
       paths: ['docs/**/*.drawio']
   jobs:
     export:
       runs-on: ubuntu-latest
       container: rlespinasse/drawio-desktop-headless
       steps:
         - uses: actions/checkout@v4
         - run: |
             find docs -name "*.drawio" -exec sh -c '
               drawio -x -f svg -o "${1%.drawio}.svg" "$1"
             ' _ {} \;
         - uses: stefanzweifel/git-auto-commit-action@v5
           with:
             commit_message: "chore: auto-export diagram SVGs"
   ```

### Container/Group Pattern

```xml
<!-- Container (group) -->
<mxCell id="group1" value="VPC" style="rounded=1;whiteSpace=wrap;html=1;
  container=1;collapsible=0;fillColor=none;strokeColor=#666666;
  dashed=1;dashPattern=8 4;fontSize=14;fontStyle=1;verticalAlign=top;"
  vertex="1" parent="1">
  <mxGeometry x="50" y="50" width="400" height="300" as="geometry"/>
</mxCell>

<!-- Child inside container (position relative to container) -->
<mxCell id="child1" value="Subnet A" style="rounded=1;whiteSpace=wrap;html=1;"
  vertex="1" parent="group1">
  <mxGeometry x="20" y="40" width="120" height="60" as="geometry"/>
</mxCell>
```

### Common Shape Styles Quick Reference

```
# Rectangles
rounded=1;whiteSpace=wrap;html=1;
shape=process;whiteSpace=wrap;html=1;       # double-sided rect

# Circles and Ovals
ellipse;whiteSpace=wrap;html=1;
ellipse;whiteSpace=wrap;html=1;aspect=fixed;  # perfect circle

# Diamonds (decisions)
rhombus;whiteSpace=wrap;html=1;

# Cylinders (databases)
shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=15;

# Documents
shape=document;whiteSpace=wrap;html=1;

# Hexagons
shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;

# Cloud shapes
ellipse;shape=cloud;whiteSpace=wrap;html=1;

# Swimlane / Pool
shape=mxgraph.flowchart.swimlane;startSize=30;

# Actor (stick figure)
shape=mxgraph.basic.person;

# Note/Comment
shape=note;whiteSpace=wrap;html=1;size=14;

# Callout
shape=callout;whiteSpace=wrap;html=1;perimeter=calloutPerimeter;size=30;position=0.5;
```

### Color Palettes (draw.io defaults)

```
Blue:   fillColor=#DAE8FC; strokeColor=#6C8EBF;
Green:  fillColor=#D5E8D4; strokeColor=#82B366;
Orange: fillColor=#FFE6CC; strokeColor=#D79B00;
Red:    fillColor=#F8CECC; strokeColor=#B85450;
Purple: fillColor=#E1D5E7; strokeColor=#9673A6;
Yellow: fillColor=#FFF2CC; strokeColor=#D6B656;
Gray:   fillColor=#F5F5F5; strokeColor=#666666;
Dark:   fillColor=#1A1A2E; strokeColor=#FFFFFF; fontColor=#FFFFFF;
```

---

## Custom Shapes and Stencils

### Library Format

Custom libraries use `<mxlibrary>` wrapping a JSON array:
```xml
<mxlibrary>[
  {
    "xml": "<mxGraphModel><root><mxCell id=\"0\"/><mxCell id=\"1\" parent=\"0\"/><mxCell id=\"2\" value=\"\" style=\"shape=hexagon;\" vertex=\"1\" parent=\"1\"><mxGeometry width=\"80\" height=\"80\" as=\"geometry\"/></mxCell></root></mxGraphModel>",
    "w": 80,
    "h": 80,
    "title": "My Hexagon",
    "aspect": "fixed"
  }
]</mxlibrary>
```

### Stencil XML Format

Complex custom shapes use XML stencil definitions:
```xml
<shape name="myShape" h="100" w="100" aspect="variable" strokewidth="inherit">
  <connections>
    <constraint x="0.5" y="0" perimeter="1" name="N"/>
    <constraint x="1" y="0.5" perimeter="1" name="E"/>
    <constraint x="0.5" y="1" perimeter="1" name="S"/>
    <constraint x="0" y="0.5" perimeter="1" name="W"/>
  </connections>
  <background>
    <rect x="0" y="0" w="100" h="100"/>
  </background>
  <foreground>
    <fillstroke/>
    <path>
      <move x="50" y="0"/>
      <line x="100" y="50"/>
      <line x="50" y="100"/>
      <line x="0" y="50"/>
      <close/>
    </path>
    <fillstroke/>
  </foreground>
</shape>
```

### Using Cloud Provider Icons

Reference built-in stencil libraries via style:
```
shape=mxgraph.aws4.lambda;
shape=mxgraph.aws4.s3;
shape=mxgraph.aws4.api_gateway;
shape=mxgraph.azure.virtual_machine;
shape=mxgraph.gcp2.compute_engine;
shape=mxgraph.kubernetes.node;
```

---

## Anti-Patterns

1. **Generating compressed files for version control** -- Always use uncompressed XML when diagrams live in Git. Compressed Base64 produces meaningless diffs.

2. **Reusing cell IDs across pages** -- IDs must be unique within a diagram (page). Use UUID or sequential counters.

3. **Missing parent cells** -- Every .drawio file MUST have `id="0"` (root) and `id="1"` (default layer). Omitting these causes load failures.

4. **Forgetting perimeter on non-rectangular shapes** -- Without `perimeter=ellipsePerimeter` on an ellipse, edges connect to the invisible bounding box.

5. **Using runtime `import()` to load maxGraph in service workers** -- maxGraph requires DOM context; use direct XML generation for headless/server-side work.

6. **Hardcoding coordinates without layout logic** -- For dynamic diagrams, implement grid/tree/force layout algorithms rather than fixed positions.

7. **Mixing vertex="1" and edge="1"** -- A cell cannot be both. Labeled edges use a child mxCell with `connectable="0"` for the label.

8. **Omitting html=1 in styles with HTML labels** -- If your `value` contains HTML markup (bold, line breaks), you must include `html=1;` in the style string.

9. **Using absolute geometry inside containers** -- Child cells of a container use coordinates relative to the container's top-left. Using absolute coords places them outside visually.

10. **Exporting without xvfb on headless Linux** -- The draw.io Electron app requires a display server. Always wrap with `xvfb-run -a` in CI environments.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| File opens blank | Missing root cells (id 0 and 1) | Add `<mxCell id="0"/>` and `<mxCell id="1" parent="0"/>` |
| Shapes overlap | Same x,y for multiple cells | Implement layout algorithm or offset |
| Edges connect to wrong point | Missing perimeter style | Add `perimeter=ellipsePerimeter` for ellipses, etc. |
| Text truncated | Missing whiteSpace=wrap | Add `whiteSpace=wrap;html=1;` to style |
| Export fails in CI | No display server | Use `xvfb-run -a` or Docker headless image |
| Compressed file unreadable | Wrong deflate settings | Use raw deflate (wbits=-15), not gzip/zlib |
| Labels not rendering HTML | Missing html=1 | Add `html=1;` to style when value has HTML |
| Container children misplaced | Absolute vs relative coords | Children use coords relative to container |
| Multi-page not working | Single diagram element | Wrap each page in separate `<diagram>` element |
| Git diff unreadable | Compressed format | Set `compressed="false"` in mxfile attribute |

---

## Integration: draw.io MCP Server

The official `jgraph/drawio-mcp` provides AI-assisted diagram generation with:
- `create_drawio` -- Generate diagram XML from description
- `edit_drawio` -- Modify existing diagram
- `search_shapes` -- Search 10,000+ shapes across all libraries (AWS, Azure, GCP, Kubernetes, UML, BPMN, etc.)
- Style and XML reference docs bundled for LLM context

Install: See [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) for setup. Typical MCP config adds stdio transport entry pointing to drawio-mcp server binary.

---

## References

- [Draw.io File Format Guide](https://diagrams.so/learn/drawio-format-guide)
- [Draw.io AI Generation Documentation](https://www.drawio.com/doc/faq/ai-drawio-generation)
- [jgraph/drawio-mcp GitHub (XML + Style Reference)](https://github.com/jgraph/drawio-mcp)
- [drawio-mcp XML Reference](https://github.com/jgraph/drawio-mcp/blob/main/shared/xml-reference.md)
- [drawio-mcp Style Reference](https://github.com/jgraph/drawio-mcp/blob/main/shared/style-reference.md)
- [drawio-mcp XSD Schema](https://github.com/jgraph/drawio-mcp/blob/main/shared/mxfile.xsd)
- [maxGraph (mxGraph successor)](https://github.com/maxGraph/maxGraph)
- [maxGraph Documentation](https://maxgraph.github.io/maxGraph/docs/intro/)
- [drawpyo Python Library](https://github.com/MerrimanInd/drawpyo)
- [drawpyo Documentation](https://merrimanind.github.io/drawpyo/)
- [drawio-diagram-generator (PyPI)](https://pypi.org/project/drawio-diagram-generator/)
- [draw.io Desktop GitHub](https://github.com/jgraph/drawio)
- [Docker Headless Export](https://github.com/rlespinasse/docker-drawio-desktop-headless)
- [draw.io-export npm](https://www.npmjs.com/package/draw.io-export)
- [Custom Shape Libraries Format](https://www.drawio.com/doc/faq/format-custom-shape-library)
- [Complex Custom Shapes](https://www.drawio.com/doc/faq/shape-complex-create-edit)
- [Diagrams from Code (draw.io blog)](https://www.drawio.com/blog/diagrams-from-code)
- [Draw.io XML Source Editing](https://www.drawio.com/doc/faq/diagram-source-edit)
- [DeepWiki: File Format Reference](https://deepwiki.com/jgraph/drawio-diagrams/10-file-format-reference)