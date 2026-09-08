#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dir = path.dirname(fileURLToPath(import.meta.url));
// Point these at a local checkout of the source hub. They are read from the
// environment so no operator path or internal repository name is committed.
const SOURCE_ROOT = process.env.CONTEXT_HUB_ROOT;
if (!SOURCE_ROOT) {
  console.error('CONTEXT_HUB_ROOT is unset. Set it to a local checkout of the source hub.');
  process.exit(2);
}
const SOURCE_TREE = `${SOURCE_ROOT}/concept-tree/tree.json`;
const SOURCE_SOURCES = `${SOURCE_ROOT}/local-sources`;
const TARGET_DIR = path.resolve(__dir, '..');

/**
 * Parse tree.json and extract concept hierarchy.
 */
function loadConceptTree() {
  const data = JSON.parse(fs.readFileSync(SOURCE_TREE, 'utf8'));
  return data; // array of concept objects
}

/**
 * Load manifest + context for a skill.
 */
function loadSkillMetadata(skillId) {
  const manifestPath = path.join(SOURCE_SOURCES, skillId, 'manifest.yaml');
  const contextPath = path.join(SOURCE_SOURCES, skillId, 'context.md');

  let manifest = null;
  let context = null;

  try {
    if (fs.existsSync(manifestPath)) {
      manifest = fs.readFileSync(manifestPath, 'utf8');
    }
    if (fs.existsSync(contextPath)) {
      context = fs.readFileSync(contextPath, 'utf8');
    }
  } catch (err) {
    console.warn(`[WARN] Failed to load skill ${skillId}: ${err.message}`);
  }

  return { manifest, context };
}

/**
 * Extract atomic facts from markdown context.
 * Simple heuristic: lines that are paragraphs or list items.
 */
function extractFacts(context, skillId) {
  const facts = [];
  if (!context) return facts;

  const lines = context.split('\n');
  let currentSection = 'general';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Detect headings as section markers
    if (line.startsWith('#')) {
      currentSection = line.replace(/^#+\s*/, '');
      continue;
    }

    // Capture non-empty paragraphs and list items as facts
    if (line && !line.startsWith('```') && !line.startsWith('|') && !line.startsWith('[')) {
      if (line.startsWith('-') || line.startsWith('•') || /^\d+\./.test(line)) {
        // List item
        const factText = line.replace(/^[-•]\s*|\d+\.\s*/, '').trim();
        if (factText) {
          facts.push({
            text: factText,
            section: currentSection,
            source: `${skillId}:${i + 1}`,
            skillId
          });
        }
      } else if (line.length > 20) {
        // Paragraph (heuristic: longer lines)
        facts.push({
          text: line,
          section: currentSection,
          source: `${skillId}:${i + 1}`,
          skillId
        });
      }
    }
  }

  return facts;
}

/**
 * Main migration.
 */
async function migrate() {
  console.log('[MIGRATE] Loading concept tree...');
  const concepts = loadConceptTree();
  console.log(`[MIGRATE] Loaded ${concepts.length} concepts`);

  const allFacts = [];
  const skillMap = new Map(); // skillId -> metadata
  const conceptIndex = [];

  // Load each skill
  console.log('[MIGRATE] Loading skill metadata and context...');
  for (const concept of concepts) {
    const { skillId } = concept;
    if (!skillId) {
      console.warn(`[WARN] Concept "${concept.concept}" has no skillId, skipping`);
      continue;
    }
    const { manifest, context } = loadSkillMetadata(skillId);

    skillMap.set(skillId, { manifest, context, concept });

    // Extract facts
    const facts = extractFacts(context, skillId);
    allFacts.push(...facts);

    // Build index entry
    conceptIndex.push({
      concept: concept.concept,
      skillId,
      parent: concept.parentConcept,
      children: concept.childConcepts,
      factsCount: facts.length
    });
  }

  console.log(`[MIGRATE] Extracted ${allFacts.length} facts from ${skillMap.size} skills`);

  // Write llms-facts as JSONL (one fact per line with source anchor)
  const factsPath = path.join(TARGET_DIR, 'llms-facts-mdb-context.jsonl');
  const factsLines = allFacts.map(f =>
    `- ${f.text} [src: ${f.skillId}]`
  ).join('\n');

  fs.writeFileSync(factsPath, factsLines, 'utf8');
  console.log(`[MIGRATE] Wrote facts to ${factsPath}`);

  // Write concept index
  const indexPath = path.join(TARGET_DIR, 'llms-mdb-context-index.json');
  fs.writeFileSync(indexPath, JSON.stringify(conceptIndex, null, 2), 'utf8');
  console.log(`[MIGRATE] Wrote concept index to ${indexPath}`);

  // Summary
  console.log('[MIGRATE] ✓ Migration complete');
  console.log(`  - Concepts: ${concepts.length}`);
  console.log(`  - Skills: ${skillMap.size}`);
  console.log(`  - Facts extracted: ${allFacts.length}`);
  console.log(`  - Output files: llms-facts-mdb-context.jsonl, llms-mdb-context-index.json`);
}

migrate().catch(err => {
  console.error('[ERROR]', err);
  process.exit(1);
});
