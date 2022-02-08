import os
from typing import Optional

from retryable_requests import RetryableSession


class IsicCliSession(RetryableSession):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # self.headers.update(
        #     {
        #         'User-agent': f'isic-cli/{__version__}',
        #     }
        # )


def get_session(headers: Optional[dict] = None) -> IsicCliSession:
    session = IsicCliSession(os.environ.get('API_URL', 'https://api.isic-archive.com/api/v2/'))
    if headers:
        session.headers.update(headers)
    return session
