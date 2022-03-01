from dataclasses import dataclass
from typing import Optional

from girder_cli_oauth_client import GirderCliOAuthClient

from isic_cli.session import IsicCliSession


@dataclass
class IsicContext:
    oauth: GirderCliOAuthClient
    session: IsicCliSession
    env: str  # One of dev/sandbox/prod
    user: Optional[dict] = None
    verbose: Optional[bool] = False
