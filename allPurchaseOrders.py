import requests
from getToken import get_token

def get_all_purchase_orders():
    """
    Получает все заказы поставщикам с необходимыми полями.
    """
    token = get_token()
    url = "https://online.moysklad.ru/api/remap/1.2/entity/purchaseorder"
    params = {
        "expand": "attributes,supplier"
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    orders = []
    for item in data.get("rows", []):
        attrs = {a["name"]: a.get("value") for a in item.get("attributes", [])}

        orders.append({
            "ms_id": item.get("id"),
            "name": item.get("name"),
            "created": item.get("created"),
            "updated": item.get("updated"),
            "supplier_name": item.get("supplier", {}).get("name"),
            "payment_balance": attrs.get("Остаток платежа"),
            "supplier_payment_status": attrs.get("Статус оплаты"),
            "supplier_payment_fact_date": attrs.get("Фактическая дата оплаты поставки"),
            "supplier_first_payment_sum": attrs.get("Сумма первого платежа поставщику")
        })

    return orders

