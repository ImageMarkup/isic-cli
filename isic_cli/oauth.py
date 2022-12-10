from girder_cli_oauth_client import GirderCliOAuthClient


def get_oauth_client(
    oauth_url: str = "https://api.isic-archive.com/oauth",
    client_id: str = "RpCzc4hFjv5gOJdM2DM2nBdokOviOh5ne63Tpn7Q",
):
    client = GirderCliOAuthClient(oauth_url, client_id)
    return client
