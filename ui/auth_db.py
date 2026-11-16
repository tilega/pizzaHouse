"""Локальні облікові записи клієнтів; паролі зберігаються як PBKDF2-хеші."""
import hashlib
import hmac
import os
from datetime import date
from database import db_connection
from people_db import add_customer


def initialize_auth_database():
    with db_connection() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS customer_accounts(
            login TEXT PRIMARY KEY COLLATE NOCASE,
            customer_id TEXT NOT NULL UNIQUE REFERENCES customers(customer_id) ON DELETE CASCADE,
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL
        )""")


def _hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 240000)


def register(login, password, first_name, last_name, phone, email, address=''):
    login = login.strip()
    if not login or len(login) > 80 or len(password) < 6:
        raise ValueError('Логін обов’язковий, пароль — від 6 символів')
    if not first_name.strip() or not last_name.strip() or not phone.strip():
        raise ValueError('Заповніть ім’я, прізвище та телефон')
    salt = os.urandom(16)
    # Перевіряємо конфлікт до створення користувача.
    with db_connection() as conn:
        if conn.execute('SELECT 1 FROM customer_accounts WHERE login=?', (login,)).fetchone():
            raise ValueError('Такий логін уже зайнятий')
    # Створюємо клієнта і акаунт; при помилці акаунта відкочуємо нового клієнта.
    from people_db import delete_customer
    customer_id = add_customer(first_name, last_name, phone, email, address, date.today().isoformat())
    try:
        with db_connection() as conn:
            conn.execute('INSERT INTO customer_accounts VALUES (?,?,?,?)',
                         (login, customer_id, salt, _hash(password, salt)))
    except Exception:
        delete_customer(customer_id)
        raise
    return customer_id


def authenticate(login, password):
    with db_connection() as conn:
        row = conn.execute('SELECT * FROM customer_accounts WHERE login=?', (login.strip(),)).fetchone()
    if row and hmac.compare_digest(row['password_hash'], _hash(password, row['salt'])):
        return row['customer_id']
    return None
