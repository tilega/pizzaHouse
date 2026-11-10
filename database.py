"""SQLite-хранилище Pizza House: меню и склад ингредиентов."""

from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
import sqlite3


# База всегда лежит рядом с database.py, независимо от папки запуска Visual Studio.
DB_PATH = Path(__file__).resolve().parent / "pizza_house.db"

# Начальные позиции — из текущего макета/таблицы меню Pizza House.
# Добавляются ТОЛЬКО при первом создании таблицы, поэтому пользовательские
# изменения не будут перезаписаны при следующих запусках.
STARTER_MENU = [
    (1, "Маргарита", "Піца", 22000),
    (2, "Чотири сири", "Піца", 31000),
    (3, "Пепероні", "Піца", 28000),
    (4, "Гавайська", "Піца", 27000),
    (5, "М'ясна", "Піца", 32000),
    (6, "BBQ Chicken", "Піца", 30000),
    (7, "Кальцоне", "Піца", 25000),
    (8, "Картопля фрі", "Закуска", 10000),
    (9, "Курячі нагетси", "Закуска", 14000),
    (10, "Часникові грінки", "Закуска", 9000),
    (11, "Coca-Cola", "Напій", 6000),
    (12, "Sprite", "Напій", 6000),
    (13, "Вода без газу", "Напій", 3500),
    (14, "Лимонад", "Напій", 9000),
    (15, "Часниковий соус", "Соус", 3000),
]


# Названия, цены и коды взяты из Excel-листа «Інгредієнти».
# В исходной таблице нет остатков, поэтому склад начинается с 0.
# Для жидкостей выбрана единица «л», для остальных — «кг»;
# единицы и цены можно редактировать через интерфейс.
STARTER_INGREDIENTS = [
    ("1_1", "Борошно пшеничне", 35, "кг"),
    ("1_2", "Дріжджі", 180, "кг"),
    ("1_3", "Сіль", 20, "кг"),
    ("1_4", "Цукор", 35, "кг"),
    ("1_5", "Оливкова олія", 250, "л"),
    ("1_6", "Томатний соус", 100, "кг"),
    ("1_7", "Сир моцарела", 320, "кг"),
    ("1_8", "Сир пармезан", 550, "кг"),
    ("1_9", "Сир дорблю", 480, "кг"),
    ("1_10", "Сир чедер", 350, "кг"),
    ("1_11", "Сир гауда", 300, "кг"),
    ("1_12", "Пепероні", 420, "кг"),
    ("1_13", "Шинка", 250, "кг"),
    ("1_14", "Куряче філе", 220, "кг"),
    ("1_15", "Бекон", 400, "кг"),
    ("1_16", "Яловичий фарш", 350, "кг"),
    ("1_17", "Ананаси консервовані", 150, "кг"),
    ("1_18", "Печериці", 120, "кг"),
    ("1_19", "Перець болгарський", 130, "кг"),
    ("1_20", "Цибуля", 35, "кг"),
    ("1_21", "Оливки", 220, "кг"),
    ("1_22", "Кукурудза консервована", 100, "кг"),
    ("1_23", "Соус BBQ", 150, "кг"),
    ("1_24", "Часник", 180, "кг"),
    ("1_25", "Вершкове масло", 300, "кг"),
    ("1_26", "Петрушка", 200, "кг"),
    ("1_27", "Картопля", 30, "кг"),
    ("1_28", "Рослинна олія", 80, "л"),
    ("1_29", "Панірувальні сухарі", 70, "кг"),
    ("1_30", "Яйця", 100, "кг"),
    ("1_31", "Молоко", 50, "л"),
    ("1_32", "Хліб", 60, "кг"),
    ("1_33", "Coca-Cola", 70, "л"),
    ("1_34", "Sprite", 70, "л"),
    ("1_35", "Вода без газу", 15, "л"),
    ("1_36", "Лимонад", 100, "л"),
    ("1_37", "Часниковий соус", 150, "кг"),
]


@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        with conn:  # commit при успехе, rollback при ошибке
            yield conn
    finally:
        conn.close()


def initialize_database():
    """Создать таблицу и наполнить её только при первом создании."""
    with db_connection() as conn:
        already_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='menu_items'"
        ).fetchone() is not None

        conn.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                name_key TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK (price_cents > 0)
            )
        """)

        if not already_exists:
            conn.executemany(
                """INSERT INTO menu_items
                   (id, name, name_key, category, price_cents)
                   VALUES (?, ?, ?, ?, ?)""",
                [(i, name, name.casefold(), category, cents)
                 for i, name, category, cents in STARTER_MENU],
            )

        # Склад. При обновлении старой базы таблица могла уже существовать,
        # но остаться пустой. В этом случае исходные 37 ингредиентов нужно
        # импортировать ОДИН РАЗ, без удаления и перезаписи данных пользователя.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_code TEXT UNIQUE,
                name TEXT NOT NULL,
                name_key TEXT NOT NULL UNIQUE,
                unit TEXT NOT NULL CHECK (unit IN ('кг', 'л', 'шт')),
                stock_milli INTEGER NOT NULL DEFAULT 0 CHECK (stock_milli >= 0),
                min_stock_milli INTEGER NOT NULL DEFAULT 0 CHECK (min_stock_milli >= 0),
                price_cents INTEGER NOT NULL CHECK (price_cents > 0)
            )
        """)
        # Служебная отметка не позволит вернуть товары, которые администратор
        # сознательно удалил позднее — даже если склад стал полностью пустым.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        seeded = conn.execute(
            "SELECT 1 FROM app_meta WHERE key = 'starter_ingredients_v1'"
        ).fetchone()
        if seeded is None:
            existing_count = conn.execute(
                "SELECT COUNT(*) FROM ingredients"
            ).fetchone()[0]
            if existing_count == 0:
                conn.executemany(
                    """INSERT OR IGNORE INTO ingredients
                       (source_code, name, name_key, unit, stock_milli,
                        min_stock_milli, price_cents)
                       VALUES (?, ?, ?, ?, 0, 0, ?)""",
                    [(code, name, name.casefold(), unit, price * 100)
                     for code, name, price, unit in STARTER_INGREDIENTS],
                )
            # Отмечаем импорт, даже если в существующей БД уже есть записи.
            conn.execute(
                "INSERT INTO app_meta (key, value) VALUES (?, ?)",
                ('starter_ingredients_v1', 'done'),
            )


def _as_item(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": Decimal(row["price_cents"]) / 100,
    }


def _price_to_cents(price):
    value = Decimal(str(price))
    cents = value * 100
    if (not value.is_finite() or value <= 0
            or value > Decimal("1000000")
            or cents != cents.to_integral_value()):
        raise ValueError("Некоректна ціна")
    return int(cents)


def list_menu_items():
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, category, price_cents FROM menu_items ORDER BY id"
        ).fetchall()
    return [_as_item(row) for row in rows]


def get_menu_item(item_id):
    with db_connection() as conn:
        row = conn.execute(
            "SELECT id, name, category, price_cents FROM menu_items WHERE id = ?",
            (item_id,),
        ).fetchone()
    return _as_item(row)


def add_menu_item(name, category, price):
    with db_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO menu_items (name, name_key, category, price_cents)
               VALUES (?, ?, ?, ?)""",
            (name, name.casefold(), category, _price_to_cents(price)),
        )
        return cursor.lastrowid


def update_menu_item(item_id, name, category, price):
    with db_connection() as conn:
        conn.execute(
            """UPDATE menu_items
               SET name = ?, name_key = ?, category = ?, price_cents = ?
               WHERE id = ?""",
            (name, name.casefold(), category, _price_to_cents(price), item_id),
        )


def remove_menu_item(item_id):
    with db_connection() as conn:
        conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))


def _quantity_to_milli(value, unit):
    """Сохраняем точность до 1 грамма/миллилитра и целое число штук."""
    if unit not in ("кг", "л", "шт"):
        raise ValueError("Невірна одиниця вимірювання")
    amount = Decimal(str(value))
    milli = amount * 1000
    if (not amount.is_finite() or amount < 0 or amount > Decimal("1000000")
            or milli != milli.to_integral_value()
            or (unit == "шт" and amount != amount.to_integral_value())):
        raise ValueError("Некоректна кількість")
    return int(milli)


def _ingredient_from_row(row):
    if row is None:
        return None
    quantity = Decimal(row["stock_milli"]) / 1000
    minimum = Decimal(row["min_stock_milli"]) / 1000
    if quantity == 0:
        status = "Немає"
    elif quantity <= minimum:
        status = "Мало"
    else:
        status = "Достатньо"
    return {
        "id": row["id"],
        "code": row["source_code"] or str(row["id"]),
        "name": row["name"],
        "unit": row["unit"],
        "quantity": quantity,
        "minimum": minimum,
        "price": Decimal(row["price_cents"]) / 100,
        "status": status,
    }


def list_ingredients():
    with db_connection() as conn:
        rows = conn.execute("SELECT * FROM ingredients ORDER BY id").fetchall()
    return [_ingredient_from_row(row) for row in rows]


def get_ingredient(ingredient_id):
    with db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM ingredients WHERE id = ?", (ingredient_id,)
        ).fetchone()
    return _ingredient_from_row(row)


def add_ingredient(name, unit, quantity, minimum, price):
    name = name.strip()
    if not name or len(name) > 100:
        raise ValueError("Введіть назву (до 100 символів)")
    stock = _quantity_to_milli(quantity, unit)
    min_stock = _quantity_to_milli(minimum, unit)
    price_cents = _price_to_cents(price)
    with db_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO ingredients
               (name, name_key, unit, stock_milli, min_stock_milli, price_cents)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, name.casefold(), unit, stock, min_stock, price_cents),
        )
    return cursor.lastrowid


def update_ingredient(ingredient_id, name, unit, quantity, minimum, price):
    name = name.strip()
    if not name or len(name) > 100:
        raise ValueError("Введіть назву (до 100 символів)")
    stock = _quantity_to_milli(quantity, unit)
    min_stock = _quantity_to_milli(minimum, unit)
    price_cents = _price_to_cents(price)
    with db_connection() as conn:
        conn.execute(
            """UPDATE ingredients
               SET name = ?, name_key = ?, unit = ?, stock_milli = ?,
                   min_stock_milli = ?, price_cents = ?
               WHERE id = ?""",
            (name, name.casefold(), unit, stock, min_stock, price_cents, ingredient_id),
        )


def remove_ingredient(ingredient_id):
    with db_connection() as conn:
        conn.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
