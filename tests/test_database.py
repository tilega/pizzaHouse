"""Запуск: python -m unittest discover -s tests -v"""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database as db


class PizzaHouseDbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.patcher = patch.object(db, 'DB_PATH', Path(self.tmp.name) / 'test.db')
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        db.initialize_database()

    def test_starter_rows_and_existing_data_survive_restart(self):
        self.assertEqual(len(db.list_menu_items()), 15)
        self.assertEqual(len(db.list_ingredients()), 37)
        db.update_ingredient(1, 'Борошно пшеничне', 'кг', '4.5', '0.5', 35)
        db.initialize_database()
        self.assertEqual(db.get_ingredient(1)['quantity'], 4.5)
        self.assertEqual(len(db.list_ingredients()), 37)

    def test_recipes_availability_and_update(self):
        menu = db.get_menu_catalog_item(1)
        self.assertEqual(menu['availability'], 'Склад не задано')
        db.save_menu_with_recipe(1, 'Маргарита', 'Піца', 220, [(1, '0.25'), (7, '0.1')], None)
        menu = db.get_menu_catalog_item(1)
        self.assertEqual(menu['availability'], 'Бракує')
        self.assertEqual({r['ingredient_id'] for r in menu['recipe']}, {1, 7})
        db.update_ingredient(1, 'Борошно пшеничне', 'кг', '1', '0.5', 35)
        self.assertEqual(db.get_menu_catalog_item(1)['availability'], 'Бракує')
        db.update_ingredient(7, 'Сир моцарела', 'кг', '0.2', '0.05', 320)
        menu = db.get_menu_catalog_item(1)
        self.assertEqual(menu['availability'], 'Можна готувати')
        self.assertEqual(menu['max_portions'], 2)
        db.save_menu_with_recipe(1, 'Маргарита', 'Піца', 220, [(1, '0.75')], None)
        self.assertEqual(db.get_menu_catalog_item(1)['max_portions'], 1)

    def test_transaction_preserves_old_recipe_on_invalid_edit(self):
        db.save_menu_with_recipe(1, 'Маргарита', 'Піца', 220, [(1, '0.25')], None)
        with self.assertRaises(ValueError):
            db.save_menu_with_recipe(1, 'Змінена', 'Піца', 230, [(1, '0.3'), (99999, '1')], None)
        self.assertEqual(db.get_menu_catalog_item(1)['name'], 'Маргарита')
        self.assertEqual(len(db.get_menu_catalog_item(1)['recipe']), 1)
        with self.assertRaises(ValueError):
            db.save_menu_with_recipe(1, 'Маргарита', 'Піца', 220, [(1, 0)], None)

    def test_delete_ingredient_cascades_and_unit_restriction(self):
        db.save_menu_with_recipe(1, 'Маргарита', 'Піца', 220, [(1, '0.25')], None)
        with self.assertRaises(ValueError):
            db.update_ingredient(1, 'Борошно пшеничне', 'шт', 4, 1, 35)
        self.assertEqual(db.menu_usage_for_ingredient(1), ['Маргарита'])
        db.remove_ingredient(1)
        self.assertEqual(db.get_menu_catalog_item(1)['availability'], 'Склад не задано')

    def test_photo_and_menu_deletion(self):
        path = 'assets/menu_photos/example.png'
        new_id = db.save_menu_with_recipe(None, 'Тестова', 'Піца', '139.99', [(1, '0.2')], path)
        self.assertEqual(db.get_menu_catalog_item(new_id)['image_path'], path)
        db.remove_menu_item(new_id)
        self.assertIsNone(db.get_menu_catalog_item(new_id))
        with db.db_connection() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM menu_recipes WHERE menu_id=?',(new_id,)).fetchone()[0], 0)

    def test_migration_from_old_database(self):
        old_db = Path(self.tmp.name) / 'legacy.db'
        with sqlite3.connect(old_db) as con:
            con.execute('''CREATE TABLE menu_items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE, category TEXT NOT NULL, price_cents INTEGER NOT NULL)''')
            con.execute("INSERT INTO menu_items (name,name_key,category,price_cents) VALUES('Тест','тест','Піца',9999)")
        with patch.object(db,'DB_PATH',old_db):
            db.initialize_database()
            self.assertEqual(str(db.get_menu_item(1)['price']), '99.99')
            self.assertIsNone(db.get_menu_catalog_item(1)['image_path'])
            db.save_menu_with_recipe(1,'Тест','Піца',99.99,[(1,'0.1')],None)
            self.assertEqual(len(db.get_menu_catalog_item(1)['recipe']),1)

if __name__=='__main__':
    unittest.main()
