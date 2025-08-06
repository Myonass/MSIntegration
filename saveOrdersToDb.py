from db import get_connection
from allCustomerOrders import get_all_customer_orders_with_details

def save_orders_to_db():
    orders = get_all_customer_orders_with_details()
    conn = get_connection()
    cur = conn.cursor()

    for order in orders:
        ms_id = order["ms_id"]
        updated_at = order["updated_at"]

        # Проверяем, есть ли заказ и его время обновления
        cur.execute("SELECT id, updated_at FROM customer_orders WHERE ms_id = %s", (ms_id,))
        result = cur.fetchone()

        if result:
            order_id_db, updated_at_db = result

            if updated_at == updated_at_db:
                # Проверяем поля вручную
                cur.execute("""
                    SELECT order_name, bitrix_deal_id, state, sum_total, currency
                    FROM customer_orders
                    WHERE id = %s
                """, (order_id_db,))
                row = cur.fetchone()
                if row == (
                    order["order_name"],
                    order["bitrix_deal_id"],
                    order["state"],
                    order["sum_total"],
                    order["currency"]
                ):
                    print(f"⏭ Заказ {order['order_name']} не изменился. Пропускаем.")
                    continue  # Данные полностью совпадают

            # Иначе — обновляем заказ и перезаписываем позиции
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
                order["order_name"],
                order["bitrix_deal_id"],
                order["state"],
                order["sum_total"],
                order["currency"],
                updated_at,
                order_id_db
            ))

            cur.execute("DELETE FROM order_positions WHERE order_id = %s", (order_id_db,))

            for pos in order["positions"]:
                cur.execute("""
                    INSERT INTO order_positions (order_id, name, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    order_id_db,
                    pos["name"],
                    pos["quantity"],
                    pos["unit_price"],
                    pos["total_price"]
                ))

            print(f"♻️ Заказ {order['order_name']} обновлён.")

        else:
            # Вставляем новый заказ
            cur.execute("""
                INSERT INTO customer_orders (ms_id, order_name, bitrix_deal_id, state, sum_total, currency, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                ms_id,
                order["order_name"],
                order["bitrix_deal_id"],
                order["state"],
                order["sum_total"],
                order["currency"],
                updated_at
            ))
            order_id = cur.fetchone()[0]

            for pos in order["positions"]:
                cur.execute("""
                    INSERT INTO order_positions (order_id, name, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    order_id,
                    pos["name"],
                    pos["quantity"],
                    pos["unit_price"],
                    pos["total_price"]
                ))

            print(f"✅ Новый заказ {order['order_name']} добавлен.")

    conn.commit()
    cur.close()
    conn.close()
    print("������ Синхронизация завершена.")

if __name__ == "__main__":
    save_orders_to_db()
