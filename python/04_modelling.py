"""
Maven Roasters - Predictive Modeling & Time Series Forecasting
Building models to predict future revenue and trends
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pyodbc
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)

# ============= CONFIGURATION =============
SERVER = "ANUJ_LAPTOP"
DATABASE = "COFFEE_SALES"
OUTPUT_DIR = "C:/coffe sales project/outputs/figure/"
REPORTS_DIR = "C:/coffe sales project/outputs/reports/"

print("="*70)
print("MAVEN ROASTERS - PREDICTIVE MODELING & FORECASTING")
print("="*70)

# ============= LOAD DATA =============
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
    p.unit_price,
    (t.transaction_qty * p.unit_price) AS total_amount,
    DATEPART(HOUR, CAST(t.transaction_time AS TIME)) AS hour,
    DATEPART(WEEKDAY, t.transaction_date) AS day_of_week_num,
    DATENAME(WEEKDAY, t.transaction_date) AS day_name
FROM transactions t
JOIN stores s ON t.store_id = s.store_id
JOIN products p ON t.product_id = p.product_id
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"✓ Loaded {len(df):,} transactions\n")

# Convert date column
df['date'] = pd.to_datetime(df['transaction_date'])

# ============= PART 1: DAILY REVENUE AGGREGATION =============
print("="*70)
print("PART 1: PREPARING TIME SERIES DATA")
print("="*70)

# Aggregate to daily level
daily_data = df.groupby('date').agg({
    'transaction_id': 'count',
    'total_amount': 'sum',
    'transaction_qty': 'sum'
}).reset_index()

daily_data.columns = ['date', 'num_transactions', 'revenue', 'items_sold']

print(f"\nDaily data prepared: {len(daily_data)} days")
print(f"Date range: {daily_data['date'].min()} to {daily_data['date'].max()}")
print(f"\nDaily Revenue Statistics:")
print(daily_data['revenue'].describe().round(2))

# ============= PART 2: TREND ANALYSIS =============
print("\n" + "="*70)
print("PART 2: TREND ANALYSIS")
print("="*70)

# Add time-based features
daily_data['day_number'] = (daily_data['date'] - daily_data['date'].min()).dt.days
daily_data['day_of_week'] = daily_data['date'].dt.dayofweek
daily_data['week_number'] = daily_data['date'].dt.isocalendar().week
daily_data['month'] = daily_data['date'].dt.month

# Fit linear trend
X_trend = daily_data['day_number'].values.reshape(-1, 1)
y_trend = daily_data['revenue'].values

trend_model = LinearRegression()
trend_model.fit(X_trend, y_trend)
daily_data['trend'] = trend_model.predict(X_trend)

# Calculate trend
daily_change = trend_model.coef_[0]
pct_change = (daily_change / daily_data['revenue'].mean()) * 100

print(f"\n--- Revenue Trend ---")
print(f"Daily change: ${daily_change:.2f} per day")
print(f"Percentage change: {pct_change:.3f}% per day")
print(f"Monthly impact: ${daily_change * 30:.2f} per month")
print(f"6-month projection: ${daily_change * 180:.2f} over 6 months")

if daily_change > 0:
    print(f"\n✓ Revenue is GROWING at ${daily_change:.2f} per day")
else:
    print(f"\n⚠ Revenue is DECLINING at ${abs(daily_change):.2f} per day")

# Visualization: Revenue with trend line
plt.figure(figsize=(14, 6))
plt.scatter(daily_data['date'], daily_data['revenue'], alpha=0.5, s=30, label='Actual Revenue')
plt.plot(daily_data['date'], daily_data['trend'], color='red', linewidth=2, label=f'Trend Line (${daily_change:.2f}/day)')
plt.title('Daily Revenue with Trend Analysis', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Revenue ($)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'revenue_trend_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: revenue_trend_analysis.png")
plt.close()

# ============= PART 3: MOVING AVERAGES =============
print("\n" + "="*70)
print("PART 3: MOVING AVERAGES (SMOOTHING)")
print("="*70)

# Calculate moving averages
daily_data['MA_7'] = daily_data['revenue'].rolling(window=7, center=True).mean()
daily_data['MA_14'] = daily_data['revenue'].rolling(window=14, center=True).mean()

print("\n7-day moving average smooths daily volatility")
print("14-day moving average shows broader trends")

# Visualization: Moving averages
plt.figure(figsize=(14, 6))
plt.plot(daily_data['date'], daily_data['revenue'], alpha=0.3, label='Daily Revenue', linewidth=1)
plt.plot(daily_data['date'], daily_data['MA_7'], linewidth=2, label='7-Day Moving Avg')
plt.plot(daily_data['date'], daily_data['MA_14'], linewidth=2, label='14-Day Moving Avg')
plt.title('Revenue with Moving Averages', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Revenue ($)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'moving_averages.png', dpi=300, bbox_inches='tight')
print("✓ Saved: moving_averages.png")
plt.close()

# ============= PART 4: SIMPLE FORECASTING =============
print("\n" + "="*70)
print("PART 4: REVENUE FORECASTING")
print("="*70)

# Prepare features for prediction
daily_data['is_weekend'] = daily_data['day_of_week'].isin([5, 6]).astype(int)

# Features that might predict revenue
features = ['day_number', 'day_of_week', 'is_weekend', 'week_number']
X = daily_data[features].copy()
y = daily_data['revenue'].copy()

# Train-test split (80% train, 20% test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=False
)

print(f"\nTraining set: {len(X_train)} days")
print(f"Testing set: {len(X_test)} days")

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

# Evaluate model
train_mae = mean_absolute_error(y_train, y_pred_train)
test_mae = mean_absolute_error(y_test, y_pred_test)
train_r2 = r2_score(y_train, y_pred_train)
test_r2 = r2_score(y_test, y_pred_test)

print("\n--- Model Performance ---")
print(f"Training MAE: ${train_mae:.2f}")
print(f"Testing MAE: ${test_mae:.2f}")
print(f"Training R²: {train_r2:.3f}")
print(f"Testing R²: {test_r2:.3f}")

print(f"\nInterpretation:")
print(f"- On average, predictions are off by ${test_mae:.2f}")
print(f"- Model explains {test_r2*100:.1f}% of revenue variation")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': features,
    'coefficient': model.coef_
}).sort_values('coefficient', key=abs, ascending=False)

print("\n--- Feature Importance ---")
print(feature_importance.to_string(index=False))

# Visualization: Actual vs Predicted
plt.figure(figsize=(14, 6))
test_dates = daily_data.loc[X_test.index, 'date']
plt.plot(test_dates, y_test.values, label='Actual Revenue', linewidth=2, alpha=0.7)
plt.plot(test_dates, y_pred_test, label='Predicted Revenue', linewidth=2, linestyle='--', alpha=0.7)
plt.title('Revenue Forecast vs Actual (Test Set)', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Revenue ($)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_DIR + 'forecast_vs_actual.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: forecast_vs_actual.png")
plt.close()

# ============= PART 5: FUTURE PREDICTIONS =============
print("\n" + "="*70)
print("PART 5: FUTURE REVENUE PREDICTIONS")
print("="*70)

# Predict next 7 days
last_day = daily_data['day_number'].max()
last_date = daily_data['date'].max()

future_predictions = []

for i in range(1, 8):
    future_day = last_day + i
    future_date = last_date + timedelta(days=i)
    day_of_week = future_date.dayofweek
    is_weekend = 1 if day_of_week in [5, 6] else 0
    week_num = future_date.isocalendar()[1]
    
    X_future = pd.DataFrame({
        'day_number': [future_day],
        'day_of_week': [day_of_week],
        'is_weekend': [is_weekend],
        'week_number': [week_num]
    })
    
    pred_revenue = model.predict(X_future)[0]
    
    future_predictions.append({
        'date': future_date,
        'day_name': future_date.strftime('%A'),
        'predicted_revenue': pred_revenue
    })

future_df = pd.DataFrame(future_predictions)

print("\n--- Next 7 Days Revenue Forecast ---")
for _, row in future_df.iterrows():
    print(f"{row['date'].strftime('%Y-%m-%d')} ({row['day_name']}): ${row['predicted_revenue']:,.2f}")

print(f"\nTotal forecasted revenue (next 7 days): ${future_df['predicted_revenue'].sum():,.2f}")
print(f"Average daily forecast: ${future_df['predicted_revenue'].mean():,.2f}")

# ============= PART 6: STORE-LEVEL FORECASTING =============
print("\n" + "="*70)
print("PART 6: STORE-LEVEL REVENUE PREDICTIONS")
print("="*70)

# Aggregate by store and date
store_daily = df.groupby(['store_location', 'date'])['total_amount'].sum().reset_index()
store_daily.columns = ['store', 'date', 'revenue']

print("\n--- Average Daily Revenue by Store ---")
store_avg = store_daily.groupby('store')['revenue'].mean().sort_values(ascending=False)
for store, avg_rev in store_avg.items():
    print(f"{store}: ${avg_rev:,.2f}/day")

# Based on historical average, predict next week per store
print("\n--- Next Week Forecast by Store ---")
for store, avg_rev in store_avg.items():
    weekly_forecast = avg_rev * 7
    print(f"{store}: ${weekly_forecast:,.2f} (7 days)")

# ============= SUMMARY REPORT =============
print("\n" + "="*70)
print("PREDICTIVE MODELING SUMMARY")
print("="*70)

summary_text = f"""
REVENUE TREND ANALYSIS:
- Daily trend: ${daily_change:.2f} per day ({pct_change:.3f}% per day)
- Monthly impact: ${daily_change * 30:,.2f}
- Trend direction: {'GROWING ↑' if daily_change > 0 else 'DECLINING ↓'}

FORECAST MODEL PERFORMANCE:
- Prediction accuracy (MAE): ${test_mae:.2f}
- Model strength (R²): {test_r2:.3f}
- This means predictions are typically within ${test_mae:.2f} of actual

NEXT 7 DAYS FORECAST:
- Total predicted revenue: ${future_df['predicted_revenue'].sum():,.2f}
- Daily average: ${future_df['predicted_revenue'].mean():,.2f}
- Range: ${future_df['predicted_revenue'].min():,.2f} to ${future_df['predicted_revenue'].max():,.2f}

BUSINESS IMPLICATIONS:
1. Revenue trend is {'positive - business is growing' if daily_change > 0 else 'negative - need intervention'}
2. Predictions can help with staffing and inventory planning
3. Model accuracy of ${test_mae:.2f} allows for reliable short-term forecasting

RECOMMENDATIONS:
- Use daily forecasts for staffing decisions
- Monitor actual vs predicted to catch anomalies early
- Update model monthly as new data comes in
"""

print(summary_text)

# Save report
with open(REPORTS_DIR + 'predictive_modeling_report.txt', 'w', encoding='utf-8') as f:
    f.write("MAVEN ROASTERS - PREDICTIVE MODELING REPORT\n")
    f.write("="*70 + "\n\n")
    f.write(summary_text)

print(f"\n✓ Report saved to: {REPORTS_DIR}predictive_modeling_report.txt")
print("\n✓ Predictive modeling complete!")
print(f"All visualizations saved to: {OUTPUT_DIR}")