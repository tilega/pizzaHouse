"""Акаунти працівників панелі керування (окремо від клієнтів).

Ролі: admin та moderator. Паролі не зберігаються відкритим текстом.
"""
import hashlib
import hmac
import os
import sqlite3
from datetime import datetime

from database import db_connection

ITERATIONS = 260_000


def _hash(password, salt):
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)


def _validate_password(password):
    if len(password) < 8 or len(password) > 128:
        raise ValueError('Пароль має містити від 8 до 128 символів')


def initialize_staff_database():
    """Додає таблицю, не торкаючись існуючих користувачів/замовлень.

    Перший запуск: переносимо старий демовхід admin/1234 на окрему форму.
    """
    with db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS staff_accounts (
            login TEXT PRIMARY KEY COLLATE NOCASE,
            role TEXT NOT NULL CHECK(role IN ('admin','moderator')),
            salt BLOB NOT NULL,
            password_hash BLOB NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1)),
            created_at TEXT NOT NULL
        )''')
        count = conn.execute('SELECT COUNT(*) FROM staff_accounts').fetchone()[0]
        if not count:
            salt = os.urandom(16)
            conn.execute('''INSERT INTO staff_accounts
                (login,role,salt,password_hash,enabled,created_at)
                VALUES (?,?,?,?,1,?)''',
                ('admin', 'admin', salt, _hash('1234', salt), datetime.now().isoformat(timespec='seconds')))


def authenticate_staff(login, password):
    login = login.strip()
    if not login or not password:
        return None
    with db_connection() as conn:
        row = conn.execute('''SELECT login,role,salt,password_hash FROM staff_accounts
                              WHERE login=? AND enabled=1''', (login,)).fetchone()
    if not row or not hmac.compare_digest(row['password_hash'], _hash(password,row['salt'])):
        return None
    return {'login': row['login'], 'role': row['role']}


def list_staff_accounts():
    with db_connection() as conn:
        rows = conn.execute('''SELECT login, role, enabled, created_at FROM staff_accounts
                              ORDER BY CASE WHEN role='admin' THEN 0 ELSE 1 END, login''').fetchall()
    return [dict(row) for row in rows]


def create_moderator(login, password):
    login = login.strip()
    if not 3 <= len(login) <= 60 or any(x.isspace() for x in login):
        raise ValueError('Логін: 3–60 символів, без пробілів')
    _validate_password(password)
    salt = os.urandom(16)
    try:
        with db_connection() as conn:
            conn.execute('''INSERT INTO staff_accounts
                    (login,role,salt,password_hash,enabled,created_at)
                    VALUES (?,'moderator',?,?,1,?)''',
                (login, salt, _hash(password, salt), datetime.now().isoformat(timespec='seconds')))
    except sqlite3.IntegrityError as exc:
        raise ValueError('Такий логін уже існує') from exc


def set_moderator_enabled(login, enabled):
    with db_connection() as conn:
        result = conn.execute('''UPDATE staff_accounts SET enabled=?
                                 WHERE login=? AND role='moderator' ''', (int(bool(enabled)), login))
        if result.rowcount != 1:
            raise ValueError('Модератора не знайдено')


def reset_moderator_password(login, new_password):
    _validate_password(new_password)
    salt = os.urandom(16)
    with db_connection() as conn:
        result = conn.execute('''UPDATE staff_accounts SET salt=?,password_hash=?
                                 WHERE login=? AND role='moderator' ''',
                              (salt, _hash(new_password, salt), login))
        if result.rowcount != 1:
            raise ValueError('Модератора не знайдено')


def delete_moderator(login):
    with db_connection() as conn:
        result = conn.execute("DELETE FROM staff_accounts WHERE login=? AND role='moderator'", (login,))
        if result.rowcount != 1:
            raise ValueError('Модератора не знайдено')


def change_staff_password(login, old_password, new_password):
    _validate_password(new_password)
    salt = os.urandom(16)
    with db_connection() as conn:
        row = conn.execute('SELECT salt,password_hash FROM staff_accounts WHERE login=? AND enabled=1',
                           (login,)).fetchone()
        if not row or not hmac.compare_digest(row['password_hash'], _hash(old_password, row['salt'])):
            raise ValueError('Неправильний поточний пароль')
        conn.execute('UPDATE staff_accounts SET salt=?,password_hash=? WHERE login=?',
                     (salt, _hash(new_password, salt), login))
