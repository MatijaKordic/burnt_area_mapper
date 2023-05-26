.ONESHELL:
SHELL=/bin/bash

shell:
	docker-compose run --rm --service-ports burnt_area_mapper bash
build:
	docker build -t burnt_area_mapper --build-arg USER_ID=$$(id -u) .