import requests
from getTokenPurchase import get_token_purchase

def normalize_purchase_order(order):
    """
    Приводит заказ к стандартной форме для сохранения в БД
    """
    attrs = {a['name']: a.get('value') for a in order.get('attributes', [])}

    return {
        "ms_id": order.get("id"),
        "name": order.get("name"),
        "created": order.get("created"),
        "updated": order.get("updated"),
        "supplier_name": order.get("agent", {}).get("name"),  # через expand=agent
        "payment_balance": (order.get("sum", 0) - order.get("payedSum", 0)) / 100,  # сумма в рублях
        "supplier_payment_status": attrs.get("Статус оплаты"),
        "supplier_payment_fact_date": attrs.get("Фактическая дата оплаты"),
        "supplier_first_payment_sum": attrs.get("Сумма первого платежа"),
    }

def get_all_purchase_orders_with_details(offset=0, limit=100):
    """
    Получает все заказы с деталями и нормализует их
    """
    headers = get_token_purchase()
    url = "https://api.moysklad.ru/api/remap/1.2/entity/purchaseorder"
    params = {
        "offset": offset,
        "limit": limit,
        "expand": "agent,attributes"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    orders = [normalize_purchase_order(item) for item in data.get("rows", [])]

    return orders
