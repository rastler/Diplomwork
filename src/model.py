import sqlite3
import os
from datetime import datetime, timedelta
from math import ceil
import pandas as pd
from fpdf import FPDF

# ===== Сутності =====

class Bike:
    def __init__(self, id, model, serial_number, type, status, price_per_hour):
        self.id = id
        self.model = model
        self.serial_number = serial_number
        self.type = type
        self.status = status
        self.price_per_hour = price_per_hour

    def __repr__(self):
        return f"Bike({self.id}, {self.model}, {self.status})"


class Client:
    def __init__(self, id, name, phone, email, document, created_at):
        self.id = id
        self.name = name
        self.phone = phone
        self.email = email
        self.document = document
        self.created_at = created_at

    def __repr__(self):
        return f"Client({self.id}, {self.name})"


class Rental:
    def __init__(self, id, client_id, bike_id, start_time, duration, end_time, status, total_cost, discount, created_at):
        self.id = id
        self.client_id = client_id
        self.bike_id = bike_id
        self.start_time = start_time
        self.duration = duration
        self.end_time = end_time
        self.status = status
        self.total_cost = total_cost
        self.discount = discount
        self.created_at = created_at

    def __repr__(self):
        return f"Rental({self.id}, Client: {self.client_id}, Bike: {self.bike_id}, {self.status})"


# ===== Клас для роботи з базою даних =====

class Database:
    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        # Увімкнення підтримки foreign keys

    def get_cursor(self):
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()


# ===== DAO для клієнтів =====

class ClientDAO:
    def __init__(self, db: Database):
        self.db = db

    def create_table(self):
        cursor = self.db.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                document TEXT,
                created_at DATETIME DEFAULT (datetime('now','localtime'))
            )
        ''')
        self.db.commit()

    def add_client(self, name, phone, email, document):
        cursor = self.db.get_cursor()
        try:
            cursor.execute('''
                INSERT INTO clients (name, phone, email, document)
                VALUES (?, ?, ?, ?)
            ''', (name, phone, email, document))
            self.db.commit()
            return True
        except Exception as e:
            print("Error adding client:", e)
            return False

    def update_client(self, client_id, name=None, phone=None, email=None, document=None):
        cursor = self.db.get_cursor()
        fields = []
        values = []
        if name is not None:
            fields.append("name = ?")
            values.append(name)
        if phone is not None:
            fields.append("phone = ?")
            values.append(phone)
        if email is not None:
            fields.append("email = ?")
            values.append(email)
        if document is not None:
            fields.append("document = ?")
            values.append(document)
        if not fields:
            return False
        values.append(client_id)
        query = "UPDATE clients SET " + ", ".join(fields) + " WHERE id = ?"
        try:
            cursor.execute(query, tuple(values))
            self.db.commit()
            return True
        except Exception as e:
            print("Error updating client:", e)
            return False

    def delete_client(self, client_id):
        cursor = self.db.get_cursor()
        try:
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            self.db.commit()
            return True, "Клієнта видалено."
        except Exception as e:
            return False, str(e)

    def get_all(self):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT id, name, phone, email, document, created_at FROM clients")
        rows = cursor.fetchall()
        clients = []
        for row in rows:
            clients.append(Client(row["id"], row["name"], row["phone"],
                                  row["email"], row["document"], row["created_at"]))
        return clients

    def search(self, search_text):
        cursor = self.db.get_cursor()
        query = """
            SELECT id, name, phone, email, document, created_at 
            FROM clients 
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        """
        wildcard = f"%{search_text}%"
        cursor.execute(query, (wildcard, wildcard, wildcard))
        rows = cursor.fetchall()
        clients = []
        for row in rows:
            clients.append(Client(row["id"], row["name"], row["phone"],
                                  row["email"], row["document"], row["created_at"]))
        return clients


# ===== DAO для велосипедів =====

class BikeDAO:
    def __init__(self, db: Database):
        self.db = db

    def create_table(self):
        cursor = self.db.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                serial_number TEXT,
                type TEXT,
                status TEXT,
                price_per_hour REAL,
                last_maintenance_date DATETIME
            )
        ''')
        self.db.commit()

    def add_bike(self, model, serial_number, bike_type, price_per_hour):
        cursor = self.db.get_cursor()
        try:
            cursor.execute('''
                INSERT INTO bikes (model, serial_number, type, status, price_per_hour)
                VALUES (?, ?, ?, ?, ?)
            ''', (model, serial_number, bike_type, "Доступний", price_per_hour))
            self.db.commit()
            return True
        except Exception as e:
            print("Error adding bike:", e)
            return False

    def update_bike(self, bike_id, model=None, serial_number=None, bike_type=None, status=None, price_per_hour=None):
        cursor = self.db.get_cursor()
        fields = []
        values = []
        if model is not None:
            fields.append("model = ?")
            values.append(model)
        if serial_number is not None:
            fields.append("serial_number = ?")
            values.append(serial_number)
        if bike_type is not None:
            fields.append("type = ?")
            values.append(bike_type)
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if price_per_hour is not None:
            fields.append("price_per_hour = ?")
            values.append(price_per_hour)
        if not fields:
            return False
        values.append(bike_id)
        query = "UPDATE bikes SET " + ", ".join(fields) + " WHERE id = ?"
        try:
            cursor.execute(query, tuple(values))
            self.db.commit()
            return True
        except Exception as e:
            print("Error updating bike:", e)
            return False

    def delete_bike(self, bike_id):
        cursor = self.db.get_cursor()
        try:
            cursor.execute("DELETE FROM bikes WHERE id = ?", (bike_id,))
            self.db.commit()
            return True, "Велосипед видалено."
        except Exception as e:
            return False, str(e)

    def get_all(self):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT id, model, serial_number, type, status, price_per_hour FROM bikes")
        rows = cursor.fetchall()
        bikes = []
        for row in rows:
            bikes.append(Bike(row["id"], row["model"], row["serial_number"],
                              row["type"], row["status"], row["price_per_hour"]))
        return bikes

    def get_available(self):
        cursor = self.db.get_cursor()
        cursor.execute("""
            SELECT id, model, serial_number, type, status, price_per_hour 
            FROM bikes 
            WHERE status = 'Доступний'
        """)
        rows = cursor.fetchall()
        bikes = []
        for row in rows:
            bikes.append(Bike(row["id"], row["model"], row["serial_number"],
                              row["type"], row["status"], row["price_per_hour"]))
        return bikes

    def search(self, search_text, bike_type, status):
        cursor = self.db.get_cursor()
        query = "SELECT id, model, serial_number, type, status, price_per_hour FROM bikes WHERE 1=1"
        values = []
        if search_text:
            query += " AND (model LIKE ? OR serial_number LIKE ?)"
            values.extend((f"%{search_text}%", f"%{search_text}%"))
        if bike_type and bike_type != "Всі типи":
            query += " AND type = ?"
            values.append(bike_type)
        if status and status != "Всі статуси":
            query += " AND status = ?"
            values.append(status)
        else:
            query += " AND status = 'Доступний'"
        cursor.execute(query, tuple(values))
        rows = cursor.fetchall()
        bikes = []
        for row in rows:
            bikes.append(Bike(row["id"], row["model"], row["serial_number"],
                              row["type"], row["status"], row["price_per_hour"]))
        return bikes

    def update_bike_status(self, bike_id, status):
        cursor = self.db.get_cursor()
        try:
            cursor.execute("UPDATE bikes SET status = ? WHERE id = ?", (status, bike_id))
            self.db.commit()
            return True
        except Exception as e:
            print("Error updating bike status:", e)
            return False


# ===== DAO для оренд =====

class RentalDAO:
    def __init__(self, db: Database, bike_dao: BikeDAO):
        self.db = db
        self.bike_dao = bike_dao

    def create_table(self):
        cursor = self.db.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                bike_id INTEGER NOT NULL,
                start_time DATETIME NOT NULL,
                duration INTEGER,
                end_time DATETIME,
                status TEXT,
                total_cost REAL,
                discount REAL DEFAULT 0,
                is_paid INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now','localtime')),
                FOREIGN KEY(client_id) REFERENCES clients(id),
                FOREIGN KEY(bike_id) REFERENCES bikes(id)
            )
        ''')
        self.db.commit()

    def get_rental_history_for_client(self, client_id):
        cursor = self.db.get_cursor()
        query = """
            SELECT r.*, b.model as bike_model 
            FROM rentals r
            LEFT JOIN bikes b ON r.bike_id = b.id
            WHERE client_id = ?
            ORDER BY start_time DESC
        """
        cursor.execute(query, (client_id,))
        rows = cursor.fetchall()
        rentals = []
        for row in rows:
            rental = Rental(
                row["id"],
                row["client_id"],
                row["bike_id"],
                row["start_time"],
                row["duration"],
                row["end_time"],
                row["status"],
                row["total_cost"],
                row["discount"],
                row["created_at"]
            )
            rental.bike_model = row["bike_model"] if "bike_model" in row.keys() else ""
            rentals.append(rental)
        return rentals

    def get_income_today(self):
        try:
            cursor = self.db.get_cursor()
            today_str = datetime.now().strftime("%Y-%m-%d")
            query = """
                SELECT SUM(total_cost) AS income 
                FROM rentals 
                WHERE status = 'Завершена' AND DATE(end_time) = ?
            """
            cursor.execute(query, (today_str,))
            row = cursor.fetchone()
            income = row["income"] if row["income"] is not None else 0
            return income
        except Exception as e:
            print(f"Помилка розрахунку доходу за сьогодні: {e}")
            return 0

    def delete_rental(self, rental_id):
        cursor = self.db.get_cursor()
        try:
            cursor.execute("DELETE FROM rentals WHERE id = ?", (rental_id,))
            self.db.commit()
            return True, "Оренду скасовано."
        except Exception as e:
            return False, str(e)

    def create_rental(self, client_id, bike_id, start_time_str, duration, discount):
        cursor = self.db.get_cursor()
        try:
            price = self.calculate_rental_price(bike_id, duration, discount)
            cursor.execute('''
                INSERT INTO rentals (client_id, bike_id, start_time, duration, total_cost, discount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (client_id, bike_id, start_time_str, duration, price, discount, "Активна"))
            rental_id = cursor.lastrowid
            self.db.commit()
            self.bike_dao.update_bike_status(bike_id, "В оренді")
            return rental_id, "Оренду створено успішно."
        except Exception as e:
            return None, str(e)

    def complete_rental(self, rental_id):
        cursor = self.db.get_cursor()
        try:
            cursor.execute("SELECT bike_id FROM rentals WHERE id = ?", (rental_id,))
            row = cursor.fetchone()
            if row is None:
                return False, "Оренду не знайдено."
            bike_id = row["bike_id"]
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE rentals SET status = ?, end_time = ? WHERE id = ?",
                           ("Завершена", end_time, rental_id))
            self.db.commit()
            self.bike_dao.update_bike_status(bike_id, "Доступний")
            return True, "Оренду завершено успішно."
        except Exception as e:
            return False, str(e)

    def extend_rental(self, rental_id, additional_duration):
        cursor = self.db.get_cursor()
        try:
            cursor.execute("SELECT duration FROM rentals WHERE id = ?", (rental_id,))
            row = cursor.fetchone()
            if row:
                new_duration = row[0] + additional_duration
                cursor.execute("SELECT bike_id, discount FROM rentals WHERE id = ?", (rental_id,))
                bike_info = cursor.fetchone()
                if bike_info:
                    bike_id, discount = bike_info
                    new_cost = self.calculate_rental_price(bike_id, new_duration, discount)
                    cursor.execute("UPDATE rentals SET duration = ?, total_cost = ? WHERE id = ?",
                                   (new_duration, new_cost, rental_id))
                    self.db.commit()
                    return True, "Оренду продовжено успішно."
            return False, "Оренду не знайдено."
        except Exception as e:
            return False, str(e)

    def get_active(self):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT * FROM rentals WHERE status = 'Активна'")
        rows = cursor.fetchall()
        rentals = []
        for row in rows:
            rentals.append(Rental(
                row["id"], row["client_id"], row["bike_id"],
                row["start_time"], row["duration"], row["end_time"],
                row["status"], row["total_cost"], row["discount"],
                row["created_at"]
            ))
        return rentals

    def calculate_rental_price(self, bike_id, duration, discount):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT price_per_hour FROM bikes WHERE id = ?", (bike_id,))
        row = cursor.fetchone()
        if row:
            base_price = row[0]
            total = base_price * duration
            if discount:
                total -= total * (discount / 100.0)
            return round(total, 2)
        return None

    def update_total_cost(self, rental_id, new_total):
        cursor = self.db.get_cursor()
        cursor.execute("UPDATE rentals SET total_cost = ? WHERE id = ?", (new_total, rental_id))
        self.db.commit()


# ===== DAO для рахунків (Invoice) =====

class InvoiceDAO:
    def __init__(self, db: Database):
        self.db = db

    def create_table(self):
        cursor = self.db.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Rentals INTEGER NOT NULL,
                invoice_date DATETIME DEFAULT (datetime('now','localtime')),
                amount REAL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY(Rentals) REFERENCES rentals(id)
            )
        ''')
        self.db.commit()

    def generate_invoice(self, rental_id):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT total_cost FROM rentals WHERE id = ?", (rental_id,))
        row = cursor.fetchone()
        if row:
            amount = row[0]
        else:
            return None, "Оренду не знайдено."
        try:
            cursor.execute("INSERT INTO invoices (Rentals, amount) VALUES (?, ?)", (rental_id, amount))
            invoice_id = cursor.lastrowid
            self.db.commit()
            return invoice_id, "Рахунок створено."
        except Exception as e:
            return None, str(e)


# ===== DAO для платежів =====

class PaymentDAO:
    def __init__(self, db: Database):
        self.db = db

    def create_table(self):
        cursor = self.db.get_cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                rental_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_date DATETIME DEFAULT (datetime('now','localtime')),
                payment_method TEXT,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id),
                FOREIGN KEY(rental_id) REFERENCES rentals(id)
            )
        ''')
        self.db.commit()

    def add_payment(self, invoice_id, rental_id, amount, payment_method):
        cursor = self.db.get_cursor()
        try:
            cursor.execute('''
                INSERT INTO payments (invoice_id, rental_id, amount, payment_method)
                VALUES (?, ?, ?, ?)
            ''', (invoice_id, rental_id, amount, payment_method))
            self.db.commit()
            return True, "Платіж зафіксовано."
        except Exception as e:
            return False, str(e)

    def get_payments(self):
        cursor = self.db.get_cursor()
        cursor.execute("SELECT * FROM payments")
        return cursor.fetchall()


# ===== Головний клас моделі =====

class BikeRentalModel:
    def __init__(self, db_path):
        self.db = Database(db_path)
        self.client_dao = ClientDAO(self.db)
        self.bike_dao = BikeDAO(self.db)
        self.rental_dao = RentalDAO(self.db, self.bike_dao)
        self.invoice_dao = InvoiceDAO(self.db)
        self.payment_dao = PaymentDAO(self.db)
        self.create_tables()

    def create_tables(self):
        self.client_dao.create_table()
        self.bike_dao.create_table()
        self.rental_dao.create_table()
        self.invoice_dao.create_table()
        self.payment_dao.create_table()

    # Методи для роботи з клієнтами
    def add_client(self, name, phone, email, document):
        return self.client_dao.add_client(name, phone, email, document)

    def update_client(self, client_id, name=None, phone=None, email=None, document=None):
        return self.client_dao.update_client(client_id, name, phone, email, document)

    def delete_client(self, client_id):
        return self.client_dao.delete_client(client_id)

    def get_all_clients(self):
        return self.client_dao.get_all()

    def search_clients(self, search_text):
        return self.client_dao.search(search_text)

    def get_client_rental_history(self, client_id):
        return self.rental_dao.get_rental_history_for_client(client_id)

    # Методи для роботи з велосипедами
    def add_bike(self, model, serial_number, bike_type, price_per_hour):
        return self.bike_dao.add_bike(model, serial_number, bike_type, price_per_hour)

    def update_bike(self, bike_id, model=None, serial_number=None, bike_type=None, status=None, price_per_hour=None):
        return self.bike_dao.update_bike(bike_id, model, serial_number, bike_type, status, price_per_hour)

    def delete_bike(self, bike_id):
        return self.bike_dao.delete_bike(bike_id)

    def get_all_bikes(self):
        return self.bike_dao.get_all()

    def get_available_bikes(self):
        return self.bike_dao.get_available()

    def search_bikes(self, search_text, bike_type, status):
        return self.bike_dao.search(search_text, bike_type, status)

    # Методи для роботи з орендою
    def get_income_today(self):
        return self.rental_dao.get_income_today()

    def create_rental(self, client_id, bike_id, start_time_str, duration, discount):
        return self.rental_dao.create_rental(client_id, bike_id, start_time_str, duration, discount)

    def complete_rental(self, rental_id):
        return self.rental_dao.complete_rental(rental_id)

    def extend_rental(self, rental_id, additional_duration):
        return self.rental_dao.extend_rental(rental_id, additional_duration)

    def delete_rental(self, rental_id):
        return self.rental_dao.delete_rental(rental_id)

    def get_active_rentals(self):
        return self.rental_dao.get_active()

    def calculate_rental_price(self, bike_id, duration, discount):
        return self.rental_dao.calculate_rental_price(bike_id, duration, discount)

    def update_rental_total_cost(self, rental_id, new_total):
        return self.rental_dao.update_total_cost(rental_id, new_total)

    # Методи для роботи зі рахунками
    def generate_invoice(self, rental_id):
        return self.invoice_dao.generate_invoice(rental_id)

    # Методи для роботи з платежами
    def add_payment(self, invoice_id, rental_id, amount, payment_method):
        return self.payment_dao.add_payment(invoice_id, rental_id, amount, payment_method)

    def get_payments(self):
        return self.payment_dao.get_payments()

    def generate_report(self, report_type, start_date, end_date, format):
        try:
            import pandas as pd
            from fpdf import FPDF
            import os

            cursor = self.db.get_cursor()
            report_data = []
            columns = []
            mapping = {}  # Маппінг: заголовок звіту -> ім'я ключа у даних

            if report_type == "Оренди за період":
                query = """
                    SELECT r.id, c.name AS client_name, b.model AS bike_model, 
                           r.start_time, r.duration, r.total_cost, r.status
                    FROM rentals r
                    LEFT JOIN clients c ON r.client_id = c.id
                    LEFT JOIN bikes b ON r.bike_id = b.id
                    WHERE DATE(r.start_time) BETWEEN ? AND ?
                    ORDER BY r.start_time ASC
                """
                cursor.execute(query, (start_date, end_date))
                columns = ["ID оренди", "Клієнт", "Велосипед", "Час початку", "Тривалість (год)", "Вартість", "Статус"]
                mapping = {
                    "ID оренди": "id",
                    "Клієнт": "client_name",
                    "Велосипед": "bike_model",
                    "Час початку": "start_time",
                    "Тривалість (год)": "duration",
                    "Вартість": "total_cost",
                    "Статус": "status"
                }
            elif report_type == "Аналіз використання велосипедів":
                query = """
                    SELECT b.model, COUNT(r.id) AS rentals_count, 
                           AVG(r.total_cost) AS avg_cost
                    FROM rentals r
                    LEFT JOIN bikes b ON r.bike_id = b.id
                    WHERE DATE(r.start_time) BETWEEN ? AND ?
                    GROUP BY b.model
                    ORDER BY rentals_count DESC
                """
                cursor.execute(query, (start_date, end_date))
                columns = ["Модель", "Кількість оренд", "Середня вартість"]
                mapping = {
                    "Модель": "model",
                    "Кількість оренд": "rentals_count",
                    "Середня вартість": "avg_cost"
                }
            elif report_type == "Дохід за періодами":
                query = """
                    SELECT DATE(r.end_time) AS rental_date, SUM(r.total_cost) AS total_income
                    FROM rentals r
                    WHERE r.status = 'Завершена' AND DATE(r.end_time) BETWEEN ? AND ?
                    GROUP BY rental_date
                    ORDER BY rental_date ASC
                """
                cursor.execute(query, (start_date, end_date))
                columns = ["Дата", "Дохід"]
                mapping = {
                    "Дата": "rental_date",
                    "Дохід": "total_income"
                }
            elif report_type == "Аналіз клієнтської бази":
                query = """
                    SELECT c.name, COUNT(r.id) AS rentals_count, 
                           COALESCE(SUM(r.total_cost), 0) AS total_spent
                    FROM clients c
                    LEFT JOIN rentals r ON c.id = r.client_id
                    WHERE DATE(r.start_time) BETWEEN ? AND ?
                    GROUP BY c.name
                    ORDER BY total_spent DESC
                """
                cursor.execute(query, (start_date, end_date))
                columns = ["Клієнт", "Кількість оренд", "Загальна сума"]
                mapping = {
                    "Клієнт": "name",
                    "Кількість оренд": "rentals_count",
                    "Загальна сума": "total_spent"
                }
            elif report_type == "Популярність типів велосипедів":
                query = """
                    SELECT b.type, COUNT(r.id) AS rentals_count
                    FROM bikes b
                    LEFT JOIN rentals r ON b.id = r.bike_id
                    WHERE DATE(r.start_time) BETWEEN ? AND ?
                    GROUP BY b.type
                    ORDER BY rentals_count DESC
                """
                cursor.execute(query, (start_date, end_date))
                columns = ["Тип", "Кількість оренд"]
                mapping = {
                    "Тип": "type",
                    "Кількість оренд": "rentals_count"
                }
            else:
                return "Невідомий тип звіту."

            # Збираємо дані звіту
            rows = cursor.fetchall()
            for row in rows:
                report_data.append(dict(row))
            if not report_data:
                return "За вибраний період дані відсутні."

            if format == "Excel":
                df = pd.DataFrame(report_data)
                # Формуємо DataFrame у потрібному порядку
                ordered_data = {col: df[mapping[col]] for col in columns if mapping[col] in df.columns}
                df = pd.DataFrame(ordered_data)
                df.columns = columns
                filename = f"Report_{report_type}_{start_date}_{end_date}.xlsx".replace(" ", "_")
                df.to_excel(filename, index=False)
                return f"Excel-звіт збережено як {filename}"
            elif format == "PDF":
                pdf = FPDF(orientation="L")  # Ландшафтний формат для кращої таблиці
                pdf.add_page()
                # Додаємо шрифт з підтримкою кирилиці
                font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
                pdf.add_font("DejaVu", "", font_path, uni=True)
                pdf.set_font("DejaVu", "", 10)
                # Обчислюємо оптимальну ширину для кожного стовпця на основі заголовків та даних
                max_widths = []
                for header in columns:
                    # Початково беремо ширину заголовка
                    max_width = pdf.get_string_width(header) + 4  # невеликий запас
                    key = mapping[header]
                    for data in report_data:
                        cell_text = str(data.get(key, ""))
                        cell_width = pdf.get_string_width(cell_text) + 4
                        if cell_width > max_width:
                            max_width = cell_width
                    max_widths.append(max_width)
                total_width = sum(max_widths)
                page_width = pdf.w - 2 * pdf.l_margin
                # Якщо сумарна оптимальна ширина перевищує доступну ширину сторінки,
                # масштабувати кожну ширину пропорційно
                if total_width > page_width:
                    scale = page_width / total_width
                    max_widths = [w * scale for w in max_widths]

                # Функція для відтворення рядка таблиці
                def draw_row(row_data, row_height):
                    x_start = pdf.get_x()
                    y_start = pdf.get_y()
                    for i, header in enumerate(columns):
                        key = mapping[header]
                        text = str(row_data.get(key, ""))
                        pdf.multi_cell(max_widths[i], row_height, text, border=1, align='C', split_only=False)
                        x_start += max_widths[i]
                        pdf.set_xy(x_start, y_start)
                    pdf.ln(row_height)

                # Вивід заголовка таблиці
                y_before = pdf.get_y()
                x_before = pdf.get_x()
                for i, header in enumerate(columns):
                    pdf.cell(max_widths[i], 10, header, border=1, align='C')
                pdf.ln()
                # Вивід рядків звіту
                for data in report_data:
                    # Оцінюємо висоту рядка: для кожного стовпця підрахуємо кількість рядків (за умовою переносу)
                    line_heights = []
                    for i, header in enumerate(columns):
                        key = mapping[header]
                        text = str(data.get(key, ""))
                        # Оцінка кількості рядків в клітинці
                        lines = pdf.multi_cell(max_widths[i], 10, text, border=0, split_only=True)
                        line_heights.append(len(lines))
                    max_lines = max(line_heights) if line_heights else 1
                    row_height = 10 * max_lines
                    # Якщо місце на сторінці не достатнє, додаємо нову сторінку та виводимо заголовок знову
                    if pdf.get_y() + row_height > pdf.page_break_trigger:
                        pdf.add_page()
                        for i, header in enumerate(columns):
                            pdf.cell(max_widths[i], 10, header, border=1, align='C')
                        pdf.ln()
                    draw_row(data, row_height)
                filename = f"Report_{report_type}_{start_date}_{end_date}.pdf".replace(" ", "_")
                pdf.output(filename)
                return f"PDF-звіт збережено як {filename}"
            else:
                return "Невідомий формат звіту."
        except Exception as e:
            return "Помилка генерації звіту: " + str(e)












