# isic-cli

The official command line tool for interacting with the [ISIC Archive](https://isic-archive.com).

## Installation
- Download the [latest isic-cli release](https://github.com/ImageMarkup/isic-cli/releases/latest).
- Extract the executable to a location where it can be invoked from the command line.

If running on macOS, you may need to [add the executable to the list of trusted software](https://support.apple.com/guide/mac-help/apple-cant-check-app-for-malicious-software-mchleab3a043/mac) to launch isic-cli in the same way you would any other registered app.

## Common use cases

Note: `isic` will be `isic.exe` on Windows.

### Downloading images

``` sh
isic image download images/  # downloads the entire archive, images and metadata, to images/

# optionally filter the results
isic image download --search 'diagnosis:"basal cell carcinoma"' images/
isic image download --search 'age_approx:[5 TO 25] AND sex:male' images/
```


### Downloading metadata

``` sh
isic metadata download  # downloads the entire archive metadata to a csv

# find a collection to filter by
isic collection list  # grab the ID for the 2020 Challenge training set (70)
isic metadata download --collections 70
```
