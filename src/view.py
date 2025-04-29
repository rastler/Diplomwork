import sys
import os
from PyQt5.QtCore import QRegExp, QDateTime, Qt, QTimer
from PyQt5.QtGui import QRegExpValidator, QIcon, QFont
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QSpinBox,
    QDoubleSpinBox, QDateTimeEdit, QGroupBox, QFormLayout, QMessageBox,
    QHeaderView, QDialog, QDialogButtonBox, QInputDialog,
)
def get_icon_path(icon_name):
    # Если приложение запущено из exe, sys._MEIPASS содержит путь к временной директории PyInstaller
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, icon_name)

class RentalHistoryDialog(QDialog):
    def __init__(self, client_name, rentals, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Історія оренд клієнта: {client_name}")
        self.resize(700, 400)
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 7, self)
        self.table.setHorizontalHeaderLabels([
            "ID оренди", "Модель велосипеда", "Час початку",
            "Тривалість (год)", "Час завершення", "Вартість", "Статус"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Кнопка закриття діалогу
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.populate_table(rentals)

    def populate_table(self, rentals):
        self.table.setRowCount(0)
        for rental in rentals:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # Перетворення всіх значень у рядки для уникнення проблем з None
            self.table.setItem(row, 0, QTableWidgetItem(str(rental.id)))
            # Припускаємо, що в об'єкті оренди є атрибут bike_model (або замініть на відповідне поле)
            bike_model = getattr(rental, "bike_model", "Невідомо")
            self.table.setItem(row, 1, QTableWidgetItem(str(bike_model)))
            self.table.setItem(row, 2, QTableWidgetItem(str(rental.start_time)))
            self.table.setItem(row, 3, QTableWidgetItem(str(rental.duration)))
            # Якщо поле end_time має значення None, відображаємо "В процесі"
            end_time = str(rental.end_time) if rental.end_time is not None else "В процесі"
            self.table.setItem(row, 4, QTableWidgetItem(end_time))
            self.table.setItem(row, 5, QTableWidgetItem(str(rental.total_cost)))
            self.table.setItem(row, 6, QTableWidgetItem(str(rental.status)))

# Диалог для додавання клієнта
class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додавання клієнта")
        self.resize(300, 180)

        layout = QFormLayout(self)

        self.name_input = QLineEdit(self)
        self.phone_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.document_input = QLineEdit(self)

        # Встановлення валідаторів
        self.name_input.setPlaceholderText("Введіть ПІБ")
        email_regex = QRegExp(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        email_validator = QRegExpValidator(email_regex, self)
        self.email_input.setValidator(email_validator)
        self.email_input.setPlaceholderText("example@domain.com")
        phone_regex = QRegExp(r"^\+?[\d\s-]{8,}$")
        phone_validator = QRegExpValidator(phone_regex, self)
        self.phone_input.setValidator(phone_validator)
        self.phone_input.setPlaceholderText("+380XXXXXXXXX")
        doc_regex = QRegExp(r".+\S")
        doc_validator = QRegExpValidator(doc_regex, self)
        self.document_input.setValidator(doc_validator)
        self.document_input.setPlaceholderText("Номер документа")

        layout.addRow("ПІБ:", self.name_input)
        layout.addRow("Телефон:", self.phone_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Документ:", self.document_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "document": self.document_input.text().strip()
        }

# Диалог для редагування клієнта (на основі AddClientDialog)
class EditClientDialog(AddClientDialog):
    def __init__(self, client_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редагування клієнта")
        self.name_input.setText(client_data.get("name", ""))
        self.phone_input.setText(client_data.get("phone", ""))
        self.email_input.setText(client_data.get("email", ""))
        self.document_input.setText(client_data.get("document", ""))

# Диалог для додавання велосипеда
class AddBikeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додавання велосипеду")
        self.resize(300, 200)

        layout = QFormLayout(self)

        self.model_input = QLineEdit(self)
        self.serial_input = QLineEdit(self)
        self.type_combo = QComboBox(self)
        self.type_combo.addItems(["Гірський", "Міський", "Шосейний", "Дитячий", "Електричний"])
        self.price_input = QDoubleSpinBox(self)
        self.price_input.setRange(10.0, 1000.0)
        self.price_input.setDecimals(2)
        self.price_input.setValue(100.0)

        layout.addRow("Модель:", self.model_input)
        layout.addRow("Серійний номер:", self.serial_input)
        layout.addRow("Тип:", self.type_combo)
        layout.addRow("Ціна/год:", self.price_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addRow(self.buttons)


    def get_data(self):
        return {
            "model": self.model_input.text().strip(),
            "serial_number": self.serial_input.text().strip(),
            "type": self.type_combo.currentText(),
            "price_per_hour": self.price_input.value()
        }

# Диалог для редагування велосипеда (на основі AddBikeDialog)
class EditBikeDialog(AddBikeDialog):
    def __init__(self, bike_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редагування велосипеду")
        self.model_input.setText(bike_data.get("model", ""))
        self.serial_input.setText(bike_data.get("serial_number", ""))
        index = self.type_combo.findText(bike_data.get("type", ""), Qt.MatchFixedString)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        self.price_input.setValue(bike_data.get("price_per_hour", 100.0))

# Основне вікно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система управління орендою велосипедів")
        self.setGeometry(100, 100, 1000, 600)

        # Встановлення іконки додатку
        self.setWindowIcon(QIcon(get_icon_path('rental.ico')))

        # Створення вкладок
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Створення вкладок для різних розділів програми
        self.dashboard_tab = self.create_dashboard_tab()
        self.bikes_tab = self.create_bikes_tab()
        self.clients_tab = self.create_clients_tab()
        self.rentals_tab = self.create_rentals_tab()
        self.reports_tab = self.create_reports_tab()

        # Додавання вкладок до головного віджета
        self.tabs.addTab(self.dashboard_tab, "Головна")
        self.tabs.addTab(self.bikes_tab, "Велосипеди")
        self.tabs.addTab(self.clients_tab, "Клієнти")
        self.tabs.addTab(self.rentals_tab, "Оренда")
        self.tabs.addTab(self.reports_tab, "Звіти")

        # Створення меню
        self.create_menu()

        # Встановлення стилю
        self.set_styles()

    def set_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 6px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom-color: #ffffff;
            }
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                selection-background-color: #a8d8ea;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #c0c0c0;
                font-weight: bold;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)

    def create_menu(self):
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("Допомога")
        about_action = help_menu.addAction("Про програму")
        about_action.triggered.connect(self.show_about_dialog)

    def show_about_dialog(self):
        QMessageBox.about(self, "Про програму",
                          "Система управління орендою велосипедів\n"
                          "Версія 1.0\n\n"
                          "Дипломний проект")

    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        header_label = QLabel("Панель управління")
        header_label.setAlignment(Qt.AlignCenter)
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        stats_group = QGroupBox("Статистика")
        stats_layout = QHBoxLayout()

        # Створюємо мітки для статистики та зберігаємо їх як атрибути головного вікна
        self.available_bikes_label = QLabel("0")
        self.active_rentals_label = QLabel("0")
        self.clients_label = QLabel("0")
        self.income_label = QLabel("0 грн")

        for title, value_label in [("Велосипедів у наявності", self.available_bikes_label),
                                   ("Активних оренд", self.active_rentals_label),
                                   ("Клієнтів", self.clients_label),
                                   ("Дохід за сьогодні", self.income_label)]:
            box = QGroupBox()
            box_layout = QVBoxLayout()
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_label.setFont(title_font)
            value_font = QFont()
            value_font.setPointSize(24)
            value_label.setFont(value_font)
            value_label.setAlignment(Qt.AlignCenter)
            box_layout.addWidget(title_label)
            box_layout.addWidget(value_label)
            box.setLayout(box_layout)
            stats_layout.addWidget(box)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        recent_group = QGroupBox("Останні оренди")
        recent_layout = QVBoxLayout()
        recent_table = QTableWidget(0, 4)
        recent_table.setObjectName("recent_table")
        recent_table.setHorizontalHeaderLabels(["Клієнт", "Велосипед", "Початок", "Статус"])
        recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        recent_table.verticalHeader().setVisible(False)
        recent_layout.addWidget(recent_table)
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)

        tab.setLayout(layout)
        return tab

    def create_bikes_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        toolbar_layout = QHBoxLayout()
        search_label = QLabel("Пошук:")
        search_input = QLineEdit()
        search_input.setObjectName("search_input")
        search_input.setPlaceholderText("Введіть модель або серійний номер...")
        type_label = QLabel("Тип:")
        type_combo = QComboBox()
        type_combo.setObjectName("type_combo")
        type_combo.addItems(["Всі типи", "Гірський", "Міський", "Шосейний", "Дитячий", "Електричний"])
        status_label = QLabel("Статус:")
        status_combo = QComboBox()
        status_combo.setObjectName("status_combo")
        status_combo.addItems(["Всі статуси", "Доступний", "В оренді", "Ремонт"])
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(search_input)
        toolbar_layout.addWidget(type_label)
        toolbar_layout.addWidget(type_combo)
        toolbar_layout.addWidget(status_label)
        toolbar_layout.addWidget(status_combo)
        toolbar_layout.addStretch()
        add_bike_btn = QPushButton("Додати велосипед")
        add_bike_btn.setObjectName("add_bike_btn")
        search_bike_btn = QPushButton("Пошук")
        search_bike_btn.setObjectName("search_bike_btn")
        toolbar_layout.addWidget(add_bike_btn)
        toolbar_layout.addWidget(search_bike_btn)
        layout.addLayout(toolbar_layout)

        bikes_table = QTableWidget(0, 6)
        bikes_table.setObjectName("bikes_table")
        bikes_table.setHorizontalHeaderLabels(["ID", "Модель", "Серійний номер", "Тип", "Статус", "Ціна/год"])
        bikes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        bikes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        bikes_table.setColumnHidden(0, True)
        bikes_table.verticalHeader().setVisible(False)
        layout.addWidget(bikes_table)

        button_layout = QHBoxLayout()
        edit_bike_btn = QPushButton("Редагувати")
        edit_bike_btn.setObjectName("edit_bike_btn")
        delete_bike_btn = QPushButton("Видалити")
        delete_bike_btn.setObjectName("delete_bike_btn")
        change_status_btn = QPushButton("Змінити статус")
        change_status_btn.setObjectName("change_status_btn")
        button_layout.addStretch()
        button_layout.addWidget(edit_bike_btn)
        button_layout.addWidget(delete_bike_btn)
        button_layout.addWidget(change_status_btn)
        layout.addLayout(button_layout)

        tab.setLayout(layout)
        return tab

    def create_clients_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        toolbar_layout = QHBoxLayout()
        search_label = QLabel("Пошук:")
        search_input = QLineEdit()
        search_input.setObjectName("search_input")
        search_input.setPlaceholderText("Введіть ім'я, телефон або email клієнта...")
        search_client_btn = QPushButton("Пошук")
        search_client_btn.setObjectName("search_client_btn")
        add_client_btn = QPushButton("Додати клієнта")
        add_client_btn.setObjectName("add_client_btn")
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(search_input)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(add_client_btn)
        toolbar_layout.addWidget(search_client_btn)
        layout.addLayout(toolbar_layout)

        clients_table = QTableWidget(0, 6)
        clients_table.setObjectName("clients_table")
        clients_table.setHorizontalHeaderLabels(["ID", "ПІБ", "Телефон", "Email", "Документ", "Дата реєстрації"])
        clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        clients_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        clients_table.setColumnHidden(0, True)
        clients_table.verticalHeader().setVisible(False)
        layout.addWidget(clients_table)

        button_layout = QHBoxLayout()
        edit_client_btn = QPushButton("Редагувати")
        edit_client_btn.setObjectName("edit_client_btn")
        delete_client_btn = QPushButton("Видалити")
        delete_client_btn.setObjectName("delete_client_btn")
        history_btn = QPushButton("Історія оренд")
        history_btn.setObjectName("history_btn")
        button_layout.addStretch()
        button_layout.addWidget(edit_client_btn)
        button_layout.addWidget(delete_client_btn)
        button_layout.addWidget(history_btn)
        layout.addLayout(button_layout)

        tab.setLayout(layout)
        return tab


    def create_rentals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        main_layout = QHBoxLayout()

        rental_form_group = QGroupBox("Нова оренда")
        rental_form_group.setObjectName("rental_form_group")
        form_layout = QFormLayout()

        # Замінюємо QComboBox на QLineEdit з пошуком
        client_search = QLineEdit()
        client_search.setObjectName("client_search")
        client_search.setPlaceholderText("Введіть ім'я або прізвище клієнта...")

        # Додаємо прихований QComboBox для збереження вибраного ID клієнта
        client_combo = QComboBox()
        client_combo.setObjectName("client_combo")
        client_combo.setVisible(False)
        client_combo.addItem("Виберіть клієнта...", None)

        # Додаємо випадаючий список результатів пошуку
        client_results = QTableWidget(0, 3)
        client_results.setObjectName("client_results")
        client_results.setHorizontalHeaderLabels(["ID", "ПІБ", "Телефон"])
        client_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        client_results.setColumnHidden(0, True)
        client_results.setSelectionBehavior(QTableWidget.SelectRows)
        client_results.setSelectionMode(QTableWidget.SingleSelection)
        client_results.setMaximumHeight(150)
        client_results.setVisible(False)

        # Об’єднуємо поле пошуку та результати в один контейнер
        client_layout = QVBoxLayout()
        client_layout.addWidget(client_search)
        client_layout.addWidget(client_results)
        client_layout.addWidget(client_combo)  # прихований

        form_layout.addRow("Клієнт:", client_layout)

        bike_combo = QComboBox()
        bike_combo.setObjectName("bike_combo")
        bike_combo.addItem("Виберіть велосипед...", None)
        form_layout.addRow("Велосипед:", bike_combo)

        start_time = QDateTimeEdit(QDateTime.currentDateTime())
        start_time.setObjectName("start_time")
        start_time.setDisplayFormat("dd.MM.yyyy HH:mm")
        form_layout.addRow("Час початку:", start_time)



        duration_spin = QSpinBox()
        duration_spin.setObjectName("duration_spin")
        duration_spin.setRange(1, 72)
        duration_spin.setSuffix(" год")
        form_layout.addRow("Тривалість:", duration_spin)

        discount_spin = QDoubleSpinBox()
        discount_spin.setObjectName("discount_spin")
        discount_spin.setRange(0, 50)
        discount_spin.setSuffix(" %")
        form_layout.addRow("Знижка:", discount_spin)

        price_field = QLineEdit("0.00")
        price_field.setObjectName("price_field")
        price_field.setReadOnly(True)
        form_layout.addRow("Вартість:", price_field)

        form_buttons = QHBoxLayout()
        calculate_btn = QPushButton("Розрахувати")
        calculate_btn.setObjectName("calculate_btn")
        create_rental_btn = QPushButton("Оформити оренду")
        create_rental_btn.setObjectName("create_rental_btn")
        form_buttons.addWidget(calculate_btn)
        form_buttons.addWidget(create_rental_btn)
        form_layout.addRow("", form_buttons)

        rental_form_group.setLayout(form_layout)

        active_rentals_group = QGroupBox("Активні оренди")
        active_rentals_group.setObjectName("active_rentals_group")
        active_layout = QVBoxLayout()
        active_table = QTableWidget(0, 6)
        active_table.setObjectName("active_table")
        active_table.setHorizontalHeaderLabels(
            ["ID", "Клієнт", "Велосипед", "Початок", "Очікуване завершення", "Вартість"]
        )
        active_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        active_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        active_table.setColumnHidden(0, True)
        active_table.verticalHeader().setVisible(False)
        button_layout = QHBoxLayout()
        return_bike_btn = QPushButton("Завершити оренду")
        return_bike_btn.setObjectName("return_bike_btn")
        extend_rental_btn = QPushButton("Продовжити")
        extend_rental_btn.setObjectName("extend_rental_btn")
        button_layout.addStretch()
        button_layout.addWidget(extend_rental_btn)
        button_layout.addWidget(return_bike_btn)
        active_layout.addWidget(active_table)
        active_layout.addLayout(button_layout)
        active_rentals_group.setLayout(active_layout)

        main_layout.addWidget(rental_form_group, 40)
        main_layout.addWidget(active_rentals_group, 60)
        layout.addLayout(main_layout)
        tab.setLayout(layout)
        return tab

    def create_reports_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        header_label = QLabel("Формування звітів")
        header_label.setAlignment(Qt.AlignCenter)
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        params_group = QGroupBox("Параметри звіту")
        params_layout = QFormLayout()
        report_type_combo = QComboBox()
        report_type_combo.setObjectName("report_type_combo")
        report_type_combo.addItems(["Оренди за період", "Аналіз використання велосипедів",
                                    "Дохід за періодами", "Аналіз клієнтської бази", "Популярність типів велосипедів"])
        start_date = QDateTimeEdit(QDateTime.currentDateTime().addDays(-30))
        start_date.setObjectName("start_date")
        start_date.setDisplayFormat("dd.MM.yyyy")
        end_date = QDateTimeEdit(QDateTime.currentDateTime())
        end_date.setObjectName("end_date")
        end_date.setDisplayFormat("dd.MM.yyyy")
        format_combo = QComboBox()
        format_combo.setObjectName("format_combo")
        format_combo.addItems(["PDF", "Excel"])
        params_layout.addRow("Тип звіту:", report_type_combo)
        params_layout.addRow("Дата початку:", start_date)
        params_layout.addRow("Дата кінця:", end_date)
        params_layout.addRow("Формат:", format_combo)
        report_btn = QPushButton("Сформувати звіт")
        report_btn.setObjectName("report_btn")
        params_layout.addRow("", report_btn)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        preview_group = QGroupBox("Попередній перегляд")
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Тут буде відображено попередній перегляд звіту")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("background-color: #ffffff; padding: 50px; border: 1px dashed #cccccc;")
        preview_layout.addWidget(preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        tab.setLayout(layout)
        return tab
