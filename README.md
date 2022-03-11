# isic-cli
[![PyPI](https://img.shields.io/pypi/v/isic-cli)](https://pypi.org/project/isic-cli/)

A command line tool for interacting with the [ISIC Archive](https://isic-archive.com).

## Quickstart

``` sh
pip install isic-cli
isic user login
```


## Common use cases

### Downloading images

``` sh
isic image download  # downloads the entire archive, images and metadata, to images/

# optionally filter the results
isic image download --search 'diagnosis:melanoma' images/
isic image download --search 'age_approx:[5 TO 25] AND sex:male' images/
```


### Downloading metadata

``` sh
isic metadata download  # downloads the entire archive metadata to a csv

# find a collection to filter by
isic collection list  # grab the ID for the 2020 Challenge training set (70)
isic metadata download --collections 70
```
