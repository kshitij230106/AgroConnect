import pandas as pd

df = pd.read_excel("Request and Response of failures.xlsx")

for desc in df["description"].dropna().unique():
    print(desc)