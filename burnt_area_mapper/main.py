from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import typer
from burnt_area import BurntArea
from utils.io import GeospatialRead
from utils.typer import (
    OPTION_COORDS,
    OPTION_DOWNLOAD_BY,
    OPTION_END_DATE,
    OPTION_GDF_BOUNDS,
    OPTION_GDF_PATH,
    OPTION_START_DATE,
)
from utils.util import array2raster, plot_burn_severity, read_band_image


def main(
    start_date: datetime = OPTION_START_DATE,
    end_date: datetime = OPTION_END_DATE,
    download_by: str = OPTION_DOWNLOAD_BY,
    coords: Optional[Tuple[float, float, float, float]] = OPTION_COORDS,
    gdf_bounds: Optional[bool] = OPTION_GDF_BOUNDS,
    gdf_path: Optional[Path] = OPTION_GDF_PATH,
) -> None:
    if gdf_bounds:
        file = GeospatialRead(gdf_path)._read_file()
        final_image = BurntArea(
            fire_start=start_date,
            fire_end=end_date,
            imagery="Sentinel",
            coords=file,
            provider=download_by,
        ).nbr_process()
        if download_by == "CA":
            (_, crs, geoTransform, _) = read_band_image(
                path="./data/sentinel/"
            )
        else:
            (_, crs, geoTransform, _) = read_band_image()
    else:
        final_image = BurntArea(
            fire_start=start_date,
            fire_end=end_date,
            imagery="Sentinel",
            coords=coords,
            provider=download_by,
        ).nbr_process()
        if download_by == "CA":
            (_, crs, geoTransform, _) = read_band_image(
                path="./data/sentinel/"
            )
        else:
            (_, crs, geoTransform, _) = read_band_image()
    _ = array2raster(
        array=final_image,
        projection=crs,
        filename="./data/output.tiff",
        geoTransform=geoTransform,
    )
    plot_burn_severity(image=final_image, name=f"Fire_{start_date}_{end_date}")


if __name__ == "__main__":
    typer.run(main)
