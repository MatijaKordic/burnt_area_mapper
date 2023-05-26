from typing import Tuple
import typer
from utils.typer import (
    OPTION_START_DATE,
    OPTION_END_DATE,
    OPTION_COORDS
)
from typing_extensions import Annotated


from utils.util import (
    plot_image,
    array2raster,
    plot_burn_severity,
    read_band_image
)
from burnt_area import BurntArea
from datetime import datetime


def main(start_date: datetime = OPTION_START_DATE,
    end_date: datetime = OPTION_END_DATE,
    coords: Tuple[float, float, float, float] = OPTION_COORDS
) -> None:
    final_image = BurntArea(fire_start=start_date, fire_end=end_date, imagery="Sentinel", coords=coords).process()
    # plot_image(image=final_image)
    (pre_fire_b8a, crs, geoTransform, targetprj) = read_band_image()
    dnbr_tif, dnbr_tifBand = array2raster(array=final_image, projection=crs, filename="output.tiff", geoTransform=geoTransform)
    plot_burn_severity(image=final_image)



if __name__=="__main__":
    typer.run(main)
