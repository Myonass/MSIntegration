import requests
import time
from config import API_BASE_URL, HEADERS
from currencyCodeConverter import get_currency_code

def fetch_assortment_name(href):
    try:
        time.sleep(0.3)
        resp = requests.get(href, headers=HEADERS)
        resp.raise_for_status()
        return resp.json().get("name", "Неизвестно")
    except Exception:
        return "Неизвестно"

def get_all_customer_orders_with_details():
    url = f"{API_BASE_URL}/entity/customerorder"
    all_orders = []
    offset = 0
    limit = 100

    while True:
        params = {"offset": offset, "limit": limit}
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        rows = resp.json().get("rows", [])

        if not rows:
            break

        for order in rows:
            order_name = order.get("name")
            sum_total = order.get("sum", 0) / 100

            curr_href = order.get("rate", {}).get("currency", {}).get("meta", {}).get("href")
            currency = get_currency_code(curr_href) if curr_href else "UNKNOWN"

            deal_id = None
            status = "Без статуса"
            for attr in order.get("attributes", []):
                attr_name = attr.get("name", "").lower()
                if "битрикс" in attr_name or "сделк" in attr_name:
                    deal_id = attr.get("value")
                elif "статус заказа" in attr_name:
                    status = attr.get("value")

            state = status or order.get("state", {}).get("name") or "Без статуса"

            updated = order.get("updated")  # ISO timestamp

            positions_info = []
            pos_url = f"{API_BASE_URL}/entity/customerorder/{order['id']}/positions"
            pos_resp = requests.get(pos_url, headers=HEADERS)
            time.sleep(0.3)

            if pos_resp.status_code == 200:
                for pos in pos_resp.json().get("rows", []):
                    assort = pos.get("assortment")
                    if isinstance(assort, dict) and assort.get("name"):
                        pos_name = assort["name"]
                    elif isinstance(assort, dict):
                        href = assort.get("meta", {}).get("href")
                        pos_name = fetch_assortment_name(href) if href else "Неизвестно"
                    else:
                        pos_name = "Неизвестно"

                    quantity = int(float(pos.get("quantity", 0)))
                    unit_price = pos.get("price", 0) / 100
                    total_price = quantity * unit_price

                    positions_info.append({
                        "name": pos_name,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price
                    })

            all_orders.append({
                "ms_id": order.get("id"),
                "order_name": order_name,
                "bitrix_deal_id": deal_id,
                "state": state,
                "sum_total": sum_total,
                "currency": currency,
                "updated_at": updated,
                "positions": positions_info
            })

        offset += limit

    return all_orders
