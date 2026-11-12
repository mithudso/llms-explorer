const WIDTH = 300;
const HEIGHT = 250;
const FRAME_SOURCE = "/ads/ezmob-banner.html";
const SANDBOX = "allow-scripts allow-popups allow-popups-to-escape-sandbox";

/** Load ads only in eligible markup, after opt-out checks and near the viewport. */
export function installEzMobBanners(root: ParentNode = document): void {
  const privacyNavigator = navigator as Navigator & { globalPrivacyControl?: boolean };
  if (privacyNavigator.globalPrivacyControl || navigator.doNotTrack === "1") return;

  for (const banner of root.querySelectorAll<HTMLElement>("[data-ezmob-banner]")) {
    if (banner.dataset.ezmobInitialized === "true") continue;
    const surface = banner.querySelector<HTMLElement>("[data-ezmob-surface]");
    if (!surface) continue;
    banner.dataset.ezmobInitialized = "true";
    banner.hidden = false;
    let frame: HTMLIFrameElement | undefined;
    const resize = () => {
      if (frame) frame.style.transform = `scale(${Math.min(1, surface.clientWidth / WIDTH)})`;
    };
    const load = () => {
      if (frame) return;
      frame = document.createElement("iframe");
      frame.title = "Advertisement";
      frame.width = String(WIDTH);
      frame.height = String(HEIGHT);
      frame.loading = "lazy";
      frame.referrerPolicy = "origin";
      frame.setAttribute("sandbox", SANDBOX);
      frame.src = FRAME_SOURCE;
      surface.append(frame);
      resize();
    };
    const sizing = typeof ResizeObserver === "undefined" ? undefined : new ResizeObserver(resize);
    sizing?.observe(surface);
    const visibility = typeof IntersectionObserver === "undefined" ? undefined : new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          load();
          visibility?.disconnect();
        }
      },
      { rootMargin: "200px" },
    );
    if (visibility) visibility.observe(surface);
    else load();
    window.addEventListener("pagehide", () => {
      visibility?.disconnect();
      sizing?.disconnect();
    }, { once: true });
  }
}
