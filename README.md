
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

`python main.py --start_date 2023-03-05 --end_date 2023-03-15 --coords 148.79697 -33.20518 150.05036 -32.64876`