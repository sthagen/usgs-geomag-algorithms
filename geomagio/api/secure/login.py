"""Module for authentication.

Requires sessions to store user information (recommend ..db.SessionMiddleware)


Configuration:
    uses environment variables:

    OPENID_CLIENT_ID      - application id, assigned by OIDC provider
    OPENID_CLIENT_SECRET  - application secret, assigned by OIDC provider
    OPENID_METADATA_URL   - url for OIDC provider information


Usage:

    current_user() - get user information if logged in

        def login_optional(user: Optional[User] = Depends(current_user))

    require_user() - require user login and group membership
                     NOTE: this is a function generator that must be called.

        def any_logged_in_user(user: User = Depends(require_user()))

        def admin_users_only(user: User = Depends(require_user(allowed_groups=["admin"])))

    router - APIRouter to be registered with FastAPI application:
        app.include_router(login.router)

        creates routes:
            /authorize  - callback from OpenIDConnect provider after authentication
            /login      - redirect to OpenIDConnect provider to authenticate
            /logout     - logout current user
            /user       - access current user information as json
"""
import logging
import os
from typing import Callable, List, Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException
import httpx
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import RedirectResponse


GITLAB_HOST = os.getenv("GITLAB_HOST", "code.usgs.gov")
GITLAB_API_URL = os.getenv("GITLAB_API_URL", f"https://{GITLAB_HOST}/api/v4")


class User(BaseModel):
    """Information about a logged in user."""

    email: str
    sub: str  # unique outh id
    groups: List[str] = []
    name: str = None
    nickname: str = None
    picture: str = None


async def current_user(request: Request) -> Optional[User]:
    """Get user information from gitlab access token or session(if currently logged in).
    Returns none if access token is not vald or user is not logged in.

    Usage example:
        user: Optional[User] = Depends(current_user)

    """
    user = None
    if "user" in request.session:
        user = User(**request.session["user"])
    elif "Authorization" in request.headers:
        user = await get_gitlab_user(token=request.headers["Authorization"])
        if user is not None:
            request.session["user"] = user.dict()
    return user


async def get_gitlab_user(token: str, url: str = GITLAB_API_URL) -> Optional[User]:
    header = {"PRIVATE-TOKEN": token}
    # request user information from gitlab api with access token

    try:
        # use httpx/async so this doesn't block other requests
        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(f"{url}/user", headers=header)
            userinfo = userinfo_response.json()
            user = User(
                email=userinfo["email"],
                sub=userinfo["id"],
                name=userinfo["name"],
                nickname=userinfo["username"],
                picture=userinfo["avatar_url"],
            )
            # use valid token to retrieve user's groups
            groups_response = await client.get(f"{url}/groups", headers=header)
            user.groups = [g["full_path"] for g in groups_response.json()]
            return user
    except Exception:
        logging.exception(f"Unable to get gitlab user")
        return None


def require_user(
    allowed_groups: List[str] = None,
) -> Callable[[Request, User], User]:
    """Create function to verifies user in allowed_groups

    Usage example:
        user: User = Depends(require_user(["admin"]))

    Parameters
    ----------
    allowed_groups: require user to be member of any group in list.
    """

    async def verify_groups(
        request: Request, user: Optional[User] = Depends(current_user)
    ) -> User:
        if not user:
            # not logged in
            raise HTTPException(status_code=401, detail=request.url_for("login"))
        if allowed_groups is not None and not any(
            g in user.groups for g in allowed_groups
        ):
            logging.info(
                f"user ({user.email}, sub={user.sub})"
                f" not member of any allowed group ({allowed_groups})"
            )
            raise HTTPException(403, detail="Forbidden")
        return user

    return verify_groups


oauth = OAuth()
# creates provider "oauth.openid"
oauth.register(
    name="openid",
    client_id=os.getenv("OPENID_CLIENT_ID"),
    client_secret=os.getenv("OPENID_CLIENT_SECRET"),
    server_metadata_url=os.getenv(
        "OPENID_METADATA_URL", f"https://{GITLAB_HOST}/.well-known/openid-configuration"
    ),
    client_kwargs={"scope": "openid email profile"},
)
# routes for login/logout
router = APIRouter()


@router.get("/authorize")
async def authorize(request: Request):
    """Authorize callback after authenticating using OpenID"""

    # finish login
    token = await oauth.openid.authorize_access_token(request)

    request.session["token"] = token
    # add user to session
    userinfo = await oauth.openid.userinfo(token=token)
    request.session["user"] = dict(userinfo)
    # redirect
    return RedirectResponse(
        url=request.session.pop(
            "after_authorize_redirect",
            # fall back to index
            request.url_for("index"),
        )
    )


@router.get("/login")
async def login(request: Request):
    """Redirect to OpenID provider."""
    redirect_uri = request.url_for("authorize")
    if "127.0.0.1" not in redirect_uri:
        # 127.0.0.1 used for local dev, all others use https
        redirect_uri = redirect_uri.replace("http://", "https://")
    # save original location
    if "Referer" in request.headers:
        request.session["after_authorize_redirect"] = request.headers["Referer"]
    # redirect to openid login
    return await oauth.openid.authorize_redirect(request, redirect_uri)


@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to index page."""
    request.session.pop("token", None)
    request.session.pop("user", None)
    return RedirectResponse(
        # referrer when set
        "Referer" in request.headers
        and request.headers["Referer"]
        # otherwise index
        or request.url_for("index")
    )


@router.get("/user")
async def user(request: Request, user: User = Depends(require_user())) -> User:
    """Get currently logged in user."""
    return user
