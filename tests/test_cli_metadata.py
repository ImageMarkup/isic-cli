import re


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
            [
                {
                    'isic_id': 'ISIC_0000000',
                    'attribution': 'Foo',
                    'copyright_license': 'CC-0',
                    'metadata': {'sex': 'male', 'diagnosis': 'melanoma'},
                }
            ]
        ),
    )

    result = cli_run(['metadata', 'download'])

    assert result.exit_code == 0, result.exception
    assert re.search(r'ISIC_0000000.*Foo.*CC-0.*melanoma.*male', result.output), result.output
