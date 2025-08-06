import os
from dotenv import load_dotenvimport psycopg2
from psycopg2.extras import RealDictCursor
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
                updated_at = %s
            WHERE id = %s
        """, (
            order_name,
            order.get("bitrix_deal_id"),
            order.get("state"),
            order.get("sum_total"),
            order.get("currency"),
            updated_at,
            order_id
        ))

        cur.execute("DELETE FROM order_positions WHERE order_id = %s", (order_id,))
        send_telegram_message(f"♻ Обновлён заказ: {order_name}")
        print(f"♻ Обновлён заказ: {order_name}")

    else:
        cur.execute("""
            INSERT INTO customer_orders (ms_id, order_name, bitrix_deal_id, state, sum_total, currency, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            ms_id,
            order_name,
            order.get("bitrix_deal_id"),
            order.get("state"),
            order.get("sum_total"),
            order.get("currency"),
            updated_at
        ))
        order_id = cur.fetchone()[0]
        send_telegram_message(f"✅ Добавлен новый заказ: {order_name}")
        print(f"✅ Добавлен новый заказ: {order_name}")

    for pos in order.get("positions", []):
        cur.execute("""
            INSERT INTO order_positions (order_id, name, quantity, unit_price, total_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            order_id,
            pos.get("name"),
            pos.get("quantity"),
            pos.get("unit_price"),
            pos.get("total_price")
        ))

    conn.commit()
    cur.close()
    conn.close()
