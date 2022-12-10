from collections import Counter
import sys
from typing import Iterable

import click

from isic_cli.cli.context import IsicContext


def suggest_guest_login(f):
    def decorator(ctx: IsicContext, **kwargs):
        if not ctx.user:
            click.echo(
                "Psst, you're logged out. Logging in with `isic user login` might return more data.\n",  # noqa: E501
                err=True,
            )
        f(ctx, **kwargs)

    return decorator


def require_login(f):
    def decorator(ctx: IsicContext, **kwargs):
        if not ctx.user:
            click.echo(
                "This command requires a logged in user, use the `isic user login` command to continue.",  # noqa: E501
                err=True,
            )
            sys.exit(1)

        f(ctx, **kwargs)

    return decorator


# This is memory inefficient but unavoidable since the CSV needs to look at ALL
# records to determine what the final headers should be. The alternative would
# be to iterate through all images_iterator twice (hitting the API each time).
def _extract_metadata(
    images: Iterable[dict], progress=None, task=None
) -> tuple[list[str], list[dict]]:
    metadata = []
    base_fields = ["isic_id", "attribution", "copyright_license"]
    metadata_fields = set()

    for image in images:
        metadata_fields |= set(image["metadata"]["acquisition"].keys())
        metadata_fields |= set(image["metadata"]["clinical"].keys())
        metadata.append(
            {
                **{
                    "isic_id": image["isic_id"],
                    "attribution": image["attribution"],
                    "copyright_license": image["copyright_license"],
                },
                **image["metadata"]["acquisition"],
                **image["metadata"]["clinical"],
            }
        )

        if progress is not None and task is not None:
            progress.update(task, advance=1)

    return base_fields + list(sorted(metadata_fields)), metadata


def get_attributions(images: Iterable[dict]) -> list[str]:
    counter = Counter(r["attribution"] for r in images)
    # sort by the number of images descending, then the name of the institution ascending
    attributions = sorted(counter.most_common(), key=lambda v: (-v[1], v[0]))
    # push anonymous attributions to the end
    attributions = sorted(attributions, key=lambda v: 1 if v[0] == "Anonymous" else 0)
    return [x[0] for x in attributions]
