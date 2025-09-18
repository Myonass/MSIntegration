import requests
import time
from config import API_BASE_URL, HEADERS
from currencyCodeConverter import get_currency_code
from datetime import datetime, timedelta
import re

def fetch_detailed_product_info(product_meta_href, order_moment=None):
    try:
        url = f"{product_meta_href}?expand=attributes.value,uom,supplier"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        attributes = data.get("attributes", [])
        brand = None
        supplier_terms = None
        supplier_payment_due = None

        for attr in attributes:
            if attr.get("name") == "Бренд":
                brand = attr.get("value")
            elif attr.get("name") == "Условия Платежа":
                supplier_terms = attr.get("value")

        if order_moment and supplier_terms:
            try:
                match = re.search(r'(\d+)\s*дн', str(supplier_terms).lower())
                if match:
                    days = int(match.group(1))
                    dt = datetime.fromisoformat(order_moment.replace(' ', 'T') if ' ' in order_moment else order_moment)
                    due = dt + timedelta(days=days)
                    supplier_payment_due = due.isoformat()
            except Exception as e:
                print(f"Ошибка расчета даты оплаты: {e}")

        return {
            "product_name": data.get("name", "Неизвестно"),
            "brand": brand,
            "supplier_terms": supplier_terms,
            "purchase_price": data.get("buyPrice", {}).get("value", 0) / 100 if data.get("buyPrice") else None,
            "weight": data.get("weight"),
            "batch": data.get("article", None),
            "unit": data.get("uom", {}).get("name"),
            "supplier": data.get("supplier", {}).get("name"),
            "supplier_payment_due": supplier_payment_due
        }

    except requests.RequestException as e:
        print(f"❌ Ошибка при получении товара: {e}")
        return {
            "product_name": "Ошибка",
            "brand": None,
            "supplier_terms": None,
            "purchase_price": None,
            "weight": None,
            "batch": None,
            "unit": None,
            "supplier": None,
            "supplier_payment_due": None
        }

def get_agent_name(agent_meta):
    """Запрашиваем имя контрагента по meta.href"""
    if not agent_meta:
        return None
    href = agent_meta.get("href")
    if not href:
        return None
    try:
        r = requests.get(href, headers=HEADERS)
        r.raise_for_status()
        return r.json().get("name")
    except requests.RequestException:
        return None

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
            moment = order.get("moment")

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

            customer_name = order.get("agent", {}).get("name")
            if not customer_name:
                customer_name = get_agent_name(order.get("agent", {}).get("meta"))

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
                            product_info = fetch_detailed_product_info(href, order_moment=moment)

                    positions_info.append({
                        "position_id": pos.get("id"),
                        "name": product_info.get("product_name"),
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price,
                        "supplier": product_info.get("supplier"),
                        "supplier_terms": product_info.get("supplier_terms"),
                        "purchase_price": product_info.get("purchase_price"),
                        "weight": product_info.get("weight"),
                        "batch": product_info.get("batch"),
                        "brand": product_info.get("brand"),
                        "unit": product_info.get("unit"),
                        "supplier_payment_due": product_info.get("supplier_payment_due")
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
                "customer_name": customer_name,
                "positions": positions_info
            })

        offset += limit

    return all_orders
