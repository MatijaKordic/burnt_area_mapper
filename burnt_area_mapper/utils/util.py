import glob

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal, osr


def plot_burn_severity(image, name):
    # set colors for plotting and classes
    cmap = matplotlib.colors.ListedColormap(
        [
            "blue",
            "red",
            "orange",
            "green",
            "yellow",
            "brown",
            "violet",
            "purple",
        ]
    )
    cmap.set_over("purple")
    cmap.set_under("white")
    bounds = [0, 2, 3, 4, 5, 6, 7, 8, 9]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(
        figsize=(10, 10), subplot_kw={"xticks": [], "yticks": []}
    )
    cax = ax.imshow(image, cmap=cmap, norm=norm)
    plt.title("Burn Severity Map")
    cbar = fig.colorbar(
        cax,
        ax=ax,
        fraction=0.035,
        pad=0.04,
        ticks=[1, 2, 3, 4, 5, 6, 7, 8],
    )
    cbar.ax.set_yticklabels(
        [
            "Water",
            "Enhanced regrowth, high (post-fire)",
            "Enhanced regrowth, low (post-fire)",
            "Unburned",
            "Low Severity",
            "Moderate-low Severity",
            "Moderate-high Severity",
            "High Severity",
        ]
    )
    # plt.show()
    plt.savefig(f"./data/{name}.png", bbox_inches="tight")


def array2raster(array, geoTransform, projection, filename):
    """
    This function tarnsforms a numpy array to a geotiff projected raster
    input:  array                       array (n x m)   input array
            geoTransform                tuple           affine transformation coefficients
            projection                  string          projection
            filename                    string          output filename
    output: dataset                                     gdal raster dataset
            dataset.GetRasterBand(1)                    band object of dataset

    """
    pixels_x = array.shape[1]
    pixels_y = array.shape[0]

    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(
        filename,
        pixels_x,
        pixels_y,
        1,
        gdal.GDT_Int16,
    )
    dataset.SetGeoTransform(geoTransform)
    dataset.SetProjection(projection)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.FlushCache()  # Write to disk.
    return dataset, dataset.GetRasterBand(
        1
    )  # If you need to return, remenber to return  also t


def read_band_image(band="response", path="start"):
    """
    This function takes as input the Sentinel-2 band name and the path of the
    folder that the images are stored, reads the image and returns the data as
    an array
    input:   band           string            Sentinel-2 band name
             path           string            path of the folder
    output:  data           array (n x m)     array of the band image
             spatialRef     string            projection
             geoTransform   tuple             affine transformation coefficients
             targetprj                        spatial reference
    """
    # a = path+'*B'+band+'*.tiff'
    a = "./data/output_*.tiff"
    img = gdal.Open(glob.glob(a)[0])
    data = np.array(img.GetRasterBand(1).ReadAsArray())
    spatialRef = img.GetProjection()
    geoTransform = img.GetGeoTransform()
    targetprj = osr.SpatialReference(wkt=img.GetProjection())
    return data, spatialRef, geoTransform, targetprj


def get_gdf_bounds(gdf):
    bounds = gdf.total_bounds
    return bounds
