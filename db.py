import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
from notifier import send_telegram_message

load_dotenv()

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def get_string(val):
    if isinstance(val, dict):
        return val.get("name") or str(val)
    return val

def upsert_customer_order(order):
    conn = get_connection()
    cur = conn.cursor()

    ms_id = order.get("ms_id") or order.get("id")
    order_name = order.get("order_name", "Без названия")

    try:
        updated_at = datetime.fromisoformat(order["updated_at"]).replace(microsecond=0)
    except Exception as e:
        print(f"⚠ Ошибка формата updated_at у {order_name}: {e}")
        updated_at = datetime.now().replace(microsecond=0)

    cur.execute("SELECT id, updated_at FROM customer_orders WHERE ms_id = %s", (ms_id,))
    result = cur.fetchone()

    if result:
        order_id, existing_updated_at = result
        existing_updated_at = existing_updated_at.replace(microsecond=0)

        if updated_at <= existing_updated_at:
            print(f"⏭ Заказ {order_name} не изменился. Пропущен.")
            cur.close()
            conn.close()
            return

        cur.execute("""
            UPDATE customer_orders
            SET order_name = %s,
                bitrix_deal_id = %s,
                state = %s,
                sum_total = %s,
                currency = %s,
                updated_at = %s,
                deal_status = %s,
                deal_status_date = %s
            WHERE id = %s
        """, (
            order_name,
            order.get("bitrix_deal_id"),
            order.get("state"),
            order.get("sum_total"),
            order.get("currency"),
            updated_at,
            order.get("deal_status"),
            order.get("deal_status_date"),
            order_id
        ))

        cur.execute("DELETE FROM order_positions WHERE order_id = %s", (order_id,))
        send_telegram_message(f"♻ Обновлён заказ: {order_name}")
    else:
        cur.execute("""
            INSERT INTO customer_orders (
                ms_id, order_name, bitrix_deal_id, state, sum_total,
                currency, updated_at, deal_status, deal_status_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            ms_id,
            order_name,
            order.get("bitrix_deal_id"),
            order.get("state"),
            order.get("sum_total"),
            order.get("currency"),
            updated_at,
            order.get("deal_status"),
            order.get("deal_status_date")
        ))
        order_id = cur.fetchone()[0]
        send_telegram_message(f"✅ Добавлен новый заказ: {order_name}")

    for pos in order.get("positions", []):
        cur.execute("""
            INSERT INTO order_positions (
                order_id, position_id, product_name, quantity, price, total,
                supplier_name, supplier_terms, supplier_payment_due, purchase_price,
                weight, lot_number, brand, unit
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            order_id,
            pos.get("position_id"),
            pos.get("name"),
            pos.get("quantity"),
            pos.get("unit_price"),
            pos.get("total_price"),
            get_string(pos.get("supplier")),
            get_string(pos.get("supplier_terms")),
            pos.get("supplier_payment_due"),
            pos.get("purchase_price"),
            pos.get("weight"),
            pos.get("batch"),
            get_string(pos.get("brand")),
            pos.get("unit")
        ))

    conn.commit()
    cur.close()
    conn.close()

def upsert_purchase_order(order):
    conn = get_connection()
    cur = conn.cursor()

    ms_id = order.get("ms_id")
    order_name = order.get("name", "Без названия")

    # Обработка updated
    try:
        updated_at = datetime.fromisoformat(order["updated"]).replace(microsecond=0)
    except Exception as e:
        print(f"⚠ Ошибка формата updated у {order_name}: {e}")
        updated_at = datetime.now().replace(microsecond=0)

    # UPSERT через ON CONFLICT(ms_id)
    cur.execute("""
        INSERT INTO purchase_orders (
            ms_id, name, created, updated, payment_balance, supplier_name,
            supplier_payment_status, supplier_payment_fact_date, supplier_first_payment_sum
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ms_id) DO UPDATE SET
            name = EXCLUDED.name,
            created = EXCLUDED.created,
            updated = EXCLUDED.updated,
            payment_balance = EXCLUDED.payment_balance,
            supplier_name = EXCLUDED.supplier_name,
            supplier_payment_status = EXCLUDED.supplier_payment_status,
            supplier_payment_fact_date = EXCLUDED.supplier_payment_fact_date,
            supplier_first_payment_sum = EXCLUDED.supplier_first_payment_sum
    """, (
        ms_id,
        order_name,
        order.get("created"),
        updated_at,
        order.get("payment_balance"),
        order.get("supplier_name"),
        order.get("supplier_payment_status"),
        order.get("supplier_payment_fact_date"),
        order.get("supplier_first_payment_sum")
    ))

    send_telegram_message(f"✅ Заказ поставщика обработан: {order_name}")
    conn.commit()
    cur.close()
    conn.close()
