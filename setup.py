from __future__ import annotations

from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / "README.md"
with readme_file.open() as f:
    long_description = f.read()

setup(
    name="isic-cli",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    url="https://github.com/ImageMarkup/isic-cli",
    project_urls={
        "Bug Reports": "https://github.com/ImageMarkup/isic-cli/issues",
        "Source": "https://github.com/ImageMarkup/isic-cli",
    },
    author="Kitware, Inc.",
    author_email="kitware@kitware.com",
    keywords="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python",
    ],
    python_requires=">=3.10",
    packages=find_packages(),
    entry_points={"console_scripts": ["isic = isic_cli.cli:main"]},
    install_requires=[
        "click>=8.2.0",
        "django-s3-file-field-client>=1.0.0",
        # We expect girder-cli-oauth-client to drop oob support in the future
        "girder-cli-oauth-client<1.0.0",
        "humanize",
        "isic-metadata>=1.2.0",
        "more-itertools",
        "packaging",
        "requests",
        "retryable-requests",
        "rich",
        "sentry-sdk",
        "tenacity",
    ],
    extras_require={
        "dev": [
            "ipython",
            "tox",
        ]
    },
)
