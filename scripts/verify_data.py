import pandas as pd

df = pd.read_csv("raw_data/india_weather_raw.csv")

print("=== DATA VERIFICATION ===")
print(f"Shape         : {df.shape}")
print(f"Date range    : {df['date'].min()}  to  {df['date'].max()}")
print(f"Cities        : {list(df['city'].unique())}")
print(f"\nMissing values:\n{df.isnull().sum()}")
print("\nSample rows:")
print(df.sample(5))
