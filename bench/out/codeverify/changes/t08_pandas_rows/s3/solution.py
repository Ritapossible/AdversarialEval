import pandas as pd

def add_row(df: pd.DataFrame, row: dict) -> pd.DataFrame:
    """
    Append a row to the DataFrame and return a new DataFrame with a fresh index.
    
    :param df: Original DataFrame to which the row will be appended.
    :param row: Dictionary representing the row to append. Missing columns become NaN.
    :return: New DataFrame with the appended row and fresh 0..n-1 index.
    """
    # Create a new DataFrame from the original one to avoid modifying it
    new_df = df.copy()
    
    # Append the new row, filling missing columns with NaN
    new_df.loc[len(new_df)] = pd.Series(row, index=new_df.columns).reindex(new_df.columns, fill_value=pd.NA)
    
    return new_df
