# test_allCustomerOrders.py
from allCustomerOrders import get_all_customer_orders_with_details

if __name__ == "__main__":
    orders = get_all_customer_orders_with_details()
    print(f"Получено заказов: {len(orders)}\n")

    # Ищем заказ 41336
    target_order = None
    for o in orders:
        if o.get("order_name") == "41336":
            target_order = o
            break

    if target_order:
        print("------ Заказ 41336 ------")
        for key, value in target_order.items():
            if key == "positions":
                print(f"{key}:")
                for pos in value:
                    print(f"  - {pos}")
            else:
                print(f"{key}: {value}")
        print("---------------------------\n")
    else:
        print("❌ Заказ 41336 не найден")
