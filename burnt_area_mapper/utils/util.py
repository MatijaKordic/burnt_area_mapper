import glob

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import shapely
from osgeo import gdal, osr
from shapely.ops import cascaded_union


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


def read_band_image(band="response", path="./data/"):
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
    a = f"{path}output_*.tiff"
    img = gdal.Open(glob.glob(a)[0])
    data = np.array(img.GetRasterBand(1).ReadAsArray())
    spatialRef = img.GetProjection()
    geoTransform = img.GetGeoTransform()
    targetprj = osr.SpatialReference(wkt=img.GetProjection())
    return data, spatialRef, geoTransform, targetprj


def min_cover_1(U):
    """
    This algorithm goes through all polygons and adds them to union_poly only if they're
    not already contained in union_poly.
    (in other words, we're only adding them to union_poly if they can increase the total area)

    performance:
    input: p1_large_ro_area.geojson with 2046 polygons
    output: 26 polygons
    time: O(n) where n is the total number of operations (intersections or unions)
    """
    _ = cascaded_union([shapely.wkt.loads(x["footprint"]) for x in U])
    union_poly = shapely.wkt.loads(U[0]["footprint"])
    union_parts = [
        U[0],
    ]
    for fp in U[1:]:
        p = shapely.wkt.loads(fp["footprint"])
        common = union_poly.intersection(p)
        if p.area - common.area < 0.001:
            pass
        else:
            union_parts.append(fp)
            union_poly = union_poly.union(p)
    return union_parts


def min_cover_2(U):
    """
    This algorithm computes a minimal covering set of the entire area.
    This means we're going to eliminate some of the images. We do this
    by checking the union of all polygons before and after removing
    each image.
    If by removing the image, the total area is the same, then the image
    can be eliminated since it didn't have any contribution.
    If the area decreases by removing the image, then it can stay.

    performance:
    input: p1_large_ro_area.geojson cu 2046 poligoane
    output: 13 polygons
    time: O(n^2) because we're executing cascaded_union 2046 times, and in the best
    case we're removing one polygon for each iteration, and cascaded_union is at least
    linear so we have quadratic complexity.
    """
    whole = cascaded_union([shapely.wkt.loads(x["footprint"]) for x in U])
    L = [shapely.wkt.loads(x["footprint"]) for x in U]
    V = []
    i = 0
    j = 0
    while j < len(U):
        without = cascaded_union(L[:i] + L[i + 1 :])
        if whole.area - without.area < 0.001:
            L.pop(i)
        else:
            V.append(U[j])
            i += 1
        j += 1

        if j % 20 == 0:
            print(i, j, len(L))
    return V


def get_gdf_bounds(gdf):
    bounds = gdf.total_bounds
    return bounds
