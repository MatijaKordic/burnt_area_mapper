import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from typing import Any, Optional, Tuple
from osgeo import gdal
import glob
from osgeo import osr
import math
from datetime import timedelta, datetime


def plot_image(
    image: np.ndarray, factor: float = 1.0, clip_range: Optional[Tuple[float, float]] = None, **kwargs: Any
) -> None:
    """Utility function for plotting RGB images."""
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(15, 15))
    if clip_range is not None:
        ax.imshow(np.clip(image * factor, *clip_range), **kwargs)
    else:
        ax.imshow(image * factor, **kwargs)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.savefig('foo_2.png')

def plot_burn_severity(image):
    #set colors for plotting and classes
    cmap = matplotlib.colors.ListedColormap(['red', 'orange', 'green','yellow','orange','red','purple'])
    cmap.set_over('purple')
    cmap.set_under('white')
    bounds = [-5.5, -0.25, -0.1, 0.1, 0.27, 0.440, 0.660, 1.3]        
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)  

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'xticks': [], 'yticks': []})
    cax = ax.imshow(image, cmap=cmap, norm = norm)
    plt.title('Burn Severity Map')
    cbar = fig.colorbar(cax, ax=ax, fraction=0.035, pad=0.04, ticks=[-5.5, -0.25, -0.1, 0.1, 0.27, 0.44, 0.66])
    cbar.ax.set_yticklabels(['Enhanced regrowth, high (post-fire)', 'Enhanced regrowth, low (post-fire)', 'Unburned', 'Low Severity', 'Moderate-low Severity', 'Moderate-high Severity', 'High Severity'])
    # plt.show()
    plt.savefig("foo_3.png", bbox_inches="tight") 


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
    
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(
        filename,
        pixels_x,
        pixels_y,
        1,
        gdal.GDT_Float64, )
    dataset.SetGeoTransform(geoTransform)
    dataset.SetProjection(projection)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.FlushCache()  # Write to disk.
    return dataset, dataset.GetRasterBand(1)  #If you need to return, remenber to return  also t

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
    targetprj = osr.SpatialReference(wkt = img.GetProjection())
    return data, spatialRef, geoTransform, targetprj

def reclassify(array):
    """
    This function reclassifies an array
    input:  array           array (n x m)    input array
    output: reclass         array (n x m)    reclassified array
    """
    reclass = np.zeros((array.shape[0],array.shape[1]))
    for i in range(0,array.shape[0]):
        for j in range(0,array.shape[1]):
            if math.isnan(array[i,j]):
                reclass[i,j] = np.nan
            elif array[i,j] < 0.1:
                reclass[i,j] = 1
            elif array[i,j] < 0.27:
                 reclass[i,j] = 2
            elif array[i,j] < 0.44:
                 reclass[i,j] = 3
            elif array[i,j] < 0.66:
                 reclass[i,j] = 4
            else:
                reclass[i,j] = 5
                
    return reclass

def recalibrate_time(time, action, days_to_subtract=7):
        if action == "+":
            end_date = datetime.date(time + timedelta(days=days_to_subtract))
            start_date = datetime.date(time)
        elif action == "-":
            start_date = datetime.date(time - timedelta(days=days_to_subtract))
            end_date = datetime.date(time)
        else:
            "No es buone de nada!"
        return start_date, end_date

def calc_burnt_area(image):
    reclass = reclassify(image.ReadAsArray())
    k = ['Unburned hectares', 'Low severity hectares', 'Moderate-low severity hectares', 'Moderate-high severity hectares', 'High severity']
    for i in range(1,6):
        x = reclass[reclass == i]
        l= x.size*0.04
        print("%s: %.2f" % (k[i-1], l))