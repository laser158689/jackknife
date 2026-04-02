"""Tests for FlatFileReader."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from jackknife.blades.data.flat.reader import FlatFileReader
from jackknife.core.exceptions import DataConnectorError


@pytest.fixture
def reader():
    return FlatFileReader()


async def test_read_csv(reader, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("name,age\nAlice,30\nBob,25\n")
    df = await reader.read_csv(csv_file)
    assert len(df) == 2
    assert list(df.columns) == ["name", "age"]


async def test_read_parquet(reader, tmp_path):
    import pandas as pd

    df_src = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
    parquet_file = tmp_path / "data.parquet"
    df_src.to_parquet(parquet_file, index=False)

    df = await reader.read_parquet(parquet_file)
    assert len(df) == 3
    assert list(df.columns) == ["x", "y"]


async def test_auto_detect_csv(reader, tmp_path):
    csv_file = tmp_path / "auto.csv"
    csv_file.write_text("col1,col2\n1,2\n3,4\n")
    df = await reader.read(csv_file)
    assert len(df) == 2


async def test_to_records(reader, tmp_path):
    csv_file = tmp_path / "records.csv"
    csv_file.write_text("id,value\n1,foo\n2,bar\n")
    records = await reader.to_records(csv_file)
    assert len(records) == 2
    assert records[0]["id"] == 1
    assert records[0]["value"] == "foo"


async def test_write_and_read_csv(reader, tmp_path):
    import pandas as pd

    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    out = tmp_path / "out.csv"
    await reader.write_csv(df, out)
    df2 = await reader.read_csv(out)
    assert list(df2["a"]) == [1, 2]


async def test_unsupported_extension(reader, tmp_path):
    bad_file = tmp_path / "data.xyz"
    bad_file.write_text("data")
    with pytest.raises(DataConnectorError, match="Unsupported"):
        await reader.read(bad_file)


async def test_read_csv_error(reader, tmp_path):
    """Covers lines 52-53: DataConnectorError on CSV read failure."""
    with patch("jackknife.blades.data.flat.reader.pd.read_csv", side_effect=OSError("disk error")):
        with pytest.raises(DataConnectorError, match="Failed to read CSV"):
            await reader.read_csv(tmp_path / "bad.csv")


async def test_read_excel_happy(reader, tmp_path):
    """Covers lines 62-63: successful Excel read (.xlsx)."""
    import pandas as pd

    df_src = pd.DataFrame({"col": [1, 2]})
    xlsx = tmp_path / "data.xlsx"
    df_src.to_excel(xlsx, index=False)
    df = await reader.read_excel(xlsx)
    assert list(df["col"]) == [1, 2]


async def test_read_excel_error(reader, tmp_path):
    """Covers lines 62-65: DataConnectorError on Excel read failure."""
    with patch(
        "jackknife.blades.data.flat.reader.pd.read_excel", side_effect=OSError("no openpyxl")
    ):
        with pytest.raises(DataConnectorError, match="Failed to read Excel"):
            await reader.read_excel(tmp_path / "bad.xlsx")


async def test_read_parquet_error(reader, tmp_path):
    """Covers lines 75-76: DataConnectorError on Parquet read failure."""
    with patch(
        "jackknife.blades.data.flat.reader.pd.read_parquet", side_effect=OSError("bad file")
    ):
        with pytest.raises(DataConnectorError, match="Failed to read Parquet"):
            await reader.read_parquet(tmp_path / "bad.parquet")


async def test_auto_detect_xls(reader, tmp_path):
    """Covers line 89: .xls extension dispatches to read_excel."""
    import pandas as pd

    df = pd.DataFrame({"v": [42]})
    xls_file = tmp_path / "data.xls"
    df.to_excel(xls_file, index=False, engine="xlwt" if False else None)
    # Use mock to avoid xlwt dependency: just mock read_excel on the instance
    reader.read_excel = AsyncMock(return_value=df)
    result = await reader.read(tmp_path / "data.xls")
    reader.read_excel.assert_called_once()
    assert result is df


async def test_auto_detect_pq(reader, tmp_path):
    """Covers line 91: .pq extension dispatches to read_parquet."""
    import pandas as pd

    df_src = pd.DataFrame({"n": [1, 2]})
    pq_file = tmp_path / "data.pq"
    df_src.to_parquet(pq_file, index=False)
    df = await reader.read(pq_file)
    assert list(df["n"]) == [1, 2]


async def test_write_csv_error(reader, tmp_path):
    """Covers lines 105-106: DataConnectorError on CSV write failure."""
    import pandas as pd

    df = pd.DataFrame({"a": [1]})
    with patch.object(df, "to_csv", side_effect=OSError("disk full")):
        with pytest.raises(DataConnectorError, match="Failed to write CSV"):
            await reader.write_csv(df, tmp_path / "out.csv")


async def test_write_parquet_happy(reader, tmp_path):
    """Covers lines 110-111: write_parquet happy path."""
    import pandas as pd

    df = pd.DataFrame({"x": [10, 20]})
    out = tmp_path / "out.parquet"
    await reader.write_parquet(df, out)
    df2 = await reader.read_parquet(out)
    assert list(df2["x"]) == [10, 20]


async def test_write_parquet_error(reader, tmp_path):
    """Covers lines 112-113: DataConnectorError on Parquet write failure."""
    import pandas as pd

    df = pd.DataFrame({"a": [1]})
    with patch.object(df, "to_parquet", side_effect=OSError("no space")):
        with pytest.raises(DataConnectorError, match="Failed to write Parquet"):
            await reader.write_parquet(df, tmp_path / "out.parquet")
