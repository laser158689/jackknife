"""
Data blade — flat file reader (CSV, Excel, Parquet).

Uses pandas + openpyxl + pyarrow. All I/O runs in a thread pool
executor to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path
from typing import Any

from jackknife.core.exceptions import DataConnectorError
from jackknife.core.logging import get_logger

try:
    import pandas as pd
except ImportError as exc:
    raise ImportError(
        "pandas is not installed. Enable the data-flat extra: poetry install -E data-flat"
    ) from exc

log = get_logger(__name__)

# Type alias so callers don't need to import pandas
DataFrame = pd.DataFrame


async def _run(fn: Any, *args: Any, **kwargs: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


class FlatFileReader:
    """
    Async reader for CSV, Excel (xlsx/xls), and Parquet files.

    All methods return a pandas DataFrame. Use .to_dict("records")
    to get a list of dicts if you don't want a pandas dependency downstream.
    """

    async def read_csv(
        self,
        path: Path | str,
        **kwargs: Any,
    ) -> DataFrame:
        """Read a CSV file into a DataFrame."""
        try:
            return await _run(pd.read_csv, str(path), **kwargs)
        except Exception as exc:
            raise DataConnectorError(f"Failed to read CSV {path!r}: {exc}") from exc

    async def read_excel(
        self,
        path: Path | str,
        sheet_name: str | int | None = 0,
        **kwargs: Any,
    ) -> DataFrame:
        """Read an Excel file into a DataFrame. Requires openpyxl."""
        try:
            return await _run(pd.read_excel, str(path), sheet_name=sheet_name, **kwargs)
        except Exception as exc:
            raise DataConnectorError(f"Failed to read Excel {path!r}: {exc}") from exc

    async def read_parquet(
        self,
        path: Path | str,
        **kwargs: Any,
    ) -> DataFrame:
        """Read a Parquet file into a DataFrame. Requires pyarrow."""
        try:
            return await _run(pd.read_parquet, str(path), **kwargs)
        except Exception as exc:
            raise DataConnectorError(f"Failed to read Parquet {path!r}: {exc}") from exc

    async def read(self, path: Path | str, **kwargs: Any) -> DataFrame:
        """
        Auto-detect format from extension and read.

        Supported: .csv, .xlsx, .xls, .parquet, .pq
        """
        p = Path(path)
        ext = p.suffix.lower()
        if ext == ".csv":
            return await self.read_csv(p, **kwargs)
        if ext in (".xlsx", ".xls"):
            return await self.read_excel(p, **kwargs)
        if ext in (".parquet", ".pq"):
            return await self.read_parquet(p, **kwargs)
        raise DataConnectorError(
            f"Unsupported file extension: {ext!r}. Supported: .csv, .xlsx, .xls, .parquet"
        )

    async def to_records(self, path: Path | str, **kwargs: Any) -> list[dict[str, Any]]:
        """Read a file and return as a list of dicts (no pandas dependency for callers)."""
        df = await self.read(path, **kwargs)
        return df.to_dict("records")  # type: ignore[return-value]

    async def write_csv(self, df: DataFrame, path: Path | str, **kwargs: Any) -> None:
        """Write a DataFrame to CSV."""
        try:
            await _run(df.to_csv, str(path), index=False, **kwargs)
        except Exception as exc:
            raise DataConnectorError(f"Failed to write CSV {path!r}: {exc}") from exc

    async def write_parquet(self, df: DataFrame, path: Path | str, **kwargs: Any) -> None:
        """Write a DataFrame to Parquet."""
        try:
            await _run(df.to_parquet, str(path), **kwargs)
        except Exception as exc:
            raise DataConnectorError(f"Failed to write Parquet {path!r}: {exc}") from exc
