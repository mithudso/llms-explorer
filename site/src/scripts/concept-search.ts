export type SearchItem = { slug: string; concept: string; summary: string; text?: string };

export function keywordHits(query: string, items: SearchItem[], limit = 8): SearchItem[] {
  const terms = query.toLocaleLowerCase().match(/[\p{L}\p{N}_$]+/gu) ?? [];
  if (!terms.length) return [];
  return items.map(item => {
    const title = item.concept.toLocaleLowerCase();
    const body = (item.text ?? item.summary).toLocaleLowerCase();
    const score = terms.every(term => title.includes(term) || body.includes(term))
      ? terms.reduce((total, term) => total + (title.includes(term) ? 4 : 1), 0)
        + (title.includes(query.toLocaleLowerCase()) ? 10 : 0) : 0;
    return { item, score };
  }).filter(hit => hit.score > 0)
    .sort((a, b) => b.score - a.score || a.item.concept.localeCompare(b.item.concept))
    .slice(0, limit).map(hit => hit.item);
}
