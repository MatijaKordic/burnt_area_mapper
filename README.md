# Intro to Repo

The repo serves to provide the analysis of fires using Earth Observation.

At the moment, the repo connects with SentinelHub to fetch the Sentinel-2 imagery based on which the analysis will be performed. 

So far, the picked algorithm for fire analysis is [Normalized Burn Ratio](https://www.un-spider.org/advisory-support/recommended-practices/recommended-practice-burn-severity/in-detail/normalized-burn-ratio). The repo plans to expand to support other fire algorithms in future. 

Runs are at the moment based on bounding box in decimal and the repo supports large area observations as it performs the split and mosaic if needed. However, this split needs to be further developed as at the moment it is hard coded matrix and it will be as per need in the upcoming versions. Additionally, a water mask is provided. 

The output is a TIFF and following JSON file with classification details and a png too. The png hasn't been tested if it matches 100% with the TIFF because it is based on internal settings and not so much on TIFF settings. 

## Installation

There are two possibilities for download:
1. Via SentinelHub -- requires registering an account thre
2. Via SentinelSat -- requires signing up at Copernicus Scihub (much easier and recommended)

### SentinelHub setup

Before running sentinelhub, you need to authenticate. In order to authenticate, follow the steps outlined here for gcloud firstly:
https://sentinelhub-py.readthedocs.io/en/latest/configure.html 

### Copernicus setup

For those not wanting to create an account at SentinelHub, you can use Copernicus. 

Go to this [link](https://scihub.copernicus.eu/dhus/#/home) and create an account. It is fairly straight-forward. Now, you need to add your username and password to the `.env` file. 


#### 1.2 .env file

The file contains your username and password for Copernicus API. The `.env` file is always held locally to avoid pushing sensitive information on Github, and it is added to the `.gitignore` file so no need to worry about it. Create a copy from the `.env-sample` file and simply replace the values in it. Leave the `.env` file in the root of the repository.

USERNAME = "<copernicus_api_username>"  
PASSWORD = "<copernicus_api_password>"

On Mac:

- if you use bash:
`echo 'export COPERNICUS_CREDENTIALS="/Users/<your_username>/rest_of_path/.env"' >> ~/.bash_profile`
- if you use zsh:
`echo 'export COPERNICUS_CREDENTIALS="/Users/<your_username>/rest_of_path/.env"' >> ~/.zprofile`

### Conda
In root of repo run:
`conda env create -f environment.yml`

### Docker
Follow the steps of setting earthengine if not doing the install via Conda. 

In root of repo run:
`make build`

After building the image, run:
`make shell`

### Pre-commit

Once in the root of repository, run:
`pre-commit install`

This will install pre-commit hooks. 

Later you can the following prior to commiting but after git add:

`pre-commit run --all-files`

### Commitizen

To install Commitizen for this repo only, in the repo root run:

`pip install -U commitizen`

To install across the system:

`pip install --user -U Commitizen`

Commitizen is used for commiting as:

`cz c`

The repo is following semantic versioning as 0.0.0:
- major (major repo change)
- minor (feature)
- patch (bug fix)

If the commit is any of these and not a build or refactor run:

`cz bump`

This will update the CHANGELOG.md and VERSION files of the repo. Make sure to commit them. 


## Test Run

The script takes several arguments: start date of the fire, end date of the fire and a bounding box in decimal degrees as minx, miny, max, and maxy. 
Based on the area size, it will split the area into a grid of requests if needed and create a mosaic.
Additionally, it takes into consideration amount of cloud cover and if it is higher > 10% of area, it will extend the period of composition by 7 days.  
Also, `download_by` argument refers to Copernicus API (CA) and SentinelHub (SH). So `--download_by CA` would download via Copernicus API. 

`python main.py --start_date 2023-03-05 --end_date 2023-03-15 --coords 148.79697 -33.20518 150.05036 -32.64876 --download_by SH`

To run using a shapefile example:

`python main.py --start_date 2023-03-05 --end_date 2023-03-15 --gdf_bounds --gdf_path path_to_folder/file.shp --download_by CA`


## Credits

Special thanks to [sentinel-mosaic](https://github.com/wsdookadr/sentinel-mosaic/tree/master) package as a good chunk of the code for Copernicus API has been taken from their existing code. The code has been extracted directly from the package to fit in within the workflow a bit differently. 