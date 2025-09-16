import requests
from config import API_BASE_URL, HEADERS

def normalize_purchase_order(order):
    """
    Приводит заказ к стандартной форме для сохранения в БД
    """
    # Преобразуем attributes в словарь
    attrs = {a['name']: a.get("value") for a in order.get("attributes", [])}

    # Берём "Номер заказа покупателя" прямо из attributes
    customer_order_name = attrs.get("Номер заказа покупателя")

    # Вытаскиваем имя контрагента (агента)
    agent_name = order.get("agent", {}).get("name")
    if not agent_name and "agent" in order and "meta" in order["agent"]:
        # Если агент не раскрыт, оставляем None
        agent_name = None

    return {
        "ms_id": order.get("id"),
        "name": order.get("name"),
        "created": order.get("created"),
        "updated": order.get("updated"),
        "supplier_name": agent_name,
        "payment_balance": (order.get("sum", 0) - order.get("payedSum", 0)) / 100,
        "supplier_payment_status": attrs.get("Статус оплаты"),
        "supplier_payment_fact_date": attrs.get("Фактическая дата оплаты"),
        "supplier_first_payment_sum": attrs.get("Сумма первого платежа"),
        "customer_order_name": customer_order_name
    }

def get_all_purchase_orders_with_details(limit=1000):
    """
    Получает все заказы поставщикам с деталями (с пагинацией)
    """
    orders = []
    offset = 0

    while True:
        url = f"{API_BASE_URL}/entity/purchaseorder?limit={limit}&offset={offset}"
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("rows", [])
        if not results:
            break
        for o in results:
            orders.append(normalize_purchase_order(o))
        offset += len(results)
        if len(results) < limit:
            break

    return orders

def get_purchase_order_by_id(order_id):
    """
    Получает конкретный заказ поставщика по UUID
    """
    url = f"{API_BASE_URL}/entity/purchaseorder/{order_id}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return normalize_purchase_order(resp.json())
    else:
        print(f"❌ Ошибка {resp.status_code}: не удалось получить заказ {order_id}")
        return None
