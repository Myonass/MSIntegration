# order_linker.py
import psycopg2
from psycopg2.extras import RealDictCursor
from db import get_connection

class CustomerPurchaseLinker:
    def __init__(self):
        self.conn = get_connection()
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    def create_link_table(self):
        """Создаёт таблицу для связей заказов, если её нет"""
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS customer_purchase_link (
            id SERIAL PRIMARY KEY,
            customer_order_id INTEGER NOT NULL REFERENCES customer_orders(id) ON DELETE CASCADE,
            purchase_order_id UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
            link_created TIMESTAMP DEFAULT NOW()
        );
        """)
        self.conn.commit()
        print("✅ Таблица customer_purchase_link готова")

    def link_orders(self):
        """
        Связывает заказы поставщиков с заказами клиентов по номеру заказа.
        Берёт поле 'Номер заказа покупателя' в purchase_orders и ищет совпадение в customer_orders.order_name
        """
        # Получаем все заказы поставщиков с заполненным полем номера заказа клиента
        self.cur.execute("""
            SELECT id AS purchase_id, name, ms_id
            FROM purchase_orders
            WHERE name IS NOT NULL
        """)
        purchase_orders = self.cur.fetchall()

        for po in purchase_orders:
            # Извлекаем номер заказа клиента из имени заказа поставщика (например, "38848_1" -> "38848")
            customer_order_number = po['name'].split("_")[0].strip()
            if not customer_order_number:
                continue

            # Ищем соответствующий заказ клиента
            self.cur.execute("""
                SELECT id
                FROM customer_orders
                WHERE order_name = %s
            """, (customer_order_number,))
            co = self.cur.fetchone()
            if co:
                # Вставляем связь, если её ещё нет
                self.cur.execute("""
                    INSERT INTO customer_purchase_link (customer_order_id, purchase_order_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (co['id'], po['purchase_id']))
                print(f"Связано CO {customer_order_number} -> PO {po['name']}")

        self.conn.commit()
        print("✅ Связи заказов поставщиков и клиентов обновлены")

    def close(self):
        self.cur.close()
        self.conn.close()
