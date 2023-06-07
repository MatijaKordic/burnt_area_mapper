import json
import os
import pathlib
import pprint
import re
import shutil
import zipfile
from glob import glob

import rasterio
import rasterio.mask
import rasterio.warp
import shapely
from dotenv import load_dotenv
from rasterio.merge import merge
from rasterio.warp import Resampling, calculate_default_transform, reproject
from sentinelsat import SentinelAPI
from shapely import box
from utils.util import min_cover_1, min_cover_2

load_dotenv(os.getenv("COPERNICUS_CREDENTIALS"))


class Sentinel_Sat:
    def __init__(self, start_date, end_date, input_file, debug=False):
        self.SENTINEL_USER = os.getenv("USERNAME")
        self.SENTINEL_PASS = os.getenv("PASSWORD")
        this_directory = os.getcwd()
        self.DL_DIR = this_directory + "/data/"
        self.INPUT_FILE = input_file
        self.START_DATE = start_date
        self.END_DATE = end_date
        self.DEBUG = debug

        if not os.path.exists(self.DL_DIR):
            os.mkdir(self.DL_DIR)

    def phase_1(self):
        self.api = SentinelAPI(self.SENTINEL_USER, self.SENTINEL_PASS)
        if type(self.INPUT_FILE) is tuple:
            self.aoi_footprint = box(*self.INPUT_FILE)
        else:
            self.aoi_footprint = self.INPUT_FILE["geometry"][0]

    def phase_2(self):
        self.api_products = self.api.query(
            area=self.aoi_footprint,
            date=(self.START_DATE, self.END_DATE),
            platformname="Sentinel-2",
            processinglevel="Level-2A",
            cloudcoverpercentage=(0, 10),
        )

    def phase_3(self):
        """
        We're doing the conversion from a GeoDataFrame to a list of dictionaries.

        After the conversion we intend to use the "footprint" and the "index" columns.

        This step is required because there are multiple products with the same footprint
        and later on we need the index in order to download the images from SentinelAPI.
        """

        self.product_df = self.api.to_dataframe(self.api_products)

        if len(self.product_df.index) == 0:
            raise Exception("No images for selected period")

        self.product_df = self.product_df.sort_values(
            ["cloudcoverpercentage", "ingestiondate"], ascending=[True, True]
        )
        self.tile_footprints = []
        for x in (
            self.product_df[["size", "processinglevel", "footprint"]]
            .T.to_dict()
            .items()
        ):
            self.tile_footprints.append({**x[1], "index": x[0]})

        if self.DEBUG:
            pprint(self.tile_footprints[:3])

    def phase_4(self):
        L1 = min_cover_1(self.tile_footprints)
        if self.DEBUG:
            print("{} tiles after the 1st reduction".format(len(L1)))
        L2 = min_cover_2(L1)
        if self.DEBUG:
            print("{} tiles after the 2nd reduction".format(len(L2)))
        self.reduced_footprints = L2

    def phase_5(self):
        dl_indexes = [x["index"] for x in self.reduced_footprints]
        self.api.download_all(dl_indexes, directory_path=self.DL_DIR)

        if self.DEBUG:
            pprint(dl_indexes)

        # self.api.download_all(self.api_products, directory_path=self.DL_DIR)

    def phase_6(self):
        """
        We're decompressing the archives unless they're already decompressed.
        """
        for p in pathlib.Path(self.DL_DIR).iterdir():
            p_dir = re.sub(".zip$", ".SAFE", str(p))
            if os.path.isfile(p) and not os.path.exists(p_dir):
                extract_path = os.path.dirname(p)
                print("Dezarhivare " + str(p))
                with zipfile.ZipFile(p, "r") as zip_ref:
                    zip_ref.extractall(extract_path)
                    os.remove(p)

    def phase_7(self):
        """
        Converting the .jp2 images to .tiff
        """

        def select_files(path, pattern, res_type=[]):
            L = []
            if len(res_type) > 0:
                for root, dirs, files in os.walk(path):
                    if len(dirs) == 0:
                        for f in files:
                            if pattern in f:
                                if "MSK" in f:
                                    pass
                                else:
                                    if "aux.xml" in f:
                                        pass
                                    else:
                                        if res_type in root and "B" in f:
                                            L.append(os.path.join(root, f))
                                        else:
                                            pass
                return L
            else:
                for root, dirs, files in os.walk(path):
                    if len(dirs) == 0:
                        for f in files:
                            if pattern in f:
                                if "MSK" in f:
                                    pass
                                else:
                                    if "aux.xml" in f:
                                        pass
                                    else:
                                        if "B" in f:
                                            L.append(os.path.join(root, f))
                                        else:
                                            pass
                return L

        def convert_to_tiff(paths):
            tiff_paths = []
            for p in paths:
                print("Converting " + p)
                with rasterio.open(p, mode="r") as src:
                    profile = src.meta.copy()
                    profile.update(driver="GTiff")

                    outfile = re.sub(".jp2", ".tiff", p)
                    with rasterio.open(outfile, "w", **profile) as dst:
                        dst.write(src.read())
                        tiff_paths.append(outfile)
            return tiff_paths

        self.jp2_paths = select_files(self.DL_DIR, ".jp2")
        self.tiffs = convert_to_tiff(self.jp2_paths)
        list_of_dirs = glob(f"{self.DL_DIR}/*/", recursive=True)
        list_of_subs = ["R10m", "R20m", "R60m"]
        # do a check if sub_dirs exist firstly and based on that call the func
        final_dict = {}
        for dir in list_of_dirs:
            dir_name = dir.split("/")[-2]
            sub_dirs = [x[0] for x in os.walk(dir)]
            for sub in sub_dirs:
                for res_type in list_of_subs:
                    if res_type in sub:
                        final_dict[dir] = res_type
        for dir in list_of_dirs:
            if "sentinel" in dir:
                pass
            else:
                dir_name = dir.split("/")[-2]
                sub_dirs = [x[0] for x in os.walk(dir)]
                if dir in final_dict:
                    for res_type in list_of_subs:
                        self.tiff_paths = select_files(dir, ".tiff", res_type)

                        self.phase8test(dir_name, res_type)
                        # self.phase_9(dir_name, res_type)
                        # self.phase_10(dir_name, res_type)
                else:
                    self.tiff_paths = select_files(dir, ".tiff")

                    self.phase8test(dir_name)
                    # self.phase_9(dir_name)
                    # self.phase_10(dir_name)
            # self.tiff_paths = convert_to_tiff(self.jp2_paths)
        return list_of_dirs

    def phase8test(self, dir_name, res_type="all"):
        self.tiff_paths.sort()
        raster_list = []
        for file in self.tiff_paths:
            raster = rasterio.open(file)
            raster_list.append(raster)

        config_dict = {}
        with open(rf"{self.DL_DIR}{dir_name}file-{res_type}.txt", "w") as fp:
            for idx, item in enumerate(self.tiff_paths):
                fp.write("%s\n" % item)
                if res_type == "all":
                    band = item.split("_")[-1].split(".")[0]
                else:
                    band = item.split("_")[-2].split("_")[-1]
                config_dict[band] = idx
        yo = f"gdalbuildvrt -input_file_list {self.DL_DIR}/{dir_name}file-{res_type}.txt -separate -overwrite {self.DL_DIR}/sentinel/{dir_name}-{res_type}merged1.tiff"
        os.system(yo)

        with open(f"./data/{dir_name}-{res_type}.json", "w") as outfile:
            json.dump(config_dict, outfile)

    def phase8ab(self, dirs):
        final_dirs = list(set(dirs))
        for dir in final_dirs:
            if "sentinel" in dir:
                files = glob(f"{self.DL_DIR}sentinel/S2*")
                for file in files:
                    os.remove(file)
            else:
                dir = dir[0:-1]
                try:
                    shutil.rmtree(dir)
                except Exception as e:
                    print(e)

    def phase8b(self):
        # iterate over same res files in sentinel folder
        # merge using rasterio
        raster_list = glob(f"{self.DL_DIR}/sentinel/*R20*.tiff")
        elements = []
        for fp in raster_list:
            src = rasterio.open(fp)
            elements.append(src)
        mosaic, out_trans = merge(elements)
        out_meta = src.meta.copy()
        out_meta.update(
            {
                "driver": "GTiff",
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
            }
        )
        with rasterio.open(
            f"./data/sentinel/output_cop_{self.START_DATE}.tiff",
            "w",
            **out_meta,
        ) as dest:
            dest.write(mosaic)
        download_type = "cop"
        return mosaic, download_type

    def phase_9(self):
        """
        Reprojecting the images to  EPSG:4326
        """

        dst_crs = "EPSG:4326"
        data = glob(f"{self.DL_DIR}sentinel/output_cop_*.tiff")

        for file in data:
            file_name = file.split("/")[-1].split(".")[0]
            print(file_name)
            with rasterio.open(file) as src:
                transform, width, height = calculate_default_transform(
                    src.crs, dst_crs, src.width, src.height, *src.bounds
                )
                kwargs = src.meta.copy()
                kwargs.update(
                    {
                        "crs": dst_crs,
                        "transform": transform,
                        "width": width,
                        "height": height,
                    }
                )
                with rasterio.open(
                    f"{self.DL_DIR}sentinel/{file_name}_4326.tiff",
                    mode="w",
                    **kwargs,
                ) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=src.transform,
                            src_crs=src.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.nearest,
                        )

    def phase_10(self, dir_name, res_type="all"):
        """
        We're clipping the area of interest.
        """

        with rasterio.open(self.MERGED_4326) as src:
            out_image, out_transform = rasterio.mask.mask(
                src, [shapely.wkt.loads(self.aoi_footprint)], crop=True
            )
            out_meta = src.meta
            out_meta.update(
                {
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                }
            )

            self.MERGED_REGION = os.path.join(
                self.DL_DIR, f"{dir_name}-{res_type}merged1_region.tiff"
            )
            with rasterio.open(self.MERGED_REGION, "w", **out_meta) as dest:
                dest.write(out_image)

                if self.DEBUG:
                    import matplotlib.pyplot as plt

                    fig, ax = plt.subplots(figsize=(14, 14))
                    from rasterio.plot import show

                    show(out_image, cmap="terrain", ax=ax)

    def ss_process(self):
        self.phase_1()
        self.phase_2()
        self.phase_3()
        self.phase_4()
        self.phase_5()
        self.phase_6()
        dirs = self.phase_7()
        mosaic, download_type = self.phase8b()
        self.phase8ab(dirs)
        # self.phase7a()
        # self.phase8test()
        # self.phase_10()
        return mosaic, download_type


# # download single scene by known product id
# api.download(<product_id>)

# # download all results from the search
# api.download_all(products)

# # convert to Pandas DataFrame
# products_df = api.to_dataframe(products)

# # GeoJSON FeatureCollection containing footprints and metadata of the scenes
# api.to_geojson(products)

# # GeoPandas GeoDataFrame with the metadata of the scenes and the footprints as geometries
# api.to_geodataframe(products)

# Get basic information about the product: its title, file size, MD5 sum, date, footprint and
# its download url
# api.get_product_odata(<product_id>)

# # Get the product's full metadata available on the server
# api.get_product_odata(<product_id>, full=True)
