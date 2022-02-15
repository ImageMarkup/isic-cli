from typing import Optional

from retryable_requests import RetryableSession


class IsicCliSession(RetryableSession):
    def __init__(self, *args, **kwargs) -> None:
        from isic_cli.utils.version import get_version

        super().__init__(*args, **kwargs)

        self.headers.update(
            {
                'Accept': 'application/json',
                'User-agent': f'isic-cli/{get_version()}',
            }
        )


def get_session(
    base_url: str = 'https://api.isic-archive.com/api/v2/', headers: Optional[dict] = None
) -> IsicCliSession:
    session = IsicCliSession(base_url)
    if headers:
        session.headers.update(headers)
    return session
