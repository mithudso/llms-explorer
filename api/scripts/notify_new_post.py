"""Mail every confirmed subscriber about a newly published post.

Not triggered by anything automatically — run it by hand (or from a publish
script) after a post lands in ``site/src/content/blog``:

    uv run --directory api python scripts/notify_new_post.py \\
        "Post Title" "https://llms-explorer.com/blog/post-slug/"

Requires the same environment as the API itself (``DATABASE_URL``, …); see
``api/.env.example``. Without ``SMTP_HOST`` set, each send is logged instead
of mailed (see ``explorer_api/notify.py``).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from explorer_api.db import create_engine, create_session_factory  # noqa: E402
from explorer_api.notify import notify_new_post  # noqa: E402
from explorer_api.settings import Settings  # noqa: E402


async def _main(title: str, url: str) -> int:
    settings = Settings.load()
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        count = await notify_new_post(session, settings, title=title, url=url)
    await engine.dispose()
    return count


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="Post title, as it should appear in the notice")
    parser.add_argument("url", help="Absolute URL of the published post")
    args = parser.parse_args()
    count = asyncio.run(_main(args.title, args.url))
    print(f"notified {count} subscriber(s)")


if __name__ == "__main__":
    main()
