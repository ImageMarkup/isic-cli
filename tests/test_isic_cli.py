import os
from pathlib import Path
import re


def test_base_command(cli_run):
    result = cli_run()

    assert result.exit_code == 0
    assert 'Usage: ' in result.output

    # The output of isic with no args and isic with --help should be identical
    help_result = cli_run(['--help'])
    assert help_result.exit_code == 0
    assert help_result.output == result.output


def test_collection_list(cli_run, mocker):
    mocker.patch(
        'isic_cli.cli.collection.get_collections',
        return_value=iter(
            [
                {
                    'id': 5,
                    'name': 'foo',
                    'public': True,
                    'official': False,
                    'doi': None,
                }
            ]
        ),
    )

    result = cli_run(['collection', 'list'])

    assert result.exit_code == 0, result.exception
    assert re.search(r'5.*foo.*True.*False', result.output), result.output


def test_metadata_validate(runner, cli_run):
    with runner.isolated_filesystem():
        with open('foo.csv', 'w') as f:
            f.write('diagnosis,sex\nfoo,bar')

        result = cli_run(['metadata', 'validate', 'foo.csv'])

    assert result.exit_code == 1, result.exception
    assert re.search(r'Invalid diagnosis.*foo', result.output), result.output
    assert re.search(r'Invalid sex.*bar', result.output), result.output


def test_metadata_download(cli_run, mocker):
    mocker.patch('isic_cli.cli.metadata.get_num_images', return_value=1)
    mocker.patch(
        'isic_cli.cli.metadata.get_images',
        return_value=iter(
            [{'isic_id': 'ISIC_0000000', 'metadata': {'sex': 'male', 'diagnosis': 'melanoma'}}]
        ),
    )

    result = cli_run(['metadata', 'download'])

    assert result.exit_code == 0, result.exception
    assert re.search(r'ISIC_0000000.*melanoma.*male', result.output), result.output


def test_image_download(runner, cli_run, mocker):
    with runner.isolated_filesystem():

        def _download_image_side_effect(*args, **kwargs):
            base = Path('images')
            with open(base / 'ISIC_0000000.JPG', 'wb') as f:
                f.write(b'12345')

            with open(base / 'ISIC_0000000.json', 'w') as f:
                f.write('12345')

        mocker.patch('isic_cli.cli.image.get_num_images', return_value=1)
        mocker.patch(
            'isic_cli.cli.image.get_images',
            return_value=iter(
                [{'isic_id': 'ISIC_0000000', 'metadata': {'sex': 'male', 'diagnosis': 'melanoma'}}]
            ),
        )
        mocker.patch('isic_cli.cli.image.download_image', side_effect=_download_image_side_effect)

        result = cli_run(['image', 'download'])

        assert result.exit_code == 0, result.exception
        assert os.path.exists('images/ISIC_0000000.JPG')
        assert os.path.exists('images/ISIC_0000000.json')
