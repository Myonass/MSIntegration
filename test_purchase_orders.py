from allPurchaseOrders import get_all_purchase_orders_with_details

if __name__ == "__main__":
    orders = get_all_purchase_orders_with_details()
    print(f"Получено заказов: {len(orders)}")
    for o in orders[:3]:
        print(o)

