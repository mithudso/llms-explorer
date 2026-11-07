// No new visitor identifier or browser storage. GA4 remains the configured backend.
declare global {
  interface Window { gtag?: (...args: unknown[]) => void; }
}
const PROPERTY = "G-0E31PW5CE9";
export function analyticsAllowed(): boolean {
  return typeof window !== "undefined" && document.body?.dataset.analyticsEnabled === "true"
    && navigator.doNotTrack !== "1"
    && !(navigator as Navigator & { globalPrivacyControl?: boolean }).globalPrivacyControl
    && !(window as unknown as Record<string, unknown>)[`ga-disable-${PROPERTY}`]
    && typeof window.gtag === "function";
}
export function track(name: string, values: Record<string, string | undefined> = {}): boolean {
  if (!analyticsAllowed() || !/^[a-z][a-z0-9_]{0,39}$/.test(name)) return false;
  const params: Record<string, string> = {
    page_location: location.origin + location.pathname,
    page_referrer: document.referrer ? new URL(document.referrer).origin : "",
  };
  // Only bounded identifiers, never prompt text, search text, URLs with queries or files.
  for (const key of ["kind", "item", "outcome", "label", "card", "cta_id", "destination"]) {
    const value = values[key];
    if (value && /^[a-zA-Z0-9/_& .-]{1,100}$/.test(value)) params[key] = value;
  }
  try { window.gtag!("event", name, params); return true; }
  catch { return false; }
}
export function installEngagement(): void {
  document.addEventListener("click", event => {
    const el = event.target instanceof Element ? event.target.closest<HTMLElement>("[data-track]") : null;
    if (!el || el.dataset.track === "resources_menu_open") return;
    track(el.dataset.track ?? "", {
      label: el.dataset.label, card: el.dataset.card, cta_id: el.dataset.ctaId,
      destination: el.dataset.destination ?? (el instanceof HTMLAnchorElement ? new URL(el.href).pathname : undefined),
    });
  });
  document.addEventListener("toggle", event => {
    const el = event.target;
    if (el instanceof HTMLDetailsElement && el.open && el.matches("details.menu")) track("resources_menu_open");
    if (el instanceof HTMLDetailsElement && el.open && el.matches("[data-skill-prompt]")) track("skill_prompt_open", { item: el.dataset.skillPrompt });
  }, true);
  const parts = location.pathname.split("/").filter(Boolean);
  if (["workflows", "skills", "apps"].includes(parts[0]) && parts.length === 2) {
    track("resource_view", { kind: parts[0], item: parts[1] });
  }
  const openPrompt = () => {
    if (location.hash === "#prompt") {
      const prompt = document.querySelector<HTMLDetailsElement>("[data-skill-prompt]");
      if (prompt) prompt.open = true;
    }
  };
  window.addEventListener("hashchange", openPrompt); openPrompt();
  document.querySelectorAll<HTMLDetailsElement>("details.menu").forEach(menu => {
    menu.addEventListener("keydown", event => {
      if (event.key === "Escape") { menu.open = false; menu.querySelector("summary")?.focus(); }
    });
  });
}
