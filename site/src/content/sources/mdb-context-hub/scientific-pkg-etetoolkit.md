---
title: "Scientific Phylogenetics (ETE Toolkit)"
description: "ETE (Environment for Tree Exploration) is a Python toolkit for phylogenetic and hierarchical tree analysis. Core use cases: tree I/O and manipulation, evolutionary event detection, NCBI taxonomy integ"
---

# ETE Toolkit (ete3)

ETE (Environment for Tree Exploration) is a Python toolkit for phylogenetic and hierarchical tree analysis. Core use cases: tree I/O and manipulation, evolutionary event detection, NCBI taxonomy integration, visualization, and clustering analysis.

## When to use this skill
Use for: loading/pruning/rerooting/traversing Newick/NHX/PhyloXML trees; detecting evolutionary events (duplication, speciation) and identifying orthologs/paralogs; NCBI taxonomy queries, lineage retrieval, tree annotation; tree visualization (PDF/SVG/PNG) with custom NodeStyle/Faces/layout functions; Robinson-Foulds comparison; ClusterTree heatmaps.

**When not to use:** generating sequence alignments, running inference tools (IQ-TREE, RAxML), or general bioinformatics not involving tree structures.

## Installation
```bash
pip install ete3
pip install ete3[gui]              # GUI/rendering support
# System deps for rendering:
brew install qt@5                  # macOS
sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg   # Ubuntu/Debian
```
**NCBI Taxonomy first-run:** `NCBITaxa()` downloads ~300 MB to `~/.etetoolkit/taxa.sqlite` on first instantiation; subsequent calls are fast local lookups.

## Core patterns

### Tree I/O and basic manipulation
```python
from ete3 import Tree
tree = Tree("tree.nw", format=1)   # format=1 internal names; format=0 flexible w/ branch lengths
print(f"Leaves: {len(tree)}, Nodes: {len(list(tree.traverse()))}")
tree.prune(["species1", "species2", "species3"], preserve_branch_length=True)
midpoint = tree.get_midpoint_outgroup(); tree.set_outgroup(midpoint)
tree.write(outfile="rooted_tree.nw")
```

**Newick format codes** (`format=` on read/write): 0 = flexible w/ branch lengths (default read); 1 = internal node names; 2 = bootstrap/support; 5 = internal names + branch lengths; 8 = all features; 9 = leaf names only; 100 = topology only.

NHX preserves custom features:
```python
tree.write(outfile="tree.nhx", features=["habitat", "temperature"])
```

### Traversal strategies
```python
for node in tree.traverse("postorder"): ...   # bottom-up (aggregation)
for node in tree.traverse("preorder"): ...     # top-down (propagation)
for leaf in tree.iter_leaves(): process(leaf)  # iterator, memory-efficient for >10k leaves
```

### Evolutionary event detection and orthology
```python
from ete3 import PhyloTree
tree = PhyloTree("gene_tree.nw", alignment="alignment.fasta")
tree.set_species_naming_function(lambda x: x.split("_")[0])
events = tree.get_descendant_evol_events()   # annotates evoltype "D" or "S"
query = tree & "species1_gene1"
orthologs, paralogs = [], []
for event in events:
    if query in event.in_seqs:
        targets = [s for s in event.out_seqs if s != query]
        if event.etype == "S": orthologs.extend(targets)
        elif event.etype == "D": paralogs.extend(targets)
ortho_groups = tree.get_speciation_trees()
for i, ortho in enumerate(ortho_groups): ortho.write(outfile=f"ortho_{i}.nw")
```

### NCBI taxonomy
```python
from ete3 import NCBITaxa
ncbi = NCBITaxa()   # downloads DB on first run (~300 MB)
name2taxid = ncbi.get_name_translator(["Homo sapiens", "Mus musculus"])
taxids = [v[0] for v in name2taxid.values()]
tree = ncbi.get_topology(taxids)
for node in tree.traverse():
    if hasattr(node, "sci_name"): lineage = ncbi.get_lineage(node.taxid)
ncbi.update_taxonomy_database()
```

### Tree comparison
```python
from ete3 import Tree
t1, t2 = Tree("tree1.nw"), Tree("tree2.nw")
rf, max_rf, common_leaves, parts_t1, parts_t2 = t1.robinson_foulds(t2)
normalized = rf / max_rf if max_rf > 0 else 0.0
unique_t1 = parts_t1 - parts_t2; unique_t2 = parts_t2 - parts_t1
```

### Visualization
```python
from ete3 import Tree, TreeStyle, NodeStyle, TextFace, CircleFace
tree = Tree("tree.nw")
ts = TreeStyle(); ts.show_leaf_name = True; ts.show_branch_support = True; ts.scale = 50
for node in tree.traverse():
    ns = NodeStyle()
    ns["fgcolor"] = "blue" if node.is_leaf() else ("darkgreen" if node.support > 0.9 else "red")
    ns["size"] = 8 if node.is_leaf() else 5
    node.set_style(ns)
tree.render("tree.pdf", tree_style=ts)            # PDF/SVG for publication (vector)
tree.render("tree.png", w=800, h=600, units="px", dpi=300)
tree.show(tree_style=ts)                          # interactive (requires Qt)
```

Layout function for per-node faces:
```python
def layout(node):
    if node.is_leaf():
        color = "blue" if node.habitat == "marine" else "green"
        node.add_face(CircleFace(radius=5, color=color), column=0, position="aligned")
        node.add_face(TextFace(node.name, fsize=10), column=1, position="aligned")
ts = TreeStyle(); ts.layout_fn = layout; ts.show_leaf_name = False
tree.render("annotated.pdf", tree_style=ts)
```

### Clustering analysis
```python
from ete3 import ClusterTree
matrix = """#Names\tSample1\tSample2\tSample3
Gene1\t1.5\t2.3\t0.8
Gene2\t0.9\t1.1\t1.8"""
tree = ClusterTree("((Gene1,Gene2),Gene3);", text_array=matrix)
for node in tree.traverse():
    if not node.is_leaf():
        print(f"Silhouette: {node.get_silhouette():.3f}, Dunn: {node.get_dunn():.3f}")
```

## Best practices
| Practice | Why |
|----------|-----|
| `preserve_branch_length=True` on prune | Maintains phylogenetic distances |
| `iter_leaves()`/`iter_*` over `get_*` | Memory-efficient on >10k-leaf trees |
| `get_cached_content()` for repeated node access | Avoids redundant subtree walks |
| Postorder traversal for aggregation | Children processed before parents |
| PDF/SVG for publication figures | Scalable; editable in Illustrator/Inkscape |
| `tree.show()` before `tree.render()` | Catch layout issues interactively |
| Cache NCBI taxonomy lookups | Avoid repeated DB queries in loops |

## Troubleshooting
- `ModuleNotFoundError: No module named 'ete3'` → `pip install ete3`
- Qt rendering errors (render/show fails) → `brew install qt@5` (macOS), `apt-get install python3-pyqt5 python3-pyqt5.qtsvg` (Ubuntu), or `pip install ete3[gui]`
- NCBI taxonomy DB corrupt/missing → `NCBITaxa().update_taxonomy_database()`
- `robinson_foulds` shared-leaf error → both trees need same leaf set, or pass `unrooted_trees=True`

Sources: etetoolkit.org docs (tutorial, reference_tree), pypi.org/project/ete3.
