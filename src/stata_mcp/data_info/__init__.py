from typing import Type

from .base import DATA_INFO_REGISTRY, DataInfoBase
from .csv import CsvDataInfo
from .dta import DtaDataInfo
from .spss import SpssDataInfo
from .xlsx import ExcelDataInfo


def get_data_handler(extension: str) -> Type[DataInfoBase] | None:
    """
    Get the appropriate data handler class for a given file extension.

    Args:
        extension: File extension (e.g., 'csv', 'dta', 'xlsx')

    Returns:
        DataInfoBase subclass or None if extension is not supported
    """
    return DATA_INFO_REGISTRY.get(extension.lower())


__all__ = [
    "CsvDataInfo",
    "DtaDataInfo",
    "ExcelDataInfo",
    "SpssDataInfo",
    "DataInfoBase",
    "DATA_INFO_REGISTRY",
    "get_data_handler",
]
