import os

from ..edge import EdgeFactory, MiniSeedFactory


def get_edge_factory(
    data_type="variation",
    host=os.getenv("EDGE_HOST", "127.0.0.1"),
    interval="second",
    **kwargs
) -> EdgeFactory:
    return EdgeFactory(host=host, interval=interval, type=data_type, **kwargs)


def get_miniseed_factory(
    data_type="variation",
    host=os.getenv("EDGE_HOST", "127.0.0.1"),
    interval="second",
    **kwargs
) -> MiniSeedFactory:
    return MiniSeedFactory(host=host, interval=interval, type=data_type, **kwargs)
