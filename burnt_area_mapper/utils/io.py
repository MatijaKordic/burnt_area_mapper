import geopandas as gpd
import rioxarray as rio
import xarray as xr


class GeospatialRead:
    def __init__(self, file):
        self.file = file
        self.core_type = self._get_core_type()
        self.driver = self._get_file_type()

    def _get_file_type(self, file_type=None):
        if file_type is None:
            file_data = self.file.parts
            file_type_f = file_data[-1].split(".")[-1]
        else:
            file_type_f = file_type
        return file_type_f

    def _get_core_type(self):
        vector_files = ["shp", "gpkg", "gdb", "geojson"]
        file_data = self.file.parts[-1]
        bits = file_data.split(".")[-1]
        if bits in vector_files:
            core_type = "vector"
        elif "feather" in vector_files:
            core_type = "feather"
        else:
            core_type = "raster"
        return core_type

    def _read_file(self):
        if self.driver == "nc":
            file = self._read_nc()
        elif self.core_type == "feather":
            file = self._read_feather()
        elif self.driver == "tif":
            file = self._read_tif()
        elif self.core_type == "vector":
            file = self._read_vector(driver=self.driver)
            return file
        else:
            raise ValueError("File type not supported")

    def _read_nc(self):
        raster = xr.open_dataarray(self.file)
        return raster

    def _read_feather(self):
        raster = gpd.read_feather(self.file)
        if raster is None:
            raster = raster.to_crs("EPSG:4326")
        else:
            raster = raster
        return raster

    def _read_tif(self):
        raster = rio.open_rasterio(self.file)
        return raster

    def _read_vector(self, driver="shp"):
        vector = gpd.read_file(filename=self.file)
        return vector
