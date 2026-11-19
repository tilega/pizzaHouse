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


def get_account_login(customer_id):
    with db_connection() as conn:
        row = conn.execute('SELECT login FROM customer_accounts WHERE customer_id=?',
                           (customer_id,)).fetchone()
        return row['login'] if row else None


def update_account(customer_id, login, first_name, last_name, phone, email, address,
                   current_password='', new_password=''):
    # Atomic update; preserve customer ID and order history.
    from people_db import _customer_payload
    login = login.strip()
    if not login or len(login) > 80:
        raise ValueError('Логін має містити від 1 до 80 символів')
    if new_password and len(new_password) < 6:
        raise ValueError('Новий пароль має містити щонайменше 6 символів')
    with db_connection() as conn:
        customer = conn.execute('SELECT * FROM customers WHERE customer_id=?',
                                (customer_id,)).fetchone()
        if customer is None:
            raise ValueError('Клієнта не знайдено')
        account = conn.execute('SELECT * FROM customer_accounts WHERE customer_id=?',
                               (customer_id,)).fetchone()
        if account is None:
            raise ValueError('Акаунт не знайдено. Створіть власний обліковий запис.')
        if login.casefold() != account['login'].casefold() or new_password:
            if not hmac.compare_digest(account['password_hash'],
                                       _hash(current_password, account['salt'])):
                raise ValueError('Невірний поточний пароль')
        payload = _customer_payload(first_name, last_name, phone, email, address,
                                    customer['registration_date'])
        conn.execute('''UPDATE customers SET first_name=?,last_name=?,phone=?,email=?,
            address=?,registration_date=? WHERE customer_id=?''', (*payload, customer_id))
        try:
            conn.execute('UPDATE customer_accounts SET login=? WHERE customer_id=?',
                         (login, customer_id))
        except __import__('sqlite3').IntegrityError as exc:
            raise ValueError('Цей логін уже зайнятий') from exc
        if new_password:
            salt = os.urandom(16)
            conn.execute('''UPDATE customer_accounts SET salt=?,password_hash=?
                WHERE customer_id=?''', (salt, _hash(new_password, salt), customer_id))
    return login
