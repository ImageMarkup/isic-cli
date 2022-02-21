import logging
import time
from typing import Optional

from retryable_requests import RetryableSession

logger = logging.getLogger(__name__)


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

    def request(self, *args, **kwargs):
        start = time.time()
        r = super().request(*args, **kwargs)
        end = time.time()

        # TODO: this is a little confusing because retries are included in
        # these times - maybe break it out.
        logger.debug(f'timing: {end - start}')

        if not r.ok:
            logger.debug(f'bad response: {r.text}')

        return r


def get_session(
    base_url: str = 'https://api.isic-archive.com/api/v2/', headers: Optional[dict] = None
) -> IsicCliSession:
    session = IsicCliSession(base_url)
    if headers:
        session.headers.update(headers)
    return session
