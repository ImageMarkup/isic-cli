from dataclasses import dataclass

from girder_cli_oauth_client import GirderCliOAuthClient

from isic_cli.session import IsicCliSession


@dataclass
class IsicContext:
    oauth: GirderCliOAuthClient
    session: IsicCliSession
    logged_in: bool
    verbose: bool
