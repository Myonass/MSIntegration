import requests
from config import API_BASE_URL, HEADERS

def fetch_agent_name(agent_meta):
    """
    Получает имя контрагента по meta.href
    """
    try:
        href = agent_meta.get("href")
        if not href:
            return None
        resp = requests.get(href, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        return data.get("name")
    except Exception as e:
        print(f"⚠️ Не удалось получить имя контрагента: {e}")
        return None


def normalize_purchase_order(order):
    """
    Приводит заказ к стандартной форме для сохранения в БД
    """
    attrs = {a['name']: a.get("value") for a in order.get("attributes", [])}
    customer_order_name = attrs.get("Номер заказа покупателя")

    # Ищем имя контрагента
    agent = order.get("agent", {})
    agent_name = agent.get("name")
    if not agent_name and "meta" in agent:
        agent_name = fetch_agent_name(agent["meta"])

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
    url = f"{API_BASE_URL}/entity/purchaseorder/{order_id}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return normalize_purchase_order(resp.json())
    else:
        print(f"❌ Ошибка {resp.status_code}: не удалось получить заказ {order_id}")
        return None
