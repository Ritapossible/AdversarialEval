import pandas as pd

def add_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    # Create a copy of the DataFrame to ensure the input is not modified
    new_df = df.copy()
    
    # Append the row to the DataFrame
    new_df = new_df.append(row, ignore_index=True)
    
    return new_df
