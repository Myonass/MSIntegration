from db import get_connection
from allCustomerOrders import get_all_customer_orders_with_details
from allPurchaseOrders import get_all_purchase_orders

# Универсальная функция для безопасного получения строки
def get_string(val):
    if isinstance(val, dict):
        return val.get("name") or str(val)
    return val


def save_orders_to_db():
    orders = get_all_customer_orders_with_details()
    conn = get_connection()
    cur = conn.cursor()

    for order in orders:
        ms_id = order["ms_id"]
        updated_at = order["updated_at"]

        cur.execute("SELECT id, updated_at FROM customer_orders WHERE ms_id = %s", (ms_id,))
        result = cur.fetchone()

        if result:
            order_id_db, _ = result
            cur.execute("""
                UPDATE customer_orders
                SET order_name = %s, bitrix_deal_id = %s, state = %s,
                    sum_total = %s, currency = %s, updated_at = %s,
                    deal_status = %s, deal_status_date = %s
                WHERE id = %s
            """, (
                order["order_name"], order["bitrix_deal_id"], order["state"],
                order["sum_total"], order["currency"], updated_at,
                order["deal_status"], order["deal_status_date"], order_id_db
            ))
            cur.execute("DELETE FROM order_positions WHERE order_id = %s", (order_id_db,))
        else:
            cur.execute("""
                INSERT INTO customer_orders (
                    ms_id, order_name, bitrix_deal_id, state, sum_total, currency,
                    updated_at, deal_status, deal_status_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                ms_id, order["order_name"], order["bitrix_deal_id"], order["state"],
                order["sum_total"], order["currency"], updated_at,
                order["deal_status"], order["deal_status_date"]
            ))
            order_id_db = cur.fetchone()[0]

        for pos in order["positions"]:
            cur.execute("""
                INSERT INTO order_positions (
                    order_id, position_id, product_name, quantity, price, total,
                    supplier_name, supplier_terms, supplier_payment_due,
                    purchase_price, weight, lot_number, brand, unit
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                order_id_db, pos.get("position_id"), pos.get("name"),
                pos.get("quantity"), pos.get("unit_price"), pos.get("total_price"),
                get_string(pos.get("supplier")), get_string(pos.get("supplier_terms")),
                pos.get("supplier_payment_due"), pos.get("purchase_price"),
                pos.get("weight"), pos.get("batch"), get_string(pos.get("brand")),
                pos.get("unit")
            ))

        print(f"✅ Заказ клиента обработан: {order['order_name']}")

    conn.commit()
    cur.close()
    conn.close()
    print("������ Синхронизация заказов клиентов завершена.")


def save_purchase_orders_to_db():
    orders = get_all_purchase_orders()
    conn = get_connection()
    cur = conn.cursor()

    for order in orders:
        cur.execute("""
            INSERT INTO purchase_orders (
                ms_id, name, created, updated,
                payment_balance, supplier_name,
                supplier_payment_status, supplier_payment_fact_date,
                supplier_first_payment_sum
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ms_id) DO UPDATE
            SET name = EXCLUDED.name,
                created = EXCLUDED.created,
                updated = EXCLUDED.updated,
                payment_balance = EXCLUDED.payment_balance,
                supplier_name = EXCLUDED.supplier_name,
                supplier_payment_status = EXCLUDED.supplier_payment_status,
                supplier_payment_fact_date = EXCLUDED.supplier_payment_fact_date,
                supplier_first_payment_sum = EXCLUDED.supplier_first_payment_sum;
        """, (
            order["ms_id"], order["name"], order["created"], order["updated"],
            order["payment_balance"], order["supplier_name"],
            order["supplier_payment_status"], order["supplier_payment_fact_date"],
            order["supplier_first_payment_sum"]
        ))

        print(f"✅ Заказ поставщика обработан: {order['name']}")

    conn.commit()
    cur.close()
    conn.close()
    print("������ Синхронизация заказов поставщиков завершена.")


if __name__ == "__main__":
    save_orders_to_db()
    save_purchase_orders_to_db()
