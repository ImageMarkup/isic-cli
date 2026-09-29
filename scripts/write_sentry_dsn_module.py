"""Write a module that embeds the Sentry DSN into the PyInstaller binary."""

from __future__ import annotations

import os
from pathlib import Path
import sys

SENTRY_DSN_ENV_VAR = "ISIC_CLI_SENTRY_DSN"


def main():
    module_path = Path(sys.argv[1])
    dsn = os.environ.get(SENTRY_DSN_ENV_VAR)

    if not dsn:
        raise SystemExit(f"{SENTRY_DSN_ENV_VAR} must be set to embed it in the binary.")

    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(f"SENTRY_DSN = {dsn!r}\n")


if __name__ == "__main__":
    main()
