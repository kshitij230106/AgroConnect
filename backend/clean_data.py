import pandas as pd

# Load Excel file
df = pd.read_excel("../data/Retailer Stock Sample data.xlsx")

# Show first 5 rows
print("\nFIRST 5 ROWS:\n")
print(df.head())

# Show all column names
print("\nCOLUMN NAMES:\n")
print(df.columns)

# Convert column names to lowercase
df.columns = df.columns.str.lower()

# Remove duplicate rows
df.drop_duplicates(inplace=True)
# Remove fully empty rows
df.dropna(how="all", inplace=True)
# Save cleaned file
df.to_csv("../data/cleaned_stock.csv", index=False)
print("\nData cleaned successfully!")