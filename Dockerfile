FROM osgeo/gdal:ubuntu-small-3.1.2

WORKDIR /burnt_area_mapper

ARG USER_NAME=matija

# create new user
RUN useradd -ms /bin/bash ${USER_NAME}

# install system dependencies
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y \
    python3 \
    python3-dev \
    python3-pip \
    git

# install requirements
COPY requirements.txt /burnt_area_mapper/requirements.txt
WORKDIR /burnt_area_mapper
RUN pip3 install -r requirements.txt

# change user for safety
USER $USER_NAME

# create the de-pipeline folder
COPY --chown=$USER_NAME . /home/$USER_NAME/burnt_area_mapper
WORKDIR /home/$USER_NAME/burnt_area_mapper
