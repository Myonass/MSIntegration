import os
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class CurrencyRateLoader:
    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")

        self.base_url = "https://www.cbr.ru/scripts/XML_dynamic.asp"
        # Коды валют ЦБ РФ
        self.codes = {
            "EUR": "R01239",
            "USD": "R01235",
            "CNY": "R01375",
        }

    def get_connection(self):
        return psycopg2.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
        )

    def fetch_rates(self, val_code, start_date, end_date):
        """Запрашиваем курсы валюты к рублю из ЦБ РФ"""
        params = {
            "date_req1": start_date.strftime("%d/%m/%Y"),
            "date_req2": end_date.strftime("%d/%m/%Y"),
            "VAL_NM_RQ": val_code,
        }
        resp = requests.get(self.base_url, params=params)
        resp.encoding = "windows-1251"
        root = ET.fromstring(resp.text)

        records = []
        for record in root.findall("Record"):
            date_str = record.attrib["Date"]
            value = record.find("Value").text
            value = float(value.replace(",", "."))
            date = datetime.strptime(date_str, "%d.%m.%Y")
            records.append({"date": date, "rate": value})

        return pd.DataFrame(records)

    def calculate_monthly_avg(self, df):
        """Считаем средний курс за месяц"""
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
        monthly_avg = (
            df.groupby(["year", "month"])["rate"].mean().reset_index()
        )
        return monthly_avg

    def save_to_db(self, monthly_avg, currency):
        """Сохраняем данные в БД"""
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS currency_rates (
                id SERIAL PRIMARY KEY,
                year INT NOT NULL,
                month INT NOT NULL,
                currency VARCHAR(10) NOT NULL,
                rate NUMERIC(12, 6) NOT NULL,
                UNIQUE(year, month, currency)
            )
            """
        )

        for _, row in monthly_avg.iterrows():
            cur.execute(
                """
                INSERT INTO currency_rates (year, month, currency, rate)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (year, month, currency)
                DO UPDATE SET rate = EXCLUDED.rate
                """,
                (
                    int(row["year"]),
                    int(row["month"]),
                    currency,
                    round(float(row["rate"]), 6),
                ),
            )

        conn.commit()
        cur.close()
        conn.close()

    def run(self):
        print("Загружаем курсы RUB→EUR, USD→EUR, CNY→EUR...")

        end_date = datetime.today()
        start_date = end_date - timedelta(days=3 * 365)

        # загружаем все курсы к рублю
        eur_df = self.fetch_rates(self.codes["EUR"], start_date, end_date)
        usd_df = self.fetch_rates(self.codes["USD"], start_date, end_date)
        cny_df = self.fetch_rates(self.codes["CNY"], start_date, end_date)

        eur_avg = self.calculate_monthly_avg(eur_df)
        usd_avg = self.calculate_monthly_avg(usd_df)
        cny_avg = self.calculate_monthly_avg(cny_df)

        # объединяем по год/месяц
        merged = eur_avg.merge(usd_avg, on=["year", "month"], suffixes=("_eur", "_usd"))
        merged = merged.merge(cny_avg, on=["year", "month"])
        merged.rename(columns={"rate": "rate_cny"}, inplace=True)

        # RUB -> EUR (инверсия)
        merged["RUB/EUR"] = 1 / merged["rate_eur"]
        # USD -> EUR
        merged["USD/EUR"] = merged["rate_usd"] / merged["rate_eur"]
        # CNY -> EUR
        merged["CNY/EUR"] = merged["rate_cny"] / merged["rate_eur"]

        # сохраняем
        for currency in ["RUB/EUR", "USD/EUR", "CNY/EUR"]:
            df = merged[["year", "month", currency]].rename(columns={currency: "rate"})
            self.save_to_db(df, currency)

        print("✅ Курсы RUB→EUR, USD→EUR и CNY→EUR сохранены в БД")


if __name__ == "__main__":
    loader = CurrencyRateLoader()
    loader.run()
