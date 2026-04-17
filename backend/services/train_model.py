#Aiming for forecasting demand per (product_id, warehouse_id)
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
import lightgbm as lgb
import joblib
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL
)


# 🔹 Fetch data from DB
def fetch_sales_data():
    query = """
    SELECT *
    FROM sales_history
    ORDER BY sale_date
    """
    df = pd.read_sql(query, engine)

    return df

print("fetching sales data...")
sales = fetch_sales_data()

print("cleaning the data...")
#sales history table cleaning
#Drop duplicate rows

sales.drop_duplicates(subset=['sale_id'])

#Removing invalid rows
sales = sales[ (sales['quantity_sold'] > 0) & (sales['revenue'] > 0) ]
#converting to datetime
sales['sale_date'] = pd.to_datetime(sales['sale_date'])
#Aggregate into daily demand
sales_daily = (
    sales
    .groupby(['product_id','warehouse_id','sale_date'])
    ['quantity_sold']
    .sum()
    .reset_index()
)

sales_daily= sales_daily.rename(
    columns = {'quantity_sold':'demand'}
)

#Aggregate into daily demand
sales_daily = (
    sales
    .groupby(['product_id','warehouse_id','sale_date'])
    ['quantity_sold']
    .sum()
    .reset_index()
)

sales_daily = sales_daily.rename(
    columns = {'quantity_sold':'demand'}
)


print("improvements for better signals")
#Improving demand density for better signals
# baseline = np.random.poisson(2, size=len(sales))
# noise = np.random.randint(0,3,len(sales))

# sales['demand'] = baseline + noise

# #Adding Seasonality
# dow = sales['sale_date'].dt.dayofweek

# sales.loc[dow >= 5, 'demand'] += np.random.randint(2,5)

sales = sales_daily
sales = sales.sort_values(
    ['product_id','warehouse_id','sale_date']
)

sales['lag_1'] = (
    sales.groupby(['product_id','warehouse_id'])['demand']
    .shift(1)
)

sales['lag_7'] = (
    sales.groupby(['product_id','warehouse_id'])['demand']
    .shift(7)
)

sales['rolling_mean_7'] = (
    sales.groupby(['product_id','warehouse_id'])['demand']
    .transform(lambda x: x.shift(1).rolling(7).mean())
)


sales['day_of_week'] = sales['sale_date'].dt.dayofweek
sales['month'] = sales['sale_date'].dt.month
sales['is_weekend'] = sales['day_of_week'].isin([5,6]).astype(int)

sales.dropna()

sales = sales.sort_values(
    ['product_id','warehouse_id','sale_date']
)

sales = sales.dropna().reset_index(drop=True)

FEATURES = [
    "lag_1",
    "lag_7",
    "rolling_mean_7",
    "day_of_week",
    "month",
    "is_weekend"
    ]

TARGET = 'demand'

split_date = sales['sale_date'].max() - pd.Timedelta(days=30)

train = sales[sales['sale_date'] <= split_date].copy()
test  = sales[sales['sale_date'] >  split_date].copy()


# model = lgb.LGBMRegressor(
#     n_estimators=500,
#     learning_rate=0.05,
#     num_leaves=31,
#     subsample=0.8,
#     colsample_bytree=0.8,
#     random_state=42,
#     n_jobs=-1
# )
model = lgb.LGBMRegressor(
    n_estimators=500,
    learning_rate=0.03,
    max_depth=7,
    num_leaves=50,
    random_state=42
)

model.fit(
    train[FEATURES],
    train[TARGET],
    eval_set=[(test[FEATURES], test[TARGET])],
    eval_metric='l1'
)

test['pred_demand_lgb'] = model.predict(test[FEATURES])

mae  = mean_absolute_error(test[TARGET], test['pred_demand_lgb'])
rmse = np.sqrt(mean_squared_error(test[TARGET], test['pred_demand_lgb']))

mape = np.mean(
    np.abs(
        (test[TARGET] - test['pred_demand_lgb']) /
        np.clip(test[TARGET],1,None)
    )
) * 100

print("LightGBM MAE :", mae)
print("LightGBM RMSE:", rmse)
print("LightGBM MAPE:", mape)


#Export model
joblib.dump(model, "forecaster_model.pkl")
print("model exported successfully")

future_days = 7
forecast_rows = []

last_data = sales.copy()

for step in range(1, future_days + 1):

    next_date = last_data['sale_date'].max() + pd.Timedelta(days=1)

    future_df = (
        last_data
        .sort_values(['product_id','warehouse_id','sale_date'])
        .groupby(['product_id','warehouse_id'])
        .tail(1)
        .copy()
    )

    future_df['sale_date'] = next_date

    future_df['lag_7'] = future_df['lag_1']
    future_df['lag_1'] = future_df['demand']

    future_df['rolling_mean_7'] = (
        future_df[['lag_1','lag_7']].mean(axis=1)
    )

    future_df['day_of_week'] = future_df['sale_date'].dt.dayofweek
    future_df['month'] = future_df['sale_date'].dt.month
    future_df['is_weekend'] = future_df['day_of_week'].isin([5,6]).astype(int)

    future_df['pred_demand'] = model.predict(
        future_df[FEATURES]
    )

    future_df['demand'] = future_df['pred_demand']

    forecast_rows.append(future_df)

    last_data = pd.concat([last_data, future_df])


forecast_lgb = pd.concat(forecast_rows)

forecast_lgb = forecast_lgb[
    ['product_id','warehouse_id','sale_date','pred_demand']
]

print(forecast_lgb)
