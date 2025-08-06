from allCustomerOrders import get_all_customer_orders_with_details
from db import upsert_customer_order

if __name__ == "__main__":
    orders = get_all_customer_orders_with_details()
    for order in orders:
        upsert_customer_order(order)
    print("Обработка завершена.")
