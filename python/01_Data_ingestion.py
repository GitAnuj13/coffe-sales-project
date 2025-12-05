"""
Maven Roasters - Data Ingestion Script
Loads Excel data into SQL Server database
"""

import pandas as pd
import pyodbc
from sqlalchemy import create_engine
import urllib
from pathlib import Path

# ============= CONFIGURATION =============
from pathlib import Path
# STEP 1: Get project root (etl folder)
BASE = Path(__file__).resolve().parents[1]
# STEP 2: Build folder paths
DATA = BASE / "data" / "raw"
# STEP 3: Build file path to Excel file
EXCEL_FILE = DATA / "Coffee Shop Sales.xlsx"
print("Project Root:", BASE)
print("Data Folder:", DATA)
print("Excel File Path:", EXCEL_FILE)

# SQL Server connection parameters
SERVER = "ANUJ_LAPTOP"  # Change if your SQL Server is different
DATABASE = "COFFEE_SALES"  # Change if your database name is different

# ============= CONNECT TO SQL SERVER =============
def get_connection():
    """Create SQLAlchemy engine for SQL Server"""
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )
    params = urllib.parse.quote_plus(conn_str)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
    return engine

# ============= LOAD DATA =============
print("Step 1: Reading Excel file...")
df = pd.read_excel(EXCEL_FILE)
print(f"✓ Loaded {len(df):,} transactions")

# ============= DATA VALIDATION =============
print("\nStep 2: Validating data...")
print(f"Columns: {list(df.columns)}")
print(f"Date range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
print(f"Unique stores: {df['store_location'].nunique()}")
print(f"Unique products: {df['product_id'].nunique()}")

# Check for missing values
missing = df.isnull().sum()
if missing.any():
    print("\n⚠ Warning: Missing values found:")
    print(missing[missing > 0])
else:
    print("✓ No missing values")

# ============= PREPARE DIMENSION TABLES =============
print("\nStep 3: Preparing dimension tables...")

# Stores table
stores = df[['store_id', 'store_location']].drop_duplicates()
print(f"✓ Prepared {len(stores)} stores")

# Products table
products = (
    df.groupby("product_id")
      .agg({
          "product_category": "first",
          "product_type": "first",
          "product_detail": "first",
          "unit_price": "mean"
      })
      .reset_index()
)

print(f"✓ Prepared {len(products)} products")

# Transactions table
transactions = df[['transaction_id', 'transaction_date', 'transaction_time',
                   'transaction_qty', 'store_id', 'product_id']]
print(f"✓ Prepared {len(transactions):,} transactions")

# ============= LOAD TO SQL SERVER =============
print("\nStep 4: Loading data to SQL Server...")

try:
    engine = get_connection()
    stores = stores.drop_duplicates()
    # Load stores
    stores.to_sql(
    'stores',
    engine,
    if_exists='replace',   # deletes entire table → inserts fresh
    index=False
)

    print("✓ Loaded stores table")
    products = products.drop_duplicates()
    # Load products
    products.to_sql('products', engine, if_exists='replace', index=False)
    print("✓ Loaded products table")
    
    # Load transactions
    transactions = transactions.drop_duplicates()
    transactions.to_sql('transactions', engine, if_exists='replace', index=False)
    print(f"✓ Loaded {len(transactions):,} transactions")
    
    print("\n" + "="*50)
    print("SUCCESS! All data loaded to SQL Server")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTroubleshooting:")
    print("1. Check SQL Server is running")
    print("2. Verify database 'MavenRoasters' exists")
    print("3. Confirm tables are created")
    print("4. Check ODBC Driver 17 is installed")

# ============= VERIFICATION =============
print("\nStep 5: Verifying data...")
try:
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )
    cursor = conn.cursor()
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM stores")
    store_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    transaction_count = cursor.fetchone()[0]
    
    print(f"\nDatabase record counts:")
    print(f"  Stores: {store_count}")
    print(f"  Products: {product_count}")
    print(f"  Transactions: {transaction_count:,}")
    
    conn.close()
    
except Exception as e:
    print(f"Could not verify: {e}")

print("\n✓ Data ingestion complete!")