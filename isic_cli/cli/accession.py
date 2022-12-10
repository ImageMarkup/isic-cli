import json
from pathlib import Path
import sys

import click
from requests.exceptions import HTTPError
from rich.console import Console
from s3_file_field_client import S3FileFieldClient

from isic_cli.cli.context import IsicContext
from isic_cli.cli.types import CohortId
from isic_cli.cli.utils import require_login
from isic_cli.io.http import create_accession


@click.group(short_help="Manage accessions.")
@click.pass_obj
def accession(ctx):
    pass


@accession.command(name="upload", help="Upload an accession to a cohort.")
@click.argument("cohort_id", type=CohortId())
@click.argument(
    "accession",
    type=click.Path(file_okay=True, dir_okay=False, exists=True, allow_dash=False, path_type=Path),
)
@click.option("--json", "json_", default=False, is_flag=True, help="Format output as JSON.")
@click.pass_obj
@require_login
def upload(
    ctx: IsicContext,
    cohort_id: int,
    accession: Path,
    json_: bool,
):

    console = Console(stderr=True)
    with console.status("Uploading"):
        from isic_cli.cli import DOMAINS

        s3ff_client = S3FileFieldClient(f"{DOMAINS[ctx.env]}/api/v2/s3-upload/", ctx.session)

        with accession.open("rb") as file_stream:
            field_value = s3ff_client.upload_file(
                file_stream,
                accession.name,
                "ingest.Accession.original_blob",
            )

        try:
            result = create_accession(ctx.session, cohort_id, field_value)
        except HTTPError as e:
            if "non_field_errors" in e.response.json():
                click.secho(e.response.json()["non_field_errors"][0], fg="red", err=True)
                sys.exit(1)
            else:
                raise

    if json_:
        click.echo(json.dumps(result, indent=2))
    else:
        click.secho(f'Accession uploaded, id={result["id"]}.', fg="green")
        click.secho(
            f"Browse accessions: {DOMAINS[ctx.env]}/upload/{cohort_id}/browser/", fg="green"
        )
