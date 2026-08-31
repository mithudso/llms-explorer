import { defineCollection, z } from "astro:content";
const page = z.object({
  title: z.string(), description: z.string(),
  section: z.string().optional(), order: z.number().optional(),
  date: z.string().optional(), tags: z.array(z.string()).optional(),
  sources: z.array(z.string()).optional(),
});
export const collections = {
  reference: defineCollection({ type: "content", schema: page }),
  essays: defineCollection({ type: "content", schema: page }),
  examples: defineCollection({ type: "content", schema: page }),
  blog: defineCollection({ type: "content", schema: page }),
};
