import { defineCollection, z } from "astro:content";
const page = z.object({
  title: z.string(), description: z.string(),
  section: z.string().optional(), order: z.number().optional(),
  date: z.string().optional(), tags: z.array(z.string()).optional(),
  sources: z.array(z.string()).optional(),
});
const skill = page.extend({
  // Path to this skill's live public showcase, when one exists — the
  // playground pages under site/src/pages/playground/. Most skills are
  // orchestration-heavy and only run inside an agent harness with filesystem
  // and tool access, so most don't have one.
  liveDemo: z.string().optional(),
  aliasCommand: z.string().optional(),
});
export const collections = {
  reference: defineCollection({ type: "content", schema: page }),
  essays: defineCollection({ type: "content", schema: page }),
  examples: defineCollection({ type: "content", schema: page }),
  blog: defineCollection({ type: "content", schema: page }),
  skills: defineCollection({ type: "content", schema: skill }),
};
