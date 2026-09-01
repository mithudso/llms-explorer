"""`/u/<user>/<slug>.llms/…` — the private served-files surface (master §6).

Thin, like every route module: `explorer_api.artifacts` owns paths, names and
headers; this file owns only *who is allowed to read* and *which status code
says so*.

Status-code contract, because each choice is security-relevant:

* **401** — nobody is signed in and no key was presented. The only code that
  invites a retry with credentials.
* **404** — somebody *is* identified but the artifact is not theirs, or the file
  does not exist, or the name is not part of the llms family. One code for all
  of them: a 403 on another user's path would confirm the artifact exists and
  turn `/u/` into an enumeration oracle over every account.
* **403** — the caller owns the path but presented a key without the `read`
  scope. Identity is already proven here, so saying "wrong scope" leaks nothing
  and is the only response the caller can act on.

Identity comes from either half of 15 §2's auth: the session cookie (a browser
reading its own account) or an `Authorization: Bearer llmsx_…` key (the CLI and
MCP clients). A key that is malformed, unknown or revoked is simply *not*
identity — it is never an error of its own, so a probe cannot tell "revoked"
from "never existed".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from .. import artifacts, keys as keys_module
from ..db import get_session
from ..models import User
from .auth import optional_user

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["artifacts"])

SessionDep = Annotated["AsyncSession", Depends(get_session)]
OptionalUser = Annotated[User | None, Depends(optional_user)]

#: 13 §5's access vocabulary: reading a file needs the `read` scope. A session
#: is the account itself and therefore carries every scope implicitly.
REQUIRED_SCOPE = "read"

BEARER = "bearer "


async def _identity(
    request: Request, session: AsyncSession, user: User | None
) -> tuple[str, frozenset[str]] | None:
    """`(user_id, scopes)` for the caller, or ``None`` when there is no caller.

    A presented key wins over a session cookie: a client that bothered to send
    one is asking to act as that key, and silently falling back to the browser's
    session would let a revoked key keep working inside a signed-in tab.
    """
    header = request.headers.get("Authorization") or ""
    if header.lower().startswith(BEARER):
        row = await keys_module.authenticate(session, header[len(BEARER):].strip())
        if row is None:
            return None
        return row.user_id, frozenset(row.scopes or ())
    if user is not None:
        return user.id, frozenset({REQUIRED_SCOPE, "run", "publish"})
    return None


@router.api_route(
    "/u/{user_id}/{artifact}/{relative:path}",
    methods=["GET", "HEAD"],
    name="user_artifact",
)
async def user_artifact(
    user_id: str,
    artifact: str,
    relative: str,
    request: Request,
    session: SessionDep,
    viewer: OptionalUser,
) -> Response:
    caller = await _identity(request, session, viewer)
    if caller is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "sign in or present an API key to read a private artifact",
            headers={"WWW-Authenticate": 'Bearer realm="llms-explorer"'},
        )
    caller_id, scopes = caller
    if caller_id != user_id:
        # Deliberately the same 404 a nonexistent artifact gets.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such artifact")
    if REQUIRED_SCOPE not in scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "this key has no read scope")

    stores_root = request.app.state.settings.stores_root
    try:
        slug = artifacts.parse_slug(artifact)
        served = artifacts.read(stores_root, user_id, slug, relative)
    except artifacts.NotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such artifact") from exc

    headers = artifacts.response_headers(
        served,
        describedby=artifacts.describedby_url(
            f"{request.url.scheme}://{request.url.netloc}", user_id, slug
        ),
    )
    # HEAD advertises the length it *would* have sent, as `llms_serve` does,
    # without writing the body.
    body = b"" if request.method == "HEAD" else served.data
    headers["Content-Length"] = str(len(served.data))
    return Response(content=body, media_type=served.content_type, headers=headers)
