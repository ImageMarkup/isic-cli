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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python",
    ],
    python_requires=">=3.9",
    packages=find_packages(),
    entry_points={"console_scripts": ["isic = isic_cli.cli:main"]},
    install_requires=[
        "click",
        "django-s3-file-field-client",
        "girder-cli-oauth-client",
        "humanize",
        "isic-metadata>=0.0.6",
        "more-itertools",
        "numpy",
        "packaging",
        "pandas",
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
