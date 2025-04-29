import sys
import os
import unittest
from datetime import datetime
from .model import BikeRentalModel



class TestBikeRentalModel(unittest.TestCase):
    def setUp(self):
        # Використання in-memory бази даних для тестування
        self.model = BikeRentalModel(":memory:")

    def test_add_and_get_client(self):
        # Тест додавання нового клієнта та його подальшого отримання
        result = self.model.add_client("Іван Іванов", "+380501234567", "ivan@example.com", "Passport123")
        self.assertTrue(result, "Не вдалося додати клієнта")
        clients = self.model.get_all_clients()
        self.assertEqual(len(clients), 1, "Кількість клієнтів має бути 1")
        self.assertEqual(clients[0].name, "Іван Іванов", "Ім'я клієнта не співпадає з очікуваним")

    def test_update_client(self):
        # Тест оновлення даних клієнта
        self.model.add_client("Іван Іванов", "+380501234567", "ivan@example.com", "Passport123")
        clients = self.model.get_all_clients()
        client_id = clients[0].id
        result = self.model.update_client(client_id, name="Марія Петрівна")
        self.assertTrue(result, "Не вдалося оновити дані клієнта")
        updated_client = self.model.get_all_clients()[0]
        self.assertEqual(updated_client.name, "Марія Петрівна", "Ім'я клієнта не оновилося")

    def test_delete_client(self):
        # Тест видалення клієнта
        self.model.add_client("Іван Іванов", "+380501234567", "ivan@example.com", "Passport123")
        clients = self.model.get_all_clients()
        client_id = clients[0].id
        result, msg = self.model.delete_client(client_id)
        self.assertTrue(result, f"Не вдалося видалити клієнта: {msg}")
        self.assertEqual(len(self.model.get_all_clients()), 0, "Клієнт має бути видалений")

    def test_add_bike_and_search(self):
        # Тест додавання велосипеда та пошуку за критеріями
        result = self.model.add_bike("Giant", "SN12345", "Гірський", 50.0)
        self.assertTrue(result, "Не вдалося додати велосипед")
        bikes = self.model.get_all_bikes()
        self.assertEqual(len(bikes), 1, "Кількість велосипедів має бути 1")
        self.assertEqual(bikes[0].model, "Giant", "Модель велосипеда не співпадає")

        # Пошук велосипеда за моделлю, типом та статусом
        search_results = self.model.search_bikes("Giant", "Гірський", "Доступний")
        self.assertGreaterEqual(len(search_results), 1, "Пошук не повернув результатів")

    def test_create_and_complete_rental(self):
        # Тест створення оренди та її завершення
        # Додамо спочатку клієнта та велосипед
        self.model.add_client("Іван Іванов", "+380501234567", "ivan@example.com", "Passport123")
        client = self.model.get_all_clients()[0]
        self.model.add_bike("Giant", "SN12345", "Гірський", 50.0)
        bike = self.model.get_all_bikes()[0]

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rental_id, msg = self.model.create_rental(client.id, bike.id, start_time, 2, 0)
        self.assertIsNotNone(rental_id, "Не вдалося створити оренду")

        # Завершимо оренду
        result, complete_msg = self.model.complete_rental(rental_id)
        self.assertTrue(result, f"Не вдалося завершити оренду: {complete_msg}")

    def test_calculate_rental_price(self):
        # Тест розрахунку вартості оренди без знижки та зі знижкою
        self.model.add_bike("Giant", "SN12345", "Гірський", 50.0)
        bike = self.model.get_all_bikes()[0]

        # Тривалість 3 години, без знижки
        price = self.model.calculate_rental_price(bike.id, 3, 0)
        self.assertAlmostEqual(price, 150.0, places=2, msg="Невірний розрахунок вартості оренди без знижки")

        # Тривалість 3 години, з 10% знижкою
        price_discount = self.model.calculate_rental_price(bike.id, 3, 10)
        self.assertAlmostEqual(price_discount, 135.0, places=2, msg="Невірний розрахунок вартості оренди зі знижкою")


if __name__ == "__main__":
    unittest.main()
