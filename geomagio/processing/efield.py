import typer

from ..adjusted import AdjustedMatrix
from .derived import adjusted
from .factory import get_edge_factory
from .filters import minute_filter

app = typer.Typer()


def main():
    app()


@app.command(name="realtime")
def efield_realtime(
    observatory: str = "BOU",
    host: str = "127.0.0.1",
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """
    inverts polarity of 1Hz E-E/E-N
    filters 1Hz inverted/non-inverted E-E/E-N to 1 minute
    """
    adjusted(
        observatory=observatory,
        interval="second",
        input_factory=get_edge_factory(host=host, data_type="variation"),
        input_channels=["E-E", "E-N"],
        output_factory=get_edge_factory(host=host, data_type="adjusted"),
        output_channels=["E-E", "E-N"],
        matrix=AdjustedMatrix(
            matrix=[
                [-1, 0, 0],
                [0, -1, 0],
                [0, 0, 1],
            ],
        ),
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )
    minute_filter(
        observatory=observatory,
        channels=["E-E", "E-N"],
        input_factory=get_edge_factory(host=host, data_type="variation"),
        output_factory=get_edge_factory(host=host, data_type="variation"),
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )
    minute_filter(
        observatory=observatory,
        channels=["E-E", "E-N"],
        input_factory=get_edge_factory(host=host, data_type="adjusted"),
        output_factory=get_edge_factory(host=host, data_type="adjusted"),
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )


@app.command(name="hour")
def efield_hour(
    observatory: str = "BOU",
    host: str = "127.0.0.1",
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """filters 1 minute inverted/non-inverted E-E/E-N to 1 hour"""
    raise NotImplementedError("hour not implemented")


@app.command(name="day")
def efield_day(
    observatory: str = "BOU",
    host: str = "127.0.0.1",
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """filters 1 minute inverted/non-inverted E-E/E-N to 1 day"""
    raise NotImplementedError("day not implemented")
