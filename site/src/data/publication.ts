import ledger from "./publication-ledger.json";

type Article = { id: string; data: { date?: string; draft?: boolean; category?: string } };

export function publicationDay(now = new Date()): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(now);
  const part = (name: string) => parts.find((p) => p.type === name)!.value;
  return `${part("year")}-${part("month")}-${part("day")}`;
}

export function isPublishedArticle(entry: Article, today = publicationDay()): boolean {
  return !entry.data.draft && (!entry.data.date || entry.data.date <= today);
}

export function articleDate(entry: Article): string {
  const receipt = (ledger.entries as { slug: string; published_on: string }[])
    .find((item) => item.slug === entry.id);
  return receipt?.published_on ?? entry.data.date ?? "";
}

export function newestFirst(a: Article, b: Article): number {
  return articleDate(b).localeCompare(articleDate(a));
}

export function isResearchArticle(entry: Article): boolean {
  return entry.data.category === "research" || entry.id.startsWith("research/");
}
