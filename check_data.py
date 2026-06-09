import pandas as pd

df = pd.read_excel("Request and Response of failures.xlsx")

unique_desc = df["description"].dropna().unique()

with open("descriptions.txt", "w", encoding="utf-8") as f:
    for desc in unique_desc:
        f.write(str(desc) + "\n")

print("Done!")