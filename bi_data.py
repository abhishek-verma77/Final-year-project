import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

print("Starting dataset generation...")

# --- CONFIGURATION ---
NUM_PRODUCTS = 50
NUM_CUSTOMERS = 300
NUM_STORES = 10
NUM_SALES_TRANSACTIONS = 2000

# --- DATA LISTS ---
product_categories = ["Electronics", "Apparel", "Home Goods", "Groceries", "Beauty"]
regions = ["West", "Northeast", "South", "Midwest"]
store_cities = ["Los Angeles", "New York", "Miami", "Chicago", "Houston", "Seattle", "Boston", "Denver", "Atlanta", "Phoenix"]
product_name_stems = ["Premium", "Eco-Friendly", "Compact", "Heavy-Duty", "Smart", "Classic", "Deluxe", "Simple"]
product_name_nouns = ["Widget", "Gadget", "Appliance", "Device", "Tool", "Kit", "Set", "Unit"]
customer_first_names = ["John", "Jane", "Peter", "Mary", "Chris", "Pat", "Alex", "Sam", "Mike", "Lisa"]
customer_last_names = ["Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson", "Taylor", "Clark"]

# --- 1. GENERATE STORES DIMENSION ---
stores_list = []
for i in range(1, NUM_STORES + 1):
    stores_list.append({
        "StoreID": f"S{100 + i}",
        "StoreName": f"XYZ {random.choice(store_cities)}",
        "Region": random.choice(regions)
    })
stores_df = pd.DataFrame(stores_list)
print("Stores data created.")

# --- 2. GENERATE PRODUCTS DIMENSION ---
products_list = []
for i in range(1, NUM_PRODUCTS + 1):
    category = random.choice(product_categories)
    unit_price = round(random.uniform(5.0, 500.0), 2)
    products_list.append({
        "ProductID": f"P{1000 + i}",
        "ProductName": f"{random.choice(product_name_stems)} {random.choice(product_name_nouns)}",
        "Category": category,
        "UnitPrice": unit_price,
        "Cost": round(unit_price * random.uniform(0.4, 0.7), 2) # Cost is 40-70% of price
    })
products_df = pd.DataFrame(products_list)
print("Products data created.")

# --- 3. GENERATE CUSTOMERS DIMENSION ---
customers_list = []
for i in range(1, NUM_CUSTOMERS + 1):
    customers_list.append({
        "CustomerID": f"C{2000 + i}",
        "CustomerName": f"{random.choice(customer_first_names)} {random.choice(customer_last_names)}",
        "LoyaltyProgramMember": random.choice(["Yes", "No"])
    })
customers_df = pd.DataFrame(customers_list)
print("Customers data created.")

# --- 4. GENERATE SALES DATA (Fact Table) ---
sales_list = []
product_ids = products_df['ProductID'].tolist()
customer_ids = customers_df['CustomerID'].tolist()
store_ids = stores_df['StoreID'].tolist()
start_date = datetime.now() - timedelta(days=365)

for i in range(1, NUM_SALES_TRANSACTIONS + 1):
    product_id = random.choice(product_ids)
    quantity_sold = random.randint(1, 5)
    unit_price = products_df.loc[products_df['ProductID'] == product_id, 'UnitPrice'].iloc[0]
    sales_list.append({
        "TransactionID": 10000 + i,
        "Date": (start_date + timedelta(days=random.randint(0, 364))).strftime('%Y-%m-%d'),
        "CustomerID": random.choice(customer_ids),
        "ProductID": product_id,
        "StoreID": random.choice(store_ids),
        "Quantity": quantity_sold,
        "TotalSale": round(quantity_sold * unit_price, 2)
    })
sales_df = pd.DataFrame(sales_list)
print("Sales data created.")


# --- 5. GENERATE INVENTORY DATA (Snapshot) ---
inventory_list = []
for store_id in store_ids:
    for product_id in product_ids:
        inventory_list.append({
            "StoreID": store_id,
            "ProductID": product_id,
            "StockLevel": random.randint(0, 250) # 0 means stockout
        })
inventory_df = pd.DataFrame(inventory_list)
print("Inventory data created.")


# --- SAVE TO CSV ---
stores_df.to_csv("stores_dim.csv", index=False)
products_df.to_csv("products_dim.csv", index=False)
customers_df.to_csv("customers_dim.csv", index=False)
sales_df.to_csv("sales_data.csv", index=False)
inventory_df.to_csv("inventory_data.csv", index=False)

print("\nAll CSV files have been generated successfully!")
print("You can now find them in the same folder as the script.")