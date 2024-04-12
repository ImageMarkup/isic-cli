from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from girder_cli_oauth_client import GirderCliOAuthClient

    from isic_cli.session import IsicCliSession


@dataclass
class IsicContext:
    oauth: GirderCliOAuthClient
    session: IsicCliSession
    env: str  # One of dev/sandbox/prod
    user: dict | None = None
    verbose: bool | None = False
