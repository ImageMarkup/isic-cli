import os

from girder_cli_oauth_client import GirderCliOAuthClient


def get_oauth_client():
    client = GirderCliOAuthClient(
        os.environ.get('ISIC_OAUTH_URL', 'https://api.isic-archive.com/oauth'),
        os.environ.get('ISIC_OAUTH_CLIENT_ID', 'RpCzc4hFjv5gOJdM2DM2nBdokOviOh5ne63Tpn7Q'),
    )
    return client
