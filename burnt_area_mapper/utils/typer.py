import typer

OPTION_START_DATE = typer.Option(
    None, "--start_date", help="Start date of the fire"
)
OPTION_END_DATE = typer.Option(None, "--end_date", help="End date of the fire")
OPTION_COORDS = typer.Option(
    None, "--coords", help="Tuple of coordinates for the bounding box"
)
