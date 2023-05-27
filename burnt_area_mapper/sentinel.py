import tempfile
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge
from sentinelhub import (
    CRS,
    BBox,
    BBoxSplitter,
    DataCollection,
    MimeType,
    MosaickingOrder,
    SentinelHubDownloadClient,
    SentinelHubRequest,
    SHConfig,
    bbox_to_dimensions,
)
from shapely.geometry import box


class Sentinel:
    def __init__(self) -> None:
        self._auth()

    def _auth(self):
        """
        This function authorizes SentinelHub
        """
        self.config = SHConfig()
        if not self.config.sh_client_id or not self.config.sh_client_secret:
            print(
                "Warning! To use Process API, please provide the credentials (OAuth client ID and client secret)."
            )

    def _evalscript(self, model="regular"):
        """
        This function creates a script used to run SentinelHub services
        Inputs:
            model: type of run, regular is normalized burn ratio
        Returns:
            evalscript: script used for SentinelHub fetch
        """
        if model == "regular":
            evalscript = """
                //VERSION=3

                function setup() {
                    return {
                        input: [{
                            bands: ["B8A", "B12", "CLM", "CLP"]
                        }],
                        output: {
                            bands: 4
                        }
                    };
                }

                function evaluatePixel(sample) {
                    return [sample.B8A, sample.B12, sample.CLM, sample.CLP];
                }
            """
        elif model == "all_bands":
            evalscript = """
                //VERSION=3
                function setup() {
                    return {
                        input: [{
                            bands: ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12"],
                            units: "DN"
                        }],
                        output: {
                            bands: 13,
                            sampleType: "INT16"
                        }
                    };
                }

                function evaluatePixel(sample) {
                    return [sample.B01,
                            sample.B02,
                            sample.B03,
                            sample.B04,
                            sample.B05,
                            sample.B06,
                            sample.B07,
                            sample.B08,
                            sample.B8A,
                            sample.B09,
                            sample.B10,
                            sample.B11,
                            sample.B12];
                }
            """
        else:
            evalscript = """
                //VERSION=3

                function setup() {
                    return {
                        input: [{
                            bands: ["B12", "B8A", "B03"]
                        }],
                        output: {
                            bands: 3
                        }
                    };
                }

                function evaluatePixel(sample) {
                    return [sample.B12, sample.B8A, sample.B03];
                }
            """
            # B12, B8, B3
        return evalscript

    def _get_bbox(self):
        """
        This function gets the bounding box based on coords
        Returns:
            bbox: SentinelHub BBox
        """
        bbox = BBox(bbox=self.coords, crs=CRS.WGS84)
        return bbox

    def _get_size(self, bbox):
        """
        This function gets the size of the bbox.
        Inputs:
            bbox: bounding box of the area
        Returns:
            size: size of the area for the SentinelHub call
        """
        size = bbox_to_dimensions(bbox, resolution=10)
        return size

    def _get_sub_area(self, bbox, evalscript, start_date, end_date):
        """
        This
        Inputs:
            bbox: bbox of the investigative area
            evalscript: the script used to fetch imagery
            start_date: start date of the composite
            end_date: end date of the composite
        Returns:
            request: SentinelHub imagery request
            OR
            cloud_check: if time needs to be recalibrated
        """
        size = bbox_to_dimensions(bbox, resolution=10)
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(start_date, end_date),
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                )
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.TIFF)
            ],
            bbox=bbox,
            size=size,
            data_folder=tempfile.gettempdir(),
            config=self.config,
        )
        data = request.get_data(save_data=True)
        sentinel_image = data[0]
        cloud_check = self._check_clm(sentinel_image)
        if cloud_check == "recalibrate":
            return cloud_check
        return request

    def _split(self):
        """
        This function splits a bbox into a grid
        Returns:
            bbox_list: list of bounding boxes
        """
        # (minx, miny, maxx, maxy)
        shp_box = box(*self.coords)
        bbox_splitter = BBoxSplitter(
            [shp_box], CRS.WGS84, (5, 3)
        )  # bounding box will be split into grid of 5x3 bounding boxes
        bbox_list = bbox_splitter.get_bbox_list()
        return bbox_list

    def _get_imagery(self, start_date, end_date, coords, action):
        """
        This functin fetches the imagery from SentinelHub
        Inputs:
            start_date: start date of the composite
            end_date: end date of the composite
            coords: coordinates of the bbox
            action: whether it is pre or post time
        Returns:
            sentinel_image: imagery of the investigative area
            download_type: whether it is batch or single download
        """
        self.coords = coords
        self.action = action
        evalscript = self._evalscript()
        bbox = self._get_bbox()
        size = self._get_size(bbox)
        if int(size[1]) > 2500:
            image, download_type = self._batch_download(
                evalscript, start_date, end_date
            )
            return image, download_type
        request = SentinelHubRequest(
            data_folder="test_dir",
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(start_date, end_date),
                    mosaicking_order=MosaickingOrder.LEAST_CC,
                )
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.TIFF)
            ],
            bbox=bbox,
            size=size,
            config=self.config,
        )
        data = request.get_data(save_data=True)
        sentinel_image = data[0]
        cloud_check = self._check_clm(sentinel_image)
        if cloud_check == "recalibrate":
            return cloud_check, cloud_check
        download_type = "regular"
        return sentinel_image, download_type

    def _check_clm(self, image):
        """
        This function checks the cloud mask of the imagery
        Inputs:
            image: numpy ndarray imagery
        Returns:
            "recalibrate" if composite time needs to be extended else True
        """
        cloud_band = image[:, :, 2]
        _ = image[:, :, 3]
        # count occurrences of each unique value
        unique, counts = np.unique(cloud_band, return_counts=True)
        dict_counts = dict(zip(unique, counts))
        if dict_counts.get(1):
            value_1 = dict_counts[1]
            value_0 = dict_counts[0]
            value_255 = dict_counts[255]
            percentage_cloud = (
                (value_1 + value_255) / (value_0 + value_1 + value_255)
            ) * 100
            if percentage_cloud > 10:
                return "recalibrate"
        elif dict_counts.get(255) in dict_counts:
            value_0 = dict_counts[0]
            value_255 = dict_counts[255]
            percentage_cloud = ((value_255) / (value_0 + value_255)) * 100
            if percentage_cloud > 10:
                return "recalibrate"
        return

    def _batch_download(self, evalscript, start_date, end_date):
        """
        This function splits bbox, downloads and mosaics
        Inputs:
            evalscript:
            start_date: start date of the composite
            end_date: end date of the composite
        Returns:
            mosaic: final mosaic of the area
            download_type: whether it is batch or single download
        """
        bbox_list = self._split()

        sh_requests = [
            self._get_sub_area(bbox, evalscript, start_date, end_date)
            for bbox in bbox_list
        ]
        if sh_requests == "recalibrate":
            return sh_requests, sh_requests
        dl_requests = [request.download_list[0] for request in sh_requests]

        # download data with multiple threads
        _ = SentinelHubDownloadClient(config=self.config).download(
            dl_requests, max_threads=5
        )

        # get paths to tiffs
        data_folder = sh_requests[0].data_folder
        tiffs = [
            Path(data_folder) / req.get_filename_list()[0]
            for req in sh_requests
        ]
        elements = []
        for fp in tiffs:
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
            f"./data/output_{start_date}.tiff", "w", **out_meta
        ) as dest:
            dest.write(mosaic)
        download_type = "batch"
        return mosaic, download_type
