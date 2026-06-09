# count_categories.py

import pandas as pd

df = pd.read_excel("Request and Response of failures.xlsx")

for desc in df["description"].dropna().value_counts().head(30).items():
    print(desc)