import polars as pl
from datetime import datetime

df = pl.DataFrame(
    {
        "integer": [1, 2, 3],
        "date": [
            datetime(2022, 1, 1),
            datetime(2022, 1, 2),
            datetime(2022, 1, 3),
        ],
        "float": [4.0, 5.0, 6.0],
    }
)
print(df)

x = df.select(pl.col("integer"), pl.col("date")).limit(1)
print(x)
