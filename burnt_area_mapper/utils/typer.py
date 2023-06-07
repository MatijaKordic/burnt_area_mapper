import typer

OPTION_START_DATE = typer.Option(
    None, "--start_date", help="Start date of the fire"
)
OPTION_END_DATE = typer.Option(None, "--end_date", help="End date of the fire")
OPTION_COORDS = typer.Option(
    (0.0, 0.0, 0.0, 0.0),
    "--coords",
    help="Tuple of coordinates for the bounding box",
)
OPTION_GDF_BOUNDS = typer.Option(
    False,
    "--gdf_bounds/--no_gdf_bounds",
    help="True if a file is used to get the bounds",
)
OPTION_GDF_PATH = typer.Option(
    None, "--gdf_path", help="Path to where the vector data is stored"
)
OPTION_DOWNLOAD_BY = typer.Option(
    "CA",
    "--download_by",
    help="Downloading via SentinelHub (SH) or Copernicus API (CA)",
)
