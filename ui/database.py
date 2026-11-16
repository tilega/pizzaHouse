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


# Названия и цены взяты из Excel-листа «Інгредієнти».
# В исходной таблице нет остатков, поэтому склад начинается с 0.
# Для жидкостей выбрана единица «л», для остальных — «кг»;
# единицы и цены можно редактировать через интерфейс.
STARTER_INGREDIENTS = [
    ("Борошно пшеничне", 35, "кг"),
    ("Дріжджі", 180, "кг"),
    ("Сіль", 20, "кг"),
    ("Цукор", 35, "кг"),
    ("Оливкова олія", 250, "л"),
    ("Томатний соус", 100, "кг"),
    ("Сир моцарела", 320, "кг"),
    ("Сир пармезан", 550, "кг"),
    ("Сир дорблю", 480, "кг"),
    ("Сир чедер", 350, "кг"),
    ("Сир гауда", 300, "кг"),
    ("Пепероні", 420, "кг"),
    ("Шинка", 250, "кг"),
    ("Куряче філе", 220, "кг"),
    ("Бекон", 400, "кг"),
    ("Яловичий фарш", 350, "кг"),
    ("Ананаси консервовані", 150, "кг"),
    ("Печериці", 120, "кг"),
    ("Перець болгарський", 130, "кг"),
    ("Цибуля", 35, "кг"),
    ("Оливки", 220, "кг"),
    ("Кукурудза консервована", 100, "кг"),
    ("Соус BBQ", 150, "кг"),
    ("Часник", 180, "кг"),
    ("Вершкове масло", 300, "кг"),
    ("Петрушка", 200, "кг"),
    ("Картопля", 30, "кг"),
    ("Рослинна олія", 80, "л"),
    ("Панірувальні сухарі", 70, "кг"),
    ("Яйця", 100, "кг"),
    ("Молоко", 50, "л"),
    ("Хліб", 60, "кг"),
    ("Coca-Cola", 70, "л"),
    ("Sprite", 70, "л"),
    ("Вода без газу", 15, "л"),
    ("Лимонад", 100, "л"),
    ("Часниковий соус", 150, "кг"),
]


@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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

        # Безпечна міграція для баз, створених попередньою версією програми.
        existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(menu_items)")}
        if "weight_g" not in existing_cols:
            conn.execute("ALTER TABLE menu_items ADD COLUMN weight_g INTEGER")
        if "image_path" not in existing_cols:
            conn.execute("ALTER TABLE menu_items ADD COLUMN image_path TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS menu_recipes (
                menu_id INTEGER NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
                ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
                quantity_milli INTEGER NOT NULL CHECK (quantity_milli > 0),
                PRIMARY KEY (menu_id, ingredient_id)
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
                       (name, name_key, unit, stock_milli,
                        min_stock_milli, price_cents)
                       VALUES (?, ?, ?, 0, 0, ?)""",
                    [(name, name.casefold(), unit, price * 100)
                     for name, price, unit in STARTER_INGREDIENTS],
                )
            # Отмечаем импорт, даже если в существующей БД уже есть записи.
            conn.execute(
                "INSERT INTO app_meta (key, value) VALUES (?, ?)",
                ('starter_ingredients_v1', 'done'),
            )

        # Старі версії імпортували службові коди на кшталт «1_1».
        # Вони не потрібні: є числовий PK ingredients.id, який
        # використовується в рецептурах та відображається в таблиці.
        # Прибираємо тільки старі коди з підкресленням, не змінюючи
        # id, залишки, рецептури та інші дані користувача.
        conn.execute("""
            UPDATE ingredients SET source_code = NULL
            WHERE source_code GLOB '1_[0-9]*'
        """)


def _as_item(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"],
        "price": Decimal(row["price_cents"]) / 100,
        "image_path": row["image_path"] if "image_path" in row.keys() else None,
        "weight_g": row["weight_g"] if "weight_g" in row.keys() else None,
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
            "SELECT id, name, category, price_cents, image_path, weight_g FROM menu_items ORDER BY id"
        ).fetchall()
    return [_as_item(row) for row in rows]


def get_menu_item(item_id):
    with db_connection() as conn:
        row = conn.execute(
            "SELECT id, name, category, price_cents, image_path, weight_g FROM menu_items WHERE id = ?",
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
        "code": f"I{1000 + row["id"]:04d}",
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
        old = conn.execute(
            "SELECT unit FROM ingredients WHERE id = ?", (ingredient_id,)
        ).fetchone()
        if old and old["unit"] != unit:
            used = conn.execute(
                "SELECT 1 FROM menu_recipes WHERE ingredient_id = ? LIMIT 1",
                (ingredient_id,),
            ).fetchone()
            used_in_purchase = False
            has_purchase_table = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='purchase_lines'"
            ).fetchone()
            if has_purchase_table:
                used_in_purchase = conn.execute(
                    "SELECT 1 FROM purchase_lines WHERE ingredient_id = ? LIMIT 1",
                    (ingredient_id,),
                ).fetchone() is not None
            if used or used_in_purchase:
                raise ValueError(
                    "Неможливо змінити одиницю вимірювання: інгредієнт використовується "
                    "в рецептурі або закупівлі."
                )
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


# Рецептура: одна позиція меню містить багато інгредієнтів,
# а один інгредієнт може входити до складу багатьох позицій.
def _recipe_for_menu(conn, menu_id):
    rows = conn.execute("""
        SELECT r.ingredient_id, r.quantity_milli, i.name, i.unit,
               i.stock_milli
        FROM menu_recipes r
        JOIN ingredients i ON i.id = r.ingredient_id
        WHERE r.menu_id = ? ORDER BY i.name COLLATE NOCASE
    """, (menu_id,)).fetchall()
    return [{
        "ingredient_id": row["ingredient_id"],
        "name": row["name"],
        "unit": row["unit"],
        "amount": Decimal(row["quantity_milli"]) / 1000,
        "in_stock": Decimal(row["stock_milli"]) / 1000,
    } for row in rows]


def _add_availability(item, recipe):
    item["recipe"] = recipe
    if not recipe:
        item["availability"] = "Склад не задано"
        item["missing"] = []
        item["max_portions"] = None
        return item
    missing = [part for part in recipe if part["in_stock"] < part["amount"]]
    item["missing"] = missing
    item["availability"] = "Бракує" if missing else "Можна готувати"
    item["max_portions"] = min(
        int(part["in_stock"] / part["amount"]) for part in recipe
    )
    return item


def list_menu_catalog():
    """Меню з фото, рецептурами та станом запасів на одну порцію."""
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT id, name, category, price_cents, image_path, weight_g
            FROM menu_items ORDER BY id
        """).fetchall()
        all_recipes = conn.execute("""
            SELECT r.menu_id, r.ingredient_id, r.quantity_milli,
                   i.name, i.unit, i.stock_milli
            FROM menu_recipes r
            JOIN ingredients i ON i.id = r.ingredient_id
            ORDER BY i.name COLLATE NOCASE
        """).fetchall()
        by_menu = {}
        for row in all_recipes:
            by_menu.setdefault(row["menu_id"], []).append({
                "ingredient_id": row["ingredient_id"],
                "name": row["name"],
                "unit": row["unit"],
                "amount": Decimal(row["quantity_milli"]) / 1000,
                "in_stock": Decimal(row["stock_milli"]) / 1000,
            })
        return [
            _add_availability(_as_item(row), by_menu.get(row["id"], []))
            for row in rows
        ]


def get_menu_catalog_item(item_id):
    with db_connection() as conn:
        row = conn.execute("""
            SELECT id, name, category, price_cents, image_path, weight_g
            FROM menu_items WHERE id = ?
        """, (item_id,)).fetchone()
        if row is None:
            return None
        return _add_availability(_as_item(row), _recipe_for_menu(conn, item_id))


def save_menu_with_recipe(item_id, name, category, price, recipe, image_path):
    """Атомарно зберегти позицію та її склад; рецепт — [(id, кількість), ...]."""
    name = name.strip()
    if not name or len(name) > 120:
        raise ValueError("Вкажіть назву позиції (до 120 символів)")
    price_cents = _price_to_cents(price)
    if image_path is not None and (not isinstance(image_path, str)
                                   or not image_path.startswith("assets/menu_photos/")):
        raise ValueError("Некоректний шлях до фотографії")
    if len({int(ingredient_id) for ingredient_id, _ in recipe}) != len(recipe):
        raise ValueError("Інгредієнт у складі повторюється")
    with db_connection() as conn:
        quantities = []
        for ingredient_id, quantity in recipe:
            ingredient = conn.execute(
                "SELECT unit FROM ingredients WHERE id = ?", (ingredient_id,)
            ).fetchone()
            if ingredient is None:
                raise ValueError("Один з інгредієнтів видалено зі складу")
            quantity_milli = _quantity_to_milli(quantity, ingredient["unit"])
            if quantity_milli <= 0:
                raise ValueError("Кількість інгредієнта має бути більшою за 0")
            quantities.append((int(ingredient_id), quantity_milli))
        if item_id is None:
            cur = conn.execute("""
                INSERT INTO menu_items (name, name_key, category, price_cents, image_path)
                VALUES (?, ?, ?, ?, ?)
            """, (name, name.casefold(), category, price_cents, image_path))
            item_id = cur.lastrowid
        else:
            cur = conn.execute("""
                UPDATE menu_items SET name=?, name_key=?, category=?,
                    price_cents=?, image_path=? WHERE id=?
            """, (name, name.casefold(), category, price_cents, image_path, item_id))
            if cur.rowcount == 0:
                raise ValueError("Позицію меню не знайдено")
        conn.execute("DELETE FROM menu_recipes WHERE menu_id = ?", (item_id,))
        conn.executemany("""
            INSERT INTO menu_recipes (menu_id, ingredient_id, quantity_milli)
            VALUES (?, ?, ?)
        """, [(item_id, ing_id, amount) for ing_id, amount in quantities])
        return item_id


def menu_usage_for_ingredient(ingredient_id):
    """Які позиції містять інгредієнт (для попередження перед видаленням)."""
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT m.name FROM menu_items m
            JOIN menu_recipes r ON r.menu_id = m.id
            WHERE r.ingredient_id = ? ORDER BY m.name
        """, (ingredient_id,)).fetchall()
    return [r["name"] for r in rows]
