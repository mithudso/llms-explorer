# LLMS Explorer public discovery continuation

Version 3. Delta records the downloads indexing correction for fleet task TASK-1518.

The production sitemap enumerates 200 canonical URLs. The generated Markdown aggregate enumerates 140 source pages. Ten are deliberately out of search, including the four legacy-domain account routes. Apply the rendered HTML index policy to the Markdown aggregate and check exact family membership against the sitemap on the final build. Preserve direct access to the standalone public account twins and legacy account behavior.

The repaired build contains 200 sitemap URLs and 130 Markdown source records. The built family, sitemap membership tests, site type check, and full site suite passed. The root Markdown summary describes resources that are still published.

The discovery release merged in PR 390. Production Cloudflare Pages deployment 69120b4f-9c12-494e-b748-fa127756f2b3 served all 200 sitemap URLs and 130 Markdown source records. The independent follow-up found that the download wildcard gave the installation landing page an HTTP noindex directive even though it published a canonical and appeared in the sitemap. Narrow the shared rules to built payloads under the route and verify both the landing and downloadable files.

The follow-up build generates one noindex rule per top-level download directory and one exact rule per direct file, leaving the landing page eligible for indexing. The local production build emitted byte-identical discovery files. The existing header policy remains shared by Cloudflare's static service and the Pages Function. The release check compares the exact production deployment and confirms the landing, raw payloads, protected account page, and discovery files.
