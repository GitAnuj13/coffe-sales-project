"""
Maven Roasters - Statistical Analysis
Testing hypotheses and finding significant patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pyodbc
from scipy import stats
from scipy.stats import chi2_contingency, ttest_ind, f_oneway, pearsonr

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# ============= CONFIGURATION =============
SERVER = "ANUJ_LAPTOP"
DATABASE = "COFFEE_SALES"
OUTPUT_DIR = "C:/coffe sales project/outputs/figure/"

print("="*70)
print("MAVEN ROASTERS - STATISTICAL ANALYSIS")
print("="*70)

# ============= CONNECT & LOAD DATA =============
print("\nLoading data from SQL Server...")

conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
)

query = """
SELECT 
    t.transaction_id,
    t.transaction_date,
    t.transaction_time,
    t.transaction_qty,
    s.store_location,
    p.product_category,
    p.product_type,
    p.unit_price,
    (t.transaction_qty * p.unit_price) AS total_amount,
    DATEPART(HOUR, CAST(t.transaction_time AS TIME)) AS hour,
    DATENAME(WEEKDAY, t.transaction_date) AS day_of_week
FROM transactions t
JOIN stores s ON t.store_id = s.store_id
JOIN products p ON t.product_id = p.product_id
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"✓ Loaded {len(df):,} transactions\n")

# ============= PART 1: DESCRIPTIVE STATISTICS =============
print("="*70)
print("PART 1: DESCRIPTIVE STATISTICS")
print("="*70)

print("\n--- Overall Transaction Statistics ---")
print(f"Mean transaction value: ${df['total_amount'].mean():.2f}")
print(f"Median transaction value: ${df['total_amount'].median():.2f}")
print(f"Std deviation: ${df['total_amount'].std():.2f}")
print(f"Min: ${df['total_amount'].min():.2f}")
print(f"Max: ${df['total_amount'].max():.2f}")

print("\n--- Transaction Value by Store ---")
store_stats = df.groupby('store_location')['total_amount'].agg([
    ('count', 'count'),
    ('mean', 'mean'),
    ('median', 'median'),
    ('std', 'std'),
    ('min', 'min'),
    ('max', 'max')
]).round(2)
print(store_stats)

# Visualization: Distribution by store
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
stores = df['store_location'].unique()

for idx, store in enumerate(stores):
    store_data = df[df['store_location'] == store]['total_amount']
    axes[idx].hist(store_data, bins=30, color='#2E86AB', edgecolor='black', alpha=0.7)
    axes[idx].set_title(f'{store}\nMean: ${store_data.mean():.2f}', fontweight='bold')
    axes[idx].set_xlabel('Transaction Amount ($)')
    axes[idx].set_ylabel('Frequency')
    axes[idx].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'transaction_distribution_by_store.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: transaction_distribution_by_store.png")
plt.close()

# ============= PART 2: HYPOTHESIS TESTING =============
print("\n" + "="*70)
print("PART 2: HYPOTHESIS TESTING")
print("="*70)

# TEST 1: Are store revenues significantly different?
print("\n--- Test 1: Store Revenue Comparison (ANOVA) ---")
print("H0 (Null Hypothesis): All stores have the same average transaction value")
print("Ha (Alternative): At least one store has different average transaction value")

store_groups = [df[df['store_location'] == store]['total_amount'].values 
                for store in df['store_location'].unique()]

f_stat, p_value = f_oneway(*store_groups)

print(f"\nF-statistic: {f_stat:.4f}")
print(f"P-value: {p_value:.6f}")

if p_value < 0.05:
    print("✓ RESULT: SIGNIFICANT difference between stores (p < 0.05)")
    print("  Interpretation: The revenue differences are statistically significant,")
    print("  not due to random chance.")
else:
    print("✗ RESULT: NO significant difference (p >= 0.05)")
    print("  Interpretation: Revenue differences could be due to random variation.")

# TEST 2: Pairwise comparison - Hell's Kitchen vs others
print("\n--- Test 2: Hell's Kitchen vs Other Stores (T-tests) ---")

stores_list = df['store_location'].unique()
hk_data = df[df['store_location'] == 'Hell\'s Kitchen']['total_amount']

for store in stores_list:
    if store != "Hell's Kitchen":
        other_data = df[df['store_location'] == store]['total_amount']
        t_stat, p_val = ttest_ind(hk_data, other_data)
        
        print(f"\nHell's Kitchen vs {store}:")
        print(f"  T-statistic: {t_stat:.4f}")
        print(f"  P-value: {p_val:.6f}")
        
        if p_val < 0.05:
            if hk_data.mean() > other_data.mean():
                print(f"  ✓ Hell's Kitchen significantly HIGHER (p < 0.05)")
            else:
                print(f"  ✓ Hell's Kitchen significantly LOWER (p < 0.05)")
        else:
            print(f"  ✗ No significant difference (p >= 0.05)")

# TEST 3: Product category performance
print("\n--- Test 3: Product Category Revenue (Chi-Square Test) ---")
print("Testing if product category sales distribution differs by store")

category_store_crosstab = pd.crosstab(df['store_location'], df['product_category'])
chi2, p_val, dof, expected = chi2_contingency(category_store_crosstab)

print(f"\nChi-square statistic: {chi2:.4f}")
print(f"P-value: {p_val:.6f}")
print(f"Degrees of freedom: {dof}")

if p_val < 0.05:
    print("✓ RESULT: Product category preferences DIFFER by store (p < 0.05)")
else:
    print("✗ RESULT: Product categories similar across stores (p >= 0.05)")

# ============= PART 3: CORRELATION ANALYSIS =============
print("\n" + "="*70)
print("PART 3: CORRELATION ANALYSIS")
print("="*70)

# Create numeric features for correlation
df['month'] = pd.to_datetime(df['transaction_date']).dt.month
df['day'] = pd.to_datetime(df['transaction_date']).dt.day

# Correlations
numeric_df = df[['transaction_qty', 'unit_price', 'total_amount', 'hour', 'month', 'day']]
correlation_matrix = numeric_df.corr()

print("\n--- Correlation Matrix ---")
print(correlation_matrix.round(3))

# Key correlations
print("\n--- Key Findings ---")
print(f"Transaction Qty vs Total Amount: {correlation_matrix.loc['transaction_qty', 'total_amount']:.3f}")
print(f"Unit Price vs Total Amount: {correlation_matrix.loc['unit_price', 'total_amount']:.3f}")
print(f"Hour of Day vs Total Amount: {correlation_matrix.loc['hour', 'total_amount']:.3f}")

# Visualization: Correlation heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, linewidths=1, fmt='.2f')
plt.title('Correlation Matrix - Transaction Variables', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'correlation_matrix.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: correlation_matrix.png")
plt.close()

# ============= PART 4: HOURLY PATTERN ANALYSIS =============
print("\n" + "="*70)
print("PART 4: HOURLY PATTERN SIGNIFICANCE")
print("="*70)

print("\n--- Testing if hourly patterns differ by store ---")

hourly_by_store = df.groupby(['store_location', 'hour'])['transaction_id'].count().reset_index()
hourly_pivot = hourly_by_store.pivot(index='hour', columns='store_location', values='transaction_id')

# Statistical test across hours
print("\nPeak hours (7-11 AM) vs Off-peak hours comparison:")

for store in df['store_location'].unique():
    store_df = df[df['store_location'] == store]
    peak_hours = store_df[store_df['hour'].between(7, 11)]['total_amount']
    offpeak_hours = store_df[~store_df['hour'].between(7, 11)]['total_amount']
    
    t_stat, p_val = ttest_ind(peak_hours, offpeak_hours)
    
    print(f"\n{store}:")
    print(f"  Peak hour avg: ${peak_hours.mean():.2f}")
    print(f"  Off-peak avg: ${offpeak_hours.mean():.2f}")
    print(f"  Difference: ${peak_hours.mean() - offpeak_hours.mean():.2f}")
    print(f"  P-value: {p_val:.6f}")
    
    if p_val < 0.05:
        print(f"  ✓ SIGNIFICANT difference between peak/off-peak (p < 0.05)")
    else:
        print(f"  ✗ No significant difference")

# ============= PART 5: DAY OF WEEK ANALYSIS =============
print("\n" + "="*70)
print("PART 5: DAY OF WEEK PATTERNS")
print("="*70)

day_revenue = df.groupby('day_of_week')['total_amount'].agg(['sum', 'mean', 'count'])
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_revenue = day_revenue.reindex(day_order)

print("\n--- Average Revenue by Day ---")
print(day_revenue.round(2))

# Test if weekday vs weekend differs
df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday'])
weekday_amounts = df[~df['is_weekend']]['total_amount']
weekend_amounts = df[df['is_weekend']]['total_amount']

t_stat, p_val = ttest_ind(weekday_amounts, weekend_amounts)

print(f"\n--- Weekday vs Weekend ---")
print(f"Weekday average: ${weekday_amounts.mean():.2f}")
print(f"Weekend average: ${weekend_amounts.mean():.2f}")
print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_val:.6f}")

if p_val < 0.05:
    if weekday_amounts.mean() > weekend_amounts.mean():
        print("✓ Weekdays significantly HIGHER than weekends (p < 0.05)")
    else:
        print("✓ Weekends significantly HIGHER than weekdays (p < 0.05)")
else:
    print("✗ No significant difference between weekdays and weekends")

# ============= SUMMARY OF FINDINGS =============
print("\n" + "="*70)
print("STATISTICAL ANALYSIS SUMMARY")
print("="*70)

print("""
KEY FINDINGS:

1. STORE PERFORMANCE:
   - Statistical tests show whether store differences are significant
   - Check p-values above (p < 0.05 = significant)

2. TIME PATTERNS:
   - Peak hours (7-11 AM) show significant difference from off-peak
   - Day of week patterns tested for significance

3. CORRELATIONS:
   - Strong correlations indicate predictable relationships
   - Useful for forecasting and optimization

4. PRODUCT CATEGORIES:
   - Chi-square test shows if preferences differ by location
   - Helps inform inventory decisions

NEXT STEPS:
- Use these insights for predictive modeling (Day 5)
- Focus interventions on statistically significant differences
- Ignore patterns that aren't statistically meaningful
""")

print("\n✓ Statistical analysis complete!")
print(f"All visualizations saved to: {OUTPUT_DIR}")