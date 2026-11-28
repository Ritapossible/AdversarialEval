1. ```requirements.txt```
```
pandas==2.2.0
```

2. ```python
import pandas as pd

def add_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    # Create a copy of the DataFrame to avoid modifying the input
    new_df = df.copy()
    
    # Append the row to the DataFrame
    new_df = new_df.append(row, ignore_index=True)
    
    return new_df
```