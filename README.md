
## Installation

### Conda
In root of repo run:
`conda env create -f environment.yml`

### Docker
Follow the steps of setting earthengine if not doing the install via Conda. 

In root of repo run:
`make build`

After building the image, run:
`make shell`


## SentinelHub setup

Before running sentinelhub, you need to authenticate. In order to authenticate, follow the steps outlined here for gcloud firstly:
https://sentinelhub-py.readthedocs.io/en/latest/configure.html 


## Test Run

The script takes three arguments: start date of the fire, end date of the fire and a bounding box in decimal degrees as minx, miny, max, and maxy. 
Based on the area size, it will split the area into a grid of requests if needed and create a mosaic.
Additionally, it takes into consideration amount of cloud cover and if it is higher > 10% of area, it will extend the period of composition by 7 days.  

`python main.py --start_date 2023-03-05 --end_date 2023-03-15 --coords 148.79697 -33.20518 150.05036 -32.64876`