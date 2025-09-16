from allPurchaseOrders import get_all_purchase_orders_with_details

if __name__ == "__main__":
    orders = get_all_purchase_orders_with_details()
    print(f"Получено заказов: {len(orders)}\n")

    # Ищем заказ 35570_1
    target_order = None
    for o in orders:
        if o.get("name") == "35570_1":
            target_order = o
            break

    if target_order:
        print("------ Заказ 35570_1 ------")
        for key, value in target_order.items():
            print(f"{key}: {value}")
        print("---------------------------\n")
    else:
        print("❌ Заказ 35570_1 не найден")
