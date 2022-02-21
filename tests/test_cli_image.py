import os
from pathlib import Path


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
