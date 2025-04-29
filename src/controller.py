import re
import os
import sys
from fpdf import FPDF
from datetime import datetime, timedelta
from math import ceil
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QInputDialog, QDateTimeEdit, QGroupBox, QFormLayout, QMessageBox,
    QHeaderView, QDialog, QDialogButtonBox, QSystemTrayIcon
)
from PyQt5.QtCore import QRegExp, QDateTime, Qt, QTimer
from PyQt5.QtGui import QRegExpValidator, QIcon, QFont
from view import MainWindow, AddClientDialog, EditClientDialog, AddBikeDialog, EditBikeDialog
from model import BikeRentalModel

class BikeRentalController:
    def __init__(self, model: BikeRentalModel, view: MainWindow):
        self.model = model
        self.view = view
        self.overdue_notification_times = {}
        self.alerted_rentals = set()
        self.setup_tray_icon()
        self.setup_connections()
        self.load_initial_data()
        self.setup_overdue_timer()
        self.setup_dashboard_timer()
        self.update_dashboard_stats()

    def setup_tray_icon(self):
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        icon_path = os.path.join(base_path, "rental.ico")
        self.tray_icon = QSystemTrayIcon(self.view)
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setVisible(True)

    def setup_overdue_timer(self):
        """Налаштовує таймер для автоматичної перевірки просрочених оренд кожні 60 секунд."""
        self.overdue_timer = QTimer(self.view)
        self.overdue_timer.timeout.connect(self.check_overdue_rentals)
        self.overdue_timer.start(5000)


    def setup_dashboard_timer(self):
        """Налаштовує таймер для оновлення статистики на головній панелі кожні 60 секунд."""
        self.dashboard_timer = QTimer(self.view)
        self.dashboard_timer.timeout.connect(self.update_dashboard_stats)
        self.dashboard_timer.start(5000)

    def update_dashboard_stats(self):
        available_bikes = len(self.model.get_available_bikes())
        active_rentals = len(self.model.get_active_rentals())
        clients_count = len(self.model.get_all_clients())
        income = self.model.get_income_today()  # Викликаємо метод моделі

        self.view.available_bikes_label.setText(str(available_bikes))
        self.view.active_rentals_label.setText(str(active_rentals))
        self.view.clients_label.setText(str(clients_count))
        self.view.income_label.setText(f"{income:.2f} грн")

    def validate_client_data(self, name, phone, email, document):
        """
        Перевірка даних клієнта.
        ПІБ має містити не менше двох слів та складатися лише з літер, пробілів і дефісів;
        Email і телефон перевіряються за шаблоном, а документ не може бути порожнім.
        """
        name = name.strip()
        if not name:
            return False, "ПІБ не може бути порожнім."
        if not re.match(r"^[А-ЯІЇЄа-яіїєA-Za-z\s\-]+$", name):
            return False, "Невірний формат ПІБ."
        if len(name.split()) < 2:
            return False, "ПІБ має містити щонайменше два слова."
        email = email.strip()
        if email and not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            return False, "Невірний формат email."
        phone = phone.strip()
        if phone and not re.match(r"^\+?\d[\d\s-]{7,}$", phone):
            return False, "Невірний формат номера телефону."
        document = document.strip()
        if not document:
            return False, "Інформація про документ не може бути порожньою."
        if not re.match(r"^[A-Za-zА-ЯІЇЄа-яіїє0-9\s\-]+$", document):
            return False, "Невірний формат інформації про документ."
        return True, ""

    def setup_connections(self):
        """Налаштовує з'єднання між подіями UI та відповідними методами контролера."""
        # Вкладка "Клієнти"
        add_client_btn = self.view.clients_tab.findChild(QPushButton, "add_client_btn")
        if add_client_btn:
            add_client_btn.clicked.connect(self.add_client)
        edit_client_btn = self.view.clients_tab.findChild(QPushButton, "edit_client_btn")
        if edit_client_btn:
            edit_client_btn.clicked.connect(self.edit_client)
        delete_client_btn = self.view.clients_tab.findChild(QPushButton, "delete_client_btn")
        if delete_client_btn:
            delete_client_btn.clicked.connect(self.delete_client)
        history_btn = self.view.clients_tab.findChild(QPushButton, "history_btn")
        if history_btn:
            history_btn.clicked.connect(self.view_client_history)
        search_client_btn = self.view.clients_tab.findChild(QPushButton, "search_client_btn")
        if search_client_btn:
            search_client_btn.clicked.connect(self.search_clients)

        # Пошук клієнтів у вкладці "Оренда"
        client_search = self.view.rentals_tab.findChild(QLineEdit, "client_search")
        if client_search:
            client_search.textChanged.connect(self.search_clients_for_rental)
        client_results = self.view.rentals_tab.findChild(QTableWidget, "client_results")
        if client_results:
            client_results.cellClicked.connect(self.select_client_from_search)

        # Вкладка "Велосипеди"
        add_bike_btn = self.view.bikes_tab.findChild(QPushButton, "add_bike_btn")
        if add_bike_btn:
            add_bike_btn.clicked.connect(self.add_bike)
        edit_bike_btn = self.view.bikes_tab.findChild(QPushButton, "edit_bike_btn")
        if edit_bike_btn:
            edit_bike_btn.clicked.connect(self.edit_bike)
        delete_bike_btn = self.view.bikes_tab.findChild(QPushButton, "delete_bike_btn")
        if delete_bike_btn:
            delete_bike_btn.clicked.connect(self.delete_bike)
        change_status_btn = self.view.bikes_tab.findChild(QPushButton, "change_status_btn")
        if change_status_btn:
            change_status_btn.clicked.connect(self.change_bike_status)
        search_bike_btn = self.view.bikes_tab.findChild(QPushButton, "search_bike_btn")
        if search_bike_btn:
            search_bike_btn.clicked.connect(self.search_bikes)

        # Вкладка "Оренда"
        calculate_btn = self.view.rentals_tab.findChild(QPushButton, "calculate_btn")
        if calculate_btn:
            calculate_btn.clicked.connect(self.calculate_rental_price)
        create_rental_btn = self.view.rentals_tab.findChild(QPushButton, "create_rental_btn")
        if create_rental_btn:
            create_rental_btn.clicked.connect(self.create_rental)
        return_bike_btn = self.view.rentals_tab.findChild(QPushButton, "return_bike_btn")
        if return_bike_btn:
            return_bike_btn.clicked.connect(self.complete_rental)
        extend_rental_btn = self.view.rentals_tab.findChild(QPushButton, "extend_rental_btn")
        if extend_rental_btn:
            extend_rental_btn.clicked.connect(self.extend_rental)

        # Вкладка "Звіти"
        report_btn = self.view.reports_tab.findChild(QPushButton, "report_btn")
        if report_btn:
            report_btn.clicked.connect(self.generate_report)

    def load_initial_data(self):
        """Завантажує дані з моделі та оновлює UI."""
        self.load_bikes_data()
        self.load_clients_data()
        self.load_rentals_data()
        self.update_client_combo()
        self.update_bike_combo()
        self.setup_overdue_timer()
        self.update_dashboard_stats()

    def load_bikes_data(self):
        """Оновлює таблицю велосипедів у вкладці 'Велосипеди'."""
        bikes = self.model.get_all_bikes()
        table = self.view.bikes_tab.findChild(QTableWidget, "bikes_table")
        table.setRowCount(0)
        for bike in bikes:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(bike.id)))
            table.setItem(row, 1, QTableWidgetItem(bike.model))
            table.setItem(row, 2, QTableWidgetItem(bike.serial_number))
            table.setItem(row, 3, QTableWidgetItem(bike.type))
            table.setItem(row, 4, QTableWidgetItem(bike.status))
            table.setItem(row, 5, QTableWidgetItem(str(bike.price_per_hour)))
        table.setColumnHidden(0, True)

    def load_clients_data(self):
        """Оновлює таблицю клієнтів у вкладці 'Клієнти'."""
        clients = self.model.get_all_clients()
        table = self.view.clients_tab.findChild(QTableWidget, "clients_table")
        table.setRowCount(0)
        for client in clients:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            table.setItem(row, 1, QTableWidgetItem(client.name))
            table.setItem(row, 2, QTableWidgetItem(client.phone))
            table.setItem(row, 3, QTableWidgetItem(client.email if client.email else ""))
            table.setItem(row, 4, QTableWidgetItem(client.document))
            table.setItem(row, 5, QTableWidgetItem(client.created_at))
        table.setColumnHidden(0, True)

    def load_rentals_data(self):
        """
        Оновлює таблицю активних оренд у вкладці "Оренда".
         1 - Ім'я клієнта, 2 - Модель велосипеда,
                 3 - Час початку, 4 - Очікуване завершення, 5 - Загальна вартість.
        """
        clients = self.model.get_all_clients()
        client_map = {client.id: client.name for client in clients}
        bikes = self.model.get_all_bikes()
        bike_map = {bike.id: bike.model for bike in bikes}
        rentals = self.model.get_active_rentals()
        table = self.view.rentals_tab.findChild(QTableWidget, "active_table")
        table.setRowCount(0)
        for rental in rentals:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(rental.id)))
            table.setItem(row, 1, QTableWidgetItem(client_map.get(rental.client_id, "Невідомо")))
            table.setItem(row, 2, QTableWidgetItem(bike_map.get(rental.bike_id, "Невідомо")))
            table.setItem(row, 3, QTableWidgetItem(rental.start_time))
            if rental.end_time is None:
                start_dt = QDateTime.fromString(rental.start_time, "yyyy-MM-dd HH:mm:ss")
                if not start_dt.isValid():
                    expected_end_str = "Невідомо"
                else:
                    expected_end = start_dt.addSecs(rental.duration * 3600)
                    expected_end_str = expected_end.toString("yyyy-MM-dd HH:mm:ss")
            else:
                expected_end_str = rental.end_time
            table.setItem(row, 4, QTableWidgetItem(expected_end_str))
            table.setItem(row, 5, QTableWidgetItem(str(rental.total_cost)))
        table.setColumnHidden(0, True)

    def update_client_combo(self):
        """Оновлює прихований ComboBox для збереження вибраного ID клієнта."""
        combo = self.view.rentals_tab.findChild(QComboBox, "client_combo")
        if combo:
            combo.clear()
            combo.addItem("Виберіть клієнта...", None)
            clients = self.model.get_all_clients()
            for client in clients:
                combo.addItem(f"{client.name} ({client.phone})", client.id)

    def update_bike_combo(self):
        """Оновлює ComboBox для вибору доступного велосипеда у вкладці 'Оренда'."""
        combo = self.view.rentals_tab.findChild(QComboBox, "bike_combo")
        if combo:
            combo.clear()
            combo.addItem("Виберіть велосипед...", None)
            bikes = self.model.get_available_bikes()
            for bike in bikes:
                combo.addItem(f"{bike.model} ({bike.serial_number}, {bike.type}) - {bike.price_per_hour} грн/год",
                              bike.id)

    # --- Методи роботи з клієнтами ---
    def add_client(self):
        dialog = AddClientDialog(self.view)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            valid, message = self.validate_client_data(data["name"], data["phone"], data["email"], data["document"])
            if not valid:
                QMessageBox.warning(self.view, "Помилка", message)
                return
            if self.model.add_client(data["name"], data["phone"], data["email"], data["document"]):
                QMessageBox.information(self.view, "Успіх", "Клієнта додано успішно!")
                self.load_clients_data()
                self.update_client_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", "Не вдалося додати клієнта.")

    def edit_client(self):
        table = self.view.clients_tab.findChild(QTableWidget, "clients_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть клієнта для редагування.")
            return
        client_id = int(table.item(row, 0).text())
        client_data = {
            "name": table.item(row, 1).text(),
            "phone": table.item(row, 2).text(),
            "email": table.item(row, 3).text(),
            "document": table.item(row, 4).text()
        }
        dialog = EditClientDialog(client_data, self.view)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            valid, message = self.validate_client_data(data["name"], data["phone"], data["email"], data["document"])
            if not valid:
                QMessageBox.warning(self.view, "Помилка", message)
                return
            if self.model.update_client(client_id, data["name"], data["phone"], data["email"], data["document"]):
                QMessageBox.information(self.view, "Успіх", "Інформацію про клієнта оновлено!")
                self.load_clients_data()
                self.update_client_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", "Не вдалося оновити інформацію про клієнта.")

    def delete_client(self):
        table = self.view.clients_tab.findChild(QTableWidget, "clients_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть клієнта для видалення.")
            return
        client_id = int(table.item(row, 0).text())
        reply = QMessageBox.question(self.view, "Підтвердження",
                                     "Ви впевнені, що хочете видалити цього клієнта?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            result, msg = self.model.delete_client(client_id)
            if result:
                QMessageBox.information(self.view, "Успіх", msg)
                self.load_clients_data()
                self.update_client_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", msg)

    def view_client_history(self):
        table = self.view.clients_tab.findChild(QTableWidget, "clients_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть клієнта для перегляду історії оренд.")
            return
        client_id = int(table.item(row, 0).text())
        client_name = table.item(row, 1).text()
        try:
            rentals = self.model.get_client_rental_history(client_id)
            if not rentals:
                QMessageBox.information(self.view, "Історія оренд", "Для вибраного клієнта історія оренд відсутня.")
                return
            from view import RentalHistoryDialog
            dialog = RentalHistoryDialog(client_name, rentals, self.view)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self.view, "Помилка", f"Сталася помилка: {str(e)}")

    # --- Методи роботи з велосипедами ---
    def add_bike(self):
        dialog = AddBikeDialog(self.view)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["model"].strip():
                QMessageBox.warning(self.view, "Помилка", "Модель не може бути порожньою.")
                return
            if not data["serial_number"].strip():
                QMessageBox.warning(self.view, "Помилка", "Серійний номер не може бути порожньою.")
                return
            bikes = self.model.get_all_bikes()
            for bike in bikes:
                if bike.serial_number == data["serial_number"]:
                    QMessageBox.warning(self.view, "Помилка", "Велосипед з таким серійним номером вже існує.")
                    return
            if self.model.add_bike(data["model"], data["serial_number"], data["type"], data["price_per_hour"]):
                QMessageBox.information(self.view, "Успіх", "Велосипед додано успішно!")
                self.load_bikes_data()
                self.update_bike_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", "Не вдалося додати велосипед.")

    def edit_bike(self):
        table = self.view.bikes_tab.findChild(QTableWidget, "bikes_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть велосипед для редагування.")
            return
        current_status = table.item(row, 4).text()
        if current_status != "Доступний":
            QMessageBox.warning(self.view, "Увага", "Редагування неможливе, велосипед знаходиться у оренді.")
            return
        bike_id = int(table.item(row, 0).text())
        bike_data = {
            "model": table.item(row, 1).text(),
            "serial_number": table.item(row, 2).text(),
            "type": table.item(row, 3).text(),
            "price_per_hour": float(table.item(row, 5).text())
        }
        dialog = EditBikeDialog(bike_data, self.view)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["model"].strip():
                QMessageBox.warning(self.view, "Помилка", "Модель не може бути порожньою.")
                return
            if not data["serial_number"].strip():
                QMessageBox.warning(self.view, "Помилка", "Серійний номер не може бути порожньою.")
                return
            bikes = self.model.get_all_bikes()
            for bike in bikes:
                if bike.id != bike_id and bike.serial_number == data["serial_number"]:
                    QMessageBox.warning(self.view, "Помилка", "Велосипед з таким серійним номером вже існує.")
                    return
            if self.model.update_bike(bike_id, model=data["model"], serial_number=data["serial_number"],
                                      bike_type=data["type"], price_per_hour=data["price_per_hour"]):
                QMessageBox.information(self.view, "Успіх", "Велосипед оновлено!")
                self.load_bikes_data()
                self.update_bike_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", "Не вдалося оновити інформацію про велосипед.")

    def delete_bike(self):
        table = self.view.bikes_tab.findChild(QTableWidget, "bikes_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть велосипед для видалення.")
            return
        current_status = table.item(row, 4).text()
        if current_status != "Доступний":
            QMessageBox.warning(self.view, "Увага", "Видалення неможливе, велосипед знаходиться у оренді.")
            return
        bike_id = int(table.item(row, 0).text())
        reply = QMessageBox.question(self.view, "Підтвердження",
                                     "Ви впевнені, що хочете видалити цей велосипед?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            result, msg = self.model.delete_bike(bike_id)
            if result:
                QMessageBox.information(self.view, "Успіх", msg)
                self.load_bikes_data()
                self.update_bike_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", msg)

    def change_bike_status(self):
        table = self.view.bikes_tab.findChild(QTableWidget, "bikes_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть велосипед для зміни статусу.")
            return
        bike_id = int(table.item(row, 0).text())
        current_status = table.item(row, 4).text()
        statuses = ["Доступний", "В оренді", "Ремонт"]
        current_index = statuses.index(current_status) if current_status in statuses else 0
        new_status, ok = QInputDialog.getItem(self.view, "Зміна статусу", "Новий статус:", statuses, current_index,
                                              False)
        if ok and new_status != current_status:
            if self.model.update_bike(bike_id, status=new_status):
                QMessageBox.information(self.view, "Успіх", f"Статус змінено на {new_status}.")
                self.load_bikes_data()
                self.update_bike_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", "Не вдалося змінити статус.")

    # --- Методи роботи з орендою ---
    def calculate_rental_price(self):
        rental_tab = self.view.rentals_tab
        bike_combo = rental_tab.findChild(QComboBox, "bike_combo")
        duration_spin = rental_tab.findChild(QSpinBox, "duration_spin")
        discount_spin = rental_tab.findChild(QDoubleSpinBox, "discount_spin")
        price_field = rental_tab.findChild(QLineEdit, "price_field")
        bike_id = bike_combo.currentData()
        duration = duration_spin.value()
        discount = discount_spin.value()
        if bike_id is not None:
            price = self.model.calculate_rental_price(bike_id, duration, discount)
            if price is not None:
                price_field.setText(f"{price:.2f} грн")
            else:
                price_field.setText("0.00 грн")
        else:
            price_field.setText("0.00 грн")

    def create_rental(self):
        rental_tab = self.view.rentals_tab
        client_combo = rental_tab.findChild(QComboBox, "client_combo")
        bike_combo = rental_tab.findChild(QComboBox, "bike_combo")
        start_time = rental_tab.findChild(QDateTimeEdit, "start_time")
        duration_spin = rental_tab.findChild(QSpinBox, "duration_spin")
        discount_spin = rental_tab.findChild(QDoubleSpinBox, "discount_spin")
        price_field = rental_tab.findChild(QLineEdit, "price_field")

        client_id = client_combo.currentData()
        bike_id = bike_combo.currentData()

        if client_id is None:
            QMessageBox.warning(self.view, "Увага", "Виберіть клієнта.")
            return
        if bike_id is None:
            QMessageBox.warning(self.view, "Увага", "Виберіть велосипед.")
            return
        if price_field.text().startswith("0.00"):
            QMessageBox.warning(self.view, "Увага", "Спочатку розрахуйте вартість оренди!")
            return

        start_time_str = start_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        duration = duration_spin.value()
        discount = discount_spin.value()

        total_cost = self.model.calculate_rental_price(bike_id, duration, discount)

        # Спочатку вибір способу оплати
        payment_methods = ["Карткою", "Готівкою"]
        payment_method, ok = QInputDialog.getItem(self.view, "Оплата",
                                                  "Оберіть спосіб оплати:", payment_methods, 0, False)
        if not ok or not payment_method.strip():
            QMessageBox.warning(self.view, "Увага", "Оплату скасовано. Оренда не проведена.")
            return

        # Створення оренди
        rental_id, msg = self.model.create_rental(client_id, bike_id, start_time_str, duration, discount)
        if not rental_id:
            QMessageBox.warning(self.view, "Помилка", msg)
            return

        # Створення рахунку
        invoice_id, invoice_msg = self.model.generate_invoice(rental_id)
        if not invoice_id:
            QMessageBox.warning(self.view, "Помилка", "Рахунок не створено: " + invoice_msg)
            return

        # Проведення платежу
        pay_result, pay_msg = self.model.add_payment(invoice_id, rental_id, total_cost, payment_method.strip())
        if not pay_result:
            QMessageBox.warning(self.view, "Помилка", "Не вдалося провести оплату: " + pay_msg)
            return

        self.model.update_bike(bike_id, status="В оренді")
        QMessageBox.information(self.view, "Успіх", "Оплата проведена. " + msg)
        self.load_rentals_data()
        self.load_bikes_data()
        self.update_bike_combo()
        client_search = rental_tab.findChild(QLineEdit, "client_search")
        if client_search:
            client_search.clear()

    def complete_rental(self):
        table = self.view.rentals_tab.findChild(QTableWidget, "active_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть оренду для завершення.")
            return
        item = table.item(row, 0)
        if item is None:
            QMessageBox.warning(self.view, "Увага", "Не вдалося отримати ID оренди.")
            return
        try:
            rental_id = int(item.text())
        except Exception as e:
            QMessageBox.warning(self.view, "Увага", f"Невірний формат ID: {str(e)}")
            return
        rentals = self.model.get_active_rentals()
        rental = next((r for r in rentals if r.id == rental_id), None)
        if rental is None:
            QMessageBox.warning(self.view, "Увага", "Оренду не знайдено.")
            return
        start_dt = QDateTime.fromString(rental.start_time, "yyyy-MM-dd HH:mm:ss")
        if not start_dt.isValid():
            QMessageBox.warning(self.view, "Помилка", "Невірний формат часу початку оренди.")
            return
        expected_end = start_dt.addSecs(rental.duration * 3600)
        now = QDateTime.currentDateTime()
        if now > expected_end:
            overdue_seconds = now.toSecsSinceEpoch() - expected_end.toSecsSinceEpoch()
            penalty_hours = ceil(overdue_seconds / 3600)
            price_per_hour = self.model.calculate_rental_price(rental.bike_id, 1, 0)
            penalty_fee = penalty_hours * price_per_hour * 1.5  # коефіцієнт штрафу 1.5
            new_total = rental.total_cost + penalty_fee
            # Оновлюємо суму оренди в БД
            if hasattr(self.model, "update_rental_total_cost"):
                self.model.update_rental_total_cost(rental.id, new_total)
        reply = QMessageBox.question(self.view, "Підтвердження", "Ви впевнені, що хочете завершити оренду?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            result, msg = self.model.complete_rental(rental_id)
            if result:
                if rental:
                    self.model.update_bike(rental.bike_id, status="Доступний")
                QMessageBox.information(self.view, "Успіх", msg)
                self.load_rentals_data()
                self.load_bikes_data()
                self.update_bike_combo()
                self.update_dashboard_stats()
            else:
                QMessageBox.warning(self.view, "Помилка", msg)

    def extend_rental(self):
        table = self.view.rentals_tab.findChild(QTableWidget, "active_table")
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self.view, "Увага", "Виберіть оренду для продовження.")
            return
        try:
            rental_id = int(table.item(row, 0).text())
        except Exception as e:
            QMessageBox.warning(self.view, "Увага", f"Невірний формат ID: {str(e)}")
            return
        additional_duration, ok = QInputDialog.getInt(self.view, "Продовження оренди", "Додаткова тривалість (год):", 1,
                                                      1, 72, 1)
        if ok:
            result, msg = self.model.extend_rental(rental_id, additional_duration)
            if result:
                QMessageBox.information(self.view, "Успіх", msg)
                self.load_rentals_data()
                self.load_bikes_data()
                self.update_bike_combo()
            else:
                QMessageBox.warning(self.view, "Помилка", msg)

    def generate_report(self):
        report_tab = self.view.reports_tab
        report_type = report_tab.findChild(QComboBox, "report_type_combo").currentText()
        start_date = report_tab.findChild(QDateTimeEdit, "start_date").dateTime().toString("yyyy-MM-dd")
        end_date = report_tab.findChild(QDateTimeEdit, "end_date").dateTime().toString("yyyy-MM-dd")
        report_format = report_tab.findChild(QComboBox, "format_combo").currentText()  # "Excel" або "PDF"
        result = self.model.generate_report(report_type, start_date, end_date, report_format)
        QMessageBox.information(self.view, "Звіт", result)

    # --- Методи пошуку ---
    def search_bikes(self):
        bike_tab = self.view.bikes_tab
        search_input = bike_tab.findChild(QLineEdit, "search_input")
        type_combo = bike_tab.findChild(QComboBox, "type_combo")
        status_combo = bike_tab.findChild(QComboBox, "status_combo")
        search_text = search_input.text()
        bike_type = type_combo.currentText()
        status = status_combo.currentText()
        bikes = self.model.search_bikes(search_text, bike_type, status)
        table = bike_tab.findChild(QTableWidget, "bikes_table")
        table.setRowCount(0)
        for bike in bikes:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(bike.id)))
            table.setItem(row, 1, QTableWidgetItem(bike.model))
            table.setItem(row, 2, QTableWidgetItem(bike.serial_number))
            table.setItem(row, 3, QTableWidgetItem(bike.type))
            table.setItem(row, 4, QTableWidgetItem(bike.status))
            table.setItem(row, 5, QTableWidgetItem(str(bike.price_per_hour)))
        table.setColumnHidden(0, True)

    def search_clients(self):
        client_tab = self.view.clients_tab
        search_input = client_tab.findChild(QLineEdit, "search_input")
        search_text = search_input.text()
        clients = self.model.search_clients(search_text)
        table = client_tab.findChild(QTableWidget, "clients_table")
        table.setRowCount(0)
        for client in clients:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            table.setItem(row, 1, QTableWidgetItem(client.name))
            table.setItem(row, 2, QTableWidgetItem(client.phone))
            table.setItem(row, 3, QTableWidgetItem(client.email if client.email else ""))
            table.setItem(row, 4, QTableWidgetItem(client.document))
            table.setItem(row, 5, QTableWidgetItem(client.created_at))
        table.setColumnHidden(0, True)

    def search_clients_for_rental(self):
        client_search = self.view.rentals_tab.findChild(QLineEdit, "client_search")
        client_results = self.view.rentals_tab.findChild(QTableWidget, "client_results")
        search_text = client_search.text().strip()
        if len(search_text) < 2:
            client_results.setVisible(False)
            return
        clients = self.model.search_clients(search_text)
        client_results.setRowCount(0)
        for client in clients:
            row = client_results.rowCount()
            client_results.insertRow(row)
            client_results.setItem(row, 0, QTableWidgetItem(str(client.id)))
            client_results.setItem(row, 1, QTableWidgetItem(client.name))
            client_results.setItem(row, 2, QTableWidgetItem(client.phone))
        client_results.setVisible(client_results.rowCount() > 0)

    def select_client_from_search(self, row, column):
        client_results = self.view.rentals_tab.findChild(QTableWidget, "client_results")
        client_search = self.view.rentals_tab.findChild(QLineEdit, "client_search")
        client_combo = self.view.rentals_tab.findChild(QComboBox, "client_combo")
        client_id = int(client_results.item(row, 0).text())
        client_name = client_results.item(row, 1).text()
        client_search.setText(client_name)
        client_combo.clear()
        client_combo.addItem(client_name, client_id)
        client_combo.setCurrentIndex(0)
        client_results.setVisible(False)

    def setup_overdue_timer(self):
        """Налаштовує таймер для перевірки прострочених оренд кожні 60 секунд."""
        self.overdue_timer = QTimer(self.view)
        self.overdue_timer.timeout.connect(self.check_overdue_rentals)
        self.overdue_timer.start(5000)
        self.overdue_notification_times = {}
        self.finished_notifications = {}  # Для повідомлень про завершення оренди
        self.notified_intervals = {}  # Для відстеження кількості повідомлених 30-хвилинних інтервалів

    def check_overdue_rentals(self):
        """
        Перевіряє активні оренди.
        Якщо оренда закінчилася (в межах 5 хвилин після expected_end) – надсилається повідомлення,
        що час оренди завершився (однократно).
        Якщо оренда прострочена (понад 5 хвилин після expected_end), штраф нараховується за кожні
        повні 30 хвилин прострочки, і якщо кількість таких інтервалів зросла, надсилається повідомлення.
        """
        now = QDateTime.currentDateTime()
        clients = self.model.get_all_clients()
        client_map = {client.id: client.name for client in clients}
        bikes = self.model.get_all_bikes()
        bike_map = {bike.id: bike.model for bike in bikes}
        active_rentals = self.model.get_active_rentals()

        for rental in active_rentals:
            start_dt = QDateTime.fromString(rental.start_time, "yyyy-MM-dd HH:mm:ss")
            if not start_dt.isValid():
                continue
            expected_end = start_dt.addSecs(rental.duration * 3600)

            # Якщо оренда щойно завершилася (менше 5 хвилин прострочки)
            if expected_end <= now and now.toSecsSinceEpoch() - expected_end.toSecsSinceEpoch() < 300:
                if not self.finished_notifications.get(rental.id, False):
                    msg = (
                        f"{client_map.get(rental.client_id, 'Невідомо')} - {bike_map.get(rental.bike_id, 'Невідомо')}: "
                        "час оренди завершився. Будь ласка, завершіть оренду.")
                    self.tray_icon.showMessage("Час оренди завершено", msg, QSystemTrayIcon.Information, 5000)
                    self.finished_notifications[rental.id] = True
                continue

            # Якщо оренда прострочена більше 5 хвилин
            if now > expected_end:
                overdue_seconds = now.toSecsSinceEpoch() - expected_end.toSecsSinceEpoch()
                penalty_intervals = int(overdue_seconds // 1800)
                if penalty_intervals == 0:
                    continue
                # далі – розрахунок штрафу
                price_per_hour = self.model.calculate_rental_price(rental.bike_id, 1, 0)
                interval_penalty = price_per_hour * 1.2
                full_penalty = penalty_intervals * interval_penalty
                prev_intervals = self.notified_intervals.get(rental.id, 0)
                additional_intervals = penalty_intervals - prev_intervals
                if additional_intervals > 0:

                    additional_penalty = additional_intervals * interval_penalty
                    new_total = rental.total_cost + additional_penalty
                    if hasattr(self.model, "update_rental_total_cost"):
                        self.model.update_rental_total_cost(rental.id, new_total)
                    rental.total_cost = new_total
                    self.notified_intervals[rental.id] = penalty_intervals
                    msg = (
                        f"{client_map.get(rental.client_id, 'Невідомо')} - {bike_map.get(rental.bike_id, 'Невідомо')}: "
                        f"прострочено на {penalty_intervals * 0.5:.1f} год, штраф: {full_penalty:.2f} грн.")
                    self.tray_icon.showMessage("Просрочені оренди", msg, QSystemTrayIcon.Information, 5000)
                    self.overdue_notification_times[rental.id] = now.toSecsSinceEpoch()
                    self.load_rentals_data()


    def generate_report(self):
        report_tab = self.view.reports_tab
        report_type = report_tab.findChild(QComboBox, "report_type_combo").currentText()
        start_date = report_tab.findChild(QDateTimeEdit, "start_date").dateTime().toString("yyyy-MM-dd")
        end_date = report_tab.findChild(QDateTimeEdit, "end_date").dateTime().toString("yyyy-MM-dd")
        report_format = report_tab.findChild(QComboBox, "format_combo").currentText()
        report = self.model.generate_report(report_type, start_date, end_date, report_format)
        QMessageBox.information(self.view, "Звіт", report)

    # --- Методи пошуку ---
    def search_bikes(self):
        bike_tab = self.view.bikes_tab
        search_input = bike_tab.findChild(QLineEdit, "search_input")
        type_combo = bike_tab.findChild(QComboBox, "type_combo")
        status_combo = bike_tab.findChild(QComboBox, "status_combo")
        search_text = search_input.text()
        bike_type = type_combo.currentText()
        status = status_combo.currentText()
        bikes = self.model.search_bikes(search_text, bike_type, status)
        table = bike_tab.findChild(QTableWidget, "bikes_table")
        table.setRowCount(0)
        for bike in bikes:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(bike.id)))
            table.setItem(row, 1, QTableWidgetItem(bike.model))
            table.setItem(row, 2, QTableWidgetItem(bike.serial_number))
            table.setItem(row, 3, QTableWidgetItem(bike.type))
            table.setItem(row, 4, QTableWidgetItem(bike.status))
            table.setItem(row, 5, QTableWidgetItem(str(bike.price_per_hour)))
        table.setColumnHidden(0, True)

    def search_clients(self):
        client_tab = self.view.clients_tab
        search_input = client_tab.findChild(QLineEdit, "search_input")
        search_text = search_input.text()
        clients = self.model.search_clients(search_text)
        table = client_tab.findChild(QTableWidget, "clients_table")
        table.setRowCount(0)
        for client in clients:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            table.setItem(row, 1, QTableWidgetItem(client.name))
            table.setItem(row, 2, QTableWidgetItem(client.phone))
            table.setItem(row, 3, QTableWidgetItem(client.email if client.email else ""))
            table.setItem(row, 4, QTableWidgetItem(client.document))
            table.setItem(row, 5, QTableWidgetItem(client.created_at))
        table.setColumnHidden(0, True)

    def search_clients_for_rental(self):
        client_search = self.view.rentals_tab.findChild(QLineEdit, "client_search")
        client_results = self.view.rentals_tab.findChild(QTableWidget, "client_results")
        search_text = client_search.text().strip()
        if len(search_text) < 2:
            client_results.setVisible(False)
            return
        clients = self.model.search_clients(search_text)
        client_results.setRowCount(0)
        for client in clients:
            row = client_results.rowCount()
            client_results.insertRow(row)
            client_results.setItem(row, 0, QTableWidgetItem(str(client.id)))
            client_results.setItem(row, 1, QTableWidgetItem(client.name))
            client_results.setItem(row, 2, QTableWidgetItem(client.phone))
        client_results.setVisible(client_results.rowCount() > 0)

    def select_client_from_search(self, row, column):
        client_results = self.view.rentals_tab.findChild(QTableWidget, "client_results")
        client_search = self.view.rentals_tab.findChild(QLineEdit, "client_search")
        client_combo = self.view.rentals_tab.findChild(QComboBox, "client_combo")
        client_id = int(client_results.item(row, 0).text())
        client_name = client_results.item(row, 1).text()
        client_search.setText(client_name)
        client_combo.clear()
        client_combo.addItem(client_name, client_id)
        client_combo.setCurrentIndex(0)
        client_results.setVisible(False)
