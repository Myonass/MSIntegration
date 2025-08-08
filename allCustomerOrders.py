import requests
import time
from config import API_BASE_URL, HEADERS
from currencyCodeConverter import get_currency_code

def fetch_detailed_product_info(product_meta_href):
    try:
        url = f"{product_meta_href}?expand=attributes.value"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        attributes = data.get("attributes", [])
        brand = None
        supplier_terms = None

        for attr in attributes:
            if attr.get("name") == "Бренд":
                brand = attr.get("value")
            elif attr.get("name") == "Условия Платежа":
                supplier_terms = attr.get("value")

        return {
            "product_name": data.get("name", "Неизвестно"),
            "brand": brand,
            "supplier_terms": supplier_terms,
            "purchase_price": data.get("buyPrice", {}).get("value", 0) / 100 if data.get("buyPrice") else None,
            "weight": data.get("weight"),
            "batch": data.get("article", None)
        }

    except requests.RequestException as e:
        print(f"❌ Ошибка при получении товара: {e}")
        return {
            "product_name": "Ошибка",
            "brand": None,
            "supplier_terms": None,
            "purchase_price": None,
            "weight": None,
            "batch": None
        }

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
            order_id = order.get("id")
            order_name = order.get("name")
            sum_total = order.get("sum", 0) / 100
            currency_href = order.get("rate", {}).get("currency", {}).get("meta", {}).get("href")
            currency = get_currency_code(currency_href) if currency_href else "UNKNOWN"
            updated = order.get("updated")

            deal_id = None
            status = "Без статуса"
            deal_status = "Неизвестно"
            deal_status_date = None

            for attr in order.get("attributes", []):
                name = attr.get("name", "").lower()
                if "битрикс" in name or "сделк" in name:
                    deal_id = attr.get("value")
                elif "статус заказа" in name:
                    status = attr.get("value")
                elif "статус сделки" in name:
                    deal_status = attr.get("value")
                    deal_status_date = attr.get("updated") or updated

            state = status or order.get("state", {}).get("name", "Без статуса")

            positions_info = []
            pos_url = f"{API_BASE_URL}/entity/customerorder/{order_id}/positions"
            pos_resp = requests.get(pos_url, headers=HEADERS)
            time.sleep(0.2)  # Уважение к API

            if pos_resp.ok:
                for pos in pos_resp.json().get("rows", []):
                    quantity = int(float(pos.get("quantity", 0)))
                    unit_price = pos.get("price", 0) / 100
                    total_price = quantity * unit_price

                    product_info = {}
                    assort = pos.get("assortment")
                    if isinstance(assort, dict):
                        href = assort.get("meta", {}).get("href")
                        if href:
                            product_info = fetch_detailed_product_info(href)

                    positions_info.append({
                        "position_id": pos.get("id"),
                        "name": product_info.get("product_name"),
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price,
                        "supplier": None,
                        "supplier_terms": product_info.get("supplier_terms"),
                        "purchase_price": product_info.get("purchase_price"),
                        "weight": product_info.get("weight"),
                        "batch": product_info.get("batch"),
                        "brand": product_info.get("brand")
                    })

            all_orders.append({
                "ms_id": order_id,
                "order_name": order_name,
                "bitrix_deal_id": deal_id,
                "state": state,
                "sum_total": sum_total,
                "currency": currency,
                "updated_at": updated,
                "deal_status": deal_status,
                "deal_status_date": deal_status_date,
                "positions": positions_info
            })

        offset += limit

    return all_orders
