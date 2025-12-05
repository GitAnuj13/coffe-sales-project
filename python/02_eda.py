"""
Maven Roasters - Exploratory Data Analysis
Understanding the data and finding initial patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pyodbc
from datetime import datetime

# Set style for better-looking charts
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# ============= CONFIGURATION =============
SERVER = "ANUJ_LAPTOP"
DATABASE = "COFFEE_SALES"
OUTPUT_DIR = "C:/coffe sales project/outputs/figure/"

# ============= CONNECT TO DATABASE =============
print("Connecting to database...")
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
)

# ============= LOAD DATA =============
print("\nLoading data from SQL Server...")

# Load all data with joins
query = """
SELECT 
    t.transaction_id,
    t.transaction_date,
    t.transaction_time,
    t.transaction_qty,
    s.store_id,
    s.store_location,
    p.product_id,
    p.product_category,
    p.product_type,
    p.product_detail,
    p.unit_price,
    (t.transaction_qty * p.unit_price) AS total_amount
FROM transactions t
JOIN stores s ON t.store_id = s.store_id
JOIN products p ON t.product_id = p.product_id
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"✓ Loaded {len(df):,} records")

# ============= BASIC DATA OVERVIEW =============
print("\n" + "="*60)
print("BASIC DATA OVERVIEW")
print("="*60)

print(f"\nDataset Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"\nDate Range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
print(f"Number of Days: {(df['transaction_date'].max() - df['transaction_date'].min()).days} days")

print("\nColumn Names and Types:")
print(df.dtypes)

print("\nFirst Few Records:")
print(df.head())

# ============= DATA QUALITY CHECK =============
print("\n" + "="*60)
print("DATA QUALITY CHECK")
print("="*60)

print("\nMissing Values:")
missing = df.isnull().sum()
if missing.sum() == 0:
    print("✓ No missing values found")
else:
    print(missing[missing > 0])

print("\nDuplicate Transactions:")
duplicates = df['transaction_id'].duplicated().sum()
print(f"Duplicates: {duplicates}")

print("\nNegative Values Check:")
print(f"Negative quantities: {(df['transaction_qty'] < 0).sum()}")
print(f"Negative prices: {(df['unit_price'] < 0).sum()}")
print(f"Negative amounts: {(df['total_amount'] < 0).sum()}")

# ============= SUMMARY STATISTICS =============
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print("\nNumeric Columns Summary:")
print(df[['transaction_qty', 'unit_price', 'total_amount']].describe())

print(f"\nTotal Revenue: ${df['total_amount'].sum():,.2f}")
print(f"Average Transaction Value: ${df['total_amount'].mean():.2f}")
print(f"Median Transaction Value: ${df['total_amount'].median():.2f}")

# ============= STORE ANALYSIS =============
print("\n" + "="*60)
print("STORE PERFORMANCE")
print("="*60)

store_stats = df.groupby('store_location').agg({
    'transaction_id': 'count',
    'total_amount': ['sum', 'mean']
}).round(2)

store_stats.columns = ['Transactions', 'Total_Revenue', 'Avg_Transaction']
store_stats = store_stats.sort_values('Total_Revenue', ascending=False)

print("\nStore Performance:")
print(store_stats)

# Visualization: Revenue by Store
plt.figure(figsize=(10, 6))
store_revenue = df.groupby('store_location')['total_amount'].sum().sort_values(ascending=False)
plt.bar(store_revenue.index, store_revenue.values, color=['#2E86AB', '#A23B72', '#F18F01'])
plt.title('Total Revenue by Store Location', fontsize=16, fontweight='bold')
plt.xlabel('Store Location', fontsize=12)
plt.ylabel('Total Revenue ($)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'revenue_by_store.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: revenue_by_store.png")
plt.close()

# ============= PRODUCT ANALYSIS =============
print("\n" + "="*60)
print("PRODUCT PERFORMANCE")
print("="*60)

# Top categories
category_stats = df.groupby('product_category').agg({
    'transaction_id': 'count',
    'total_amount': 'sum'
}).round(2)
category_stats.columns = ['Transactions', 'Revenue']
category_stats = category_stats.sort_values('Revenue', ascending=False)

print("\nRevenue by Product Category:")
print(category_stats)

# Visualization: Revenue by Category
plt.figure(figsize=(10, 6))
plt.bar(category_stats.index, category_stats['Revenue'], color='#2E86AB')
plt.title('Revenue by Product Category', fontsize=16, fontweight='bold')
plt.xlabel('Product Category', fontsize=12)
plt.ylabel('Total Revenue ($)', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'revenue_by_category.png', dpi=300, bbox_inches='tight')
print("✓ Saved: revenue_by_category.png")
plt.close()

# Top 10 products
top_products = df.groupby('product_detail')['total_amount'].sum().sort_values(ascending=False).head(10)
print("\nTop 10 Products by Revenue:")
print(top_products)

# ============= TIME ANALYSIS =============
print("\n" + "="*60)
print("TIME PATTERNS")
print("="*60)

# Add time features
df['date'] = pd.to_datetime(df['transaction_date'])
df['hour'] = pd.to_datetime(df['transaction_time'], format='%H:%M:%S').dt.hour
df['day_of_week'] = df['date'].dt.day_name()
df['month'] = df['date'].dt.month_name()

# Daily revenue
daily_revenue = df.groupby('date')['total_amount'].sum()
print(f"\nAverage Daily Revenue: ${daily_revenue.mean():,.2f}")
print(f"Best Day: {daily_revenue.idxmax()} (${daily_revenue.max():,.2f})")
print(f"Worst Day: {daily_revenue.idxmin()} (${daily_revenue.min():,.2f})")

# Visualization: Revenue over time
plt.figure(figsize=(14, 6))
plt.plot(daily_revenue.index, daily_revenue.values, color='#2E86AB', linewidth=2)
plt.title('Daily Revenue Trend', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Revenue ($)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'daily_revenue_trend.png', dpi=300, bbox_inches='tight')
print("✓ Saved: daily_revenue_trend.png")
plt.close()

# Hourly patterns
hourly_sales = df.groupby('hour')['transaction_id'].count()
print("\nTransactions by Hour:")
print(hourly_sales)

# Visualization: Hourly pattern
plt.figure(figsize=(12, 6))
plt.bar(hourly_sales.index, hourly_sales.values, color='#A23B72')
plt.title('Transactions by Hour of Day', fontsize=16, fontweight='bold')
plt.xlabel('Hour', fontsize=12)
plt.ylabel('Number of Transactions', fontsize=12)
plt.xticks(range(0, 24))
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'hourly_pattern.png', dpi=300, bbox_inches='tight')
print("✓ Saved: hourly_pattern.png")
plt.close()

# Day of week
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_revenue = df.groupby('day_of_week')['total_amount'].sum().reindex(day_order)
print("\nRevenue by Day of Week:")
print(day_revenue)

# ============= PRICE ANALYSIS =============
print("\n" + "="*60)
print("PRICE DISTRIBUTION")
print("="*60)

print("\nPrice Statistics:")
print(df['unit_price'].describe())

# Visualization: Price distribution
plt.figure(figsize=(10, 6))
plt.hist(df['unit_price'], bins=30, color='#F18F01', edgecolor='black', alpha=0.7)
plt.title('Distribution of Product Prices', fontsize=16, fontweight='bold')
plt.xlabel('Unit Price ($)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'price_distribution.png', dpi=300, bbox_inches='tight')
print("✓ Saved: price_distribution.png")
plt.close()

# ============= KEY INSIGHTS =============
print("\n" + "="*60)
print("KEY INSIGHTS DISCOVERED")
print("="*60)

print(f"""
1. REVENUE: Total revenue is ${df['total_amount'].sum():,.2f}

2. BEST PERFORMING STORE: {store_stats.index[0]} 
   - Revenue: ${store_stats.iloc[0]['Total_Revenue']:,.2f}

3. TOP CATEGORY: {category_stats.index[0]}
   - Revenue: ${category_stats.iloc[0]['Revenue']:,.2f}

4. PEAK HOUR: {hourly_sales.idxmax()}:00 
   - Transactions: {hourly_sales.max()}

5. AVERAGE TRANSACTION: ${df['total_amount'].mean():.2f}

6. BUSIEST DAY: {day_revenue.idxmax()}
   - Revenue: ${day_revenue.max():,.2f}
""")

print("\n" + "="*60)
print("EDA COMPLETE!")
print("="*60)
print(f"\nAll visualizations saved to: {OUTPUT_DIR}")
print("\nNext Steps:")
print("1. Review the charts in the outputs/figures folder")
print("2. Note any surprising patterns")
print("3. Prepare questions for deeper analysis")