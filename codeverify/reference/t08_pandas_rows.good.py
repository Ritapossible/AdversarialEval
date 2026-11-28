import pandas as pd
def add_row(df, row):
    new = pd.DataFrame([row], columns=df.columns)
    return pd.concat([df, new], ignore_index=True) if len(df) else new.reset_index(drop=True)
