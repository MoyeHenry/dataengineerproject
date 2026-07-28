# Import libraries for file handling, data cleaning, and database loading
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, Date

# # Align DataFrame column headers to the left when printing.
# pd.set_option("display.colheader_justify", "left")

# Define source file, target table, and PostgreSQL connection.
BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_FILE = BASE_DIR / "data" / "ecommerce_sales.csv"
TABLE_NAME = "ecommerce_sales"
engine = create_engine("postgresql://postgres:12345@localhost:5432/sales_db")

# Load the raw ecommerce sales dataset.
df = pd.read_csv(SOURCE_FILE)
print(f"Raw dataset loaded: {df.shape[0]} rows and {df.shape[1]} columns")

# Standardize column names to database-friendly snake_case.
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
    .str.replace(r"[^a-z0-9_]", "", regex=True)
)

# Remove exact duplicate records.
duplicate_count = df.duplicated().sum()
df = df.drop_duplicates().reset_index(drop=True)
print(f"Duplicate rows removed: {duplicate_count}")

# Trim text fields and standardize repeated spaces.
text_columns = [
    "order_id",
    "product",
    "category",
    "city",
]
for column in text_columns:
    df[column] = df[column].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)

# Convert numeric columns to the correct data types..
numeric_columns = [
    "quantity",
    "price",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column],errors="coerce"
    )
        
# Convert date column to datetime.
df["date"] = pd.to_datetime(df["date"],errors="coerce"
)

# Check missing values after type conversion.
required_columns = (numeric_columns + text_columns + ["date"]
)

missing_after_conversion = (df[required_columns].isna().sum()
)

print("Missing values after type conversion:")
print(missing_after_conversion[missing_after_conversion > 0
    ]
)

# Drop rows with missing values in required columns.
df = (
    df.dropna(subset=required_columns)
    .reset_index(drop=True)
)


# Keep only realistic values for student wellbeing and usage metrics.
valid_rows = (
    df["quantity"].between(1, 100)
    & df["price"].between(1, 1000000)
)
invalid_count = (~valid_rows).sum()
df = df.loc[valid_rows].reset_index(drop=True)
print(f"Invalid range rows removed: {invalid_count}")

# Convert integer-like metrics to nullable integer database types.
df["quantity"] = df["quantity"].astype("Int64")
df["price"] = df["price"].astype("float64")

# Define required columns.
required_columns = [
    "order_id",
    "product",
    "category",
    "quantity",
    "price",
    "date",
    "city",
]

#check missing values.
missing_values = df[required_columns].isna().sum()

print("Missing values:")
print(missing_values)

# Drop rows with missing values in required columns.
df = df.dropna(
    subset=required_columns
).reset_index(drop=True)

# check for exact duplicate rows.
duplicate_count = df.duplicated().sum()

print(f"Exact duplicate rows found: {duplicate_count}")

# Remove exact duplicate rows.
df = df.drop_duplicates().reset_index(drop=True)

# check for duplicate order IDs.
duplicate_order_ids = df["order_id"].duplicated().sum()

print(f"Duplicate order IDs found: {duplicate_order_ids}")

# Remove duplicate order IDs and keep the first record.
df = df.drop_duplicates(
    subset=["order_id"],
    keep="first"
).reset_index(drop=True)

# Validate quantity and price business rules.
valid_rows = (
    (df["quantity"] > 0) & (df["price"] > 0)
)

invalid_count = (~valid_rows).sum()

# Remove invalid records.
df = df.loc[valid_rows].reset_index(drop=True)

print(f"Invalid business rule rows removed: {invalid_count}")

# Define valid product categories.
valid_categories = [
    "Accessories",
    "Books",
    "Electronics",
    "Fashion",
    "Home Appliances",
]

# Identify rows with invalid categories.
invalid_category_rows = ~df["category"].isin(valid_categories)

invalid_category_count = invalid_category_rows.sum()

print(f"Invalid category rows found: {invalid_category_count}")

# Keep only valid categories.
df = df.loc[~invalid_category_rows].reset_index(drop=True)

# Calculate total sales for each order.
df["total_sales"] = (df["quantity"] * df["price"]
).round(2)

# Validate calculated total sales.
invalid_total_sales = (df["total_sales"] <= 0).sum()

print(f"Invalid total sales rows found:"f"{invalid_total_sales}"
)

# Validate order ID format.
valid_order_id_pattern = r"^ORD\d{4}$"

invalid_order_ids = ~df["order_id"].str.match(valid_order_id_pattern,na=False
)

invalid_order_id_count = invalid_order_ids.sum()

print(
    f"Invalid order IDs found: "
    f"{invalid_order_id_count}"
)

# Keep only valid order IDs.
df = df.loc[~invalid_order_ids].reset_index(drop=True)

# Validate order dates.
invalid_dates = df["date"].isna()

invalid_date_count = invalid_dates.sum()

print(
    f"Invalid dates found: "
    f"{invalid_date_count}"
)

# Remove rows with invalid dates.
df = df.loc[~invalid_dates].reset_index(drop=True)

# Create useful date fields.
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["month_name"] = df["date"].dt.month_name()


#  analytical columns.

# 1. Week number of the year.
df["week_of_year"] = df["date"].dt.isocalendar().week.astype("Int64")


# 2. Day of the month.
df["day_of_month"] = df["date"].dt.day


# 3. Price band.
df["price_band"] = pd.cut(
    df["price"],
    bins=[0, 1000, 5000, 20000, float("inf")],
    labels=[
        "Low Price",
        "Medium Price",
        "High Price",
        "Premium Price"
    ]
)


# 4. Total sales band.
df["total_sales_band"] = pd.cut(
    df["total_sales"],
    bins=[0, 2000, 10000, 50000, float("inf")],
    labels=[
        "Low Sales",
        "Medium Sales",
        "High Sales",
        "Very High Sales"
    ]
)


# 5. City order count.
df["city_order_count"] = df.groupby("city")["order_id"].transform("count")

# Final data quality checks.
print("\nFinal Data Quality Report")
print("-" * 30)

print(f"Total rows: {len(df)}")
print(f"Duplicate rows: {df.duplicated().sum()}")
print(f"Missing values: {df.isna().sum().sum()}")
print(f"Duplicate order IDs: {df['order_id'].duplicated().sum()}")

print("\nFinal data types:")
print(df.dtypes)

print("\nCleaned dataset preview:")
print(df.head())

# Load the cleaned and transformed dataframe into PostgreSQL.
engine = create_engine(
    "postgresql://postgres:12345@localhost:5432/sales_db"
)
df.to_sql(
    TABLE_NAME,
    engine,
    if_exists="replace",
    index=False,
    chunksize=1000,
    method="multi",
    dtype={
        "date": Date()
    }
)

print(f"Data has been successfully loaded into PostgreSQL table: {TABLE_NAME}")