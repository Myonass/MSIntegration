import psycopg2
from psycopg2.extras import RealDictCursor
from allCustomerOrders import get_all_customer_orders_with_details
from allPurchaseOrders import get_all_purchase_orders_with_details
from db import upsert_customer_order
from db import upsert_purchase_order

if __name__ == "__main__":
    orders = get_all_customer_orders_with_details()
    for order in orders:
        upsert_customer_order(order)
    orders = get_all_purchase_orders_with_details()
    for order in orders:
        upsert_purchase_order(order)
    print("Обработка завершена.")
