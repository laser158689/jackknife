"""Tests for FlatFileReader."""

from __future__ import annotations

import pytest

from jackknife.blades.data.flat.reader import FlatFileReader


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
    from jackknife.core.exceptions import DataConnectorError

    bad_file = tmp_path / "data.xyz"
    bad_file.write_text("data")
    with pytest.raises(DataConnectorError, match="Unsupported"):
        await reader.read(bad_file)
