from datetime import datetime
from typing import Tuple

import typer
from burnt_area import BurntArea
from utils.typer import OPTION_COORDS, OPTION_END_DATE, OPTION_START_DATE
from utils.util import array2raster, plot_burn_severity, read_band_image


def main(
    start_date: datetime = OPTION_START_DATE,
    end_date: datetime = OPTION_END_DATE,
    coords: Tuple[float, float, float, float] = OPTION_COORDS,
) -> None:
    final_image = BurntArea(
        fire_start=start_date,
        fire_end=end_date,
        imagery="Sentinel",
        coords=coords,
    ).nbr_process()
    (_, crs, geoTransform, _) = read_band_image()
    _ = array2raster(
        array=final_image,
        projection=crs,
        filename="output.tiff",
        geoTransform=geoTransform,
    )
    plot_burn_severity(image=final_image)


if __name__ == "__main__":
    typer.run(main)
