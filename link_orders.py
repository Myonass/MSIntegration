from order_linker import CustomerPurchaseLinker

if __name__ == "__main__":
    linker = CustomerPurchaseLinker()
    linker.create_link_table()  # создаём таблицу, если её нет
    linker.link_orders()        # связываем все заказы
    linker.close()
    print("✅ Связь заказов создана")
