from typing_extensions import Literal

DataInterval = Literal["tenhertz", "second", "minute", "hour", "day", "month"]
DataType = Literal[
    "adjusted", "definitive", "provisional", "quasi-definitive", "reported", "variation"
]
