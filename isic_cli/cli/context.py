from dataclasses import dataclass

from girder_cli_oauth_client import GirderCliOAuthClient

from isic_cli.session import IsicCliSession


@dataclass
class IsicContext:
    oauth: GirderCliOAuthClient
    session: IsicCliSession
    logged_in: bool
    env: str  # One of sandbox/dev/prod
    verbose: bool
