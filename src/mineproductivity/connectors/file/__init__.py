"""File-based reference connectors: :class:`CSVConnector`, :class:`ExcelConnector`."""

from __future__ import annotations

from mineproductivity.connectors.file.csv_connector import CSVConnector
from mineproductivity.connectors.file.excel_connector import ExcelConnector

__all__ = ["CSVConnector", "ExcelConnector"]
