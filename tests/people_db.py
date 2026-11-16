"""Клієнти й працівники Pizza House.

Дані зберігаються у ТІЙ САМІЙ pizza_house.db, що й меню та інгредієнти.
ID не залежать один від одного: C.... для клієнтів, E.... для працівників.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import sqlite3

from database import db_connection


# 9 клієнтів із аркуша «Користувачі» початкової Excel-таблиці.
# Нулі на початку телефонів відновлено з українського формату номера.
STARTER_CUSTOMERS = [
    ('C1042', 'Анна', 'Коваленко', '0501234567', 'anna.kovalenko@example.com', 'вул. Шевченка, 12', '2026-09-01'),
    ('C2087', 'Максим', 'Бондаренко', '0672345678', 'maksym.bondarenko@example.com', 'вул. Лесі Українки, 5', '2026-09-03'),
    ('C3156', 'Софія', 'Мельник', '0933456789', 'sofia.melnyk@example.com', 'вул. Франка, 25', '2026-09-05'),
    ('C4271', 'Артем', 'Шевченко', '0954567890', 'artem.shevchenko@example.com', 'вул. Садова, 14', '2026-09-07'),
    ('C5368', 'Марія', 'Ткаченко', '0635678901', 'maria.tkachenko@example.com', 'вул. Садова, 8', '2026-09-10'),
    ('C6429', 'Дмитро', 'Кравченко', '0996789012', 'dmytro.kravchenko@example.com', 'вул. Центральна, 41', '2026-09-12'),
    ('C7513', 'Ольга', 'Лисенко', '0977890123', 'olha.lysenko@example.com', 'вул. Миру, 7', '2026-09-15'),
    ('C8645', 'Владислав', 'Поліщук', '0668901234', 'vladyslav.polishchuk@example.com', 'вул. Молодіжна, 17', '2026-09-18'),
    ('C9732', 'Назар', 'Романенко', '0500123456', 'nazar.romanenko@example.com', 'вул. Центральна, 19', '2026-09-22'),
]

# 8 працівників із аркуша «Працівники». Зарплата зберігається в копійках.
STARTER_EMPLOYEES = [
    ('E1024', 'Олександр', 'Петренко', 'Піцайоло', '0502345671', 'oleksandr.petrenko@example.com', '2025-03-01', 2500000),
    ('E2158', 'Ірина', 'Мороз', 'Касир', '0673456782', 'iryna.moroz@example.com', '2025-04-15', 1800000),
    ('E3267', 'Андрій', 'Коваленко', "Кур'єр", '0934567893', 'andrii.kovalenko@example.com', '2025-05-20', 1600000),
    ('E4391', 'Катерина', 'Бойко', 'Адміністратор', '0955678904', 'kateryna.boiko@example.com', '2025-06-10', 2800000),
    ('E5472', 'Максим', 'Сидоренко', 'Піцайоло', '0636789015', 'maksym.sydorenko@example.com', '2025-08-01', 2600000),
    ('E6583', 'Вікторія', 'Шевчук', "Кур'єр", '0997890126', 'viktoriia.shevchuk@example.com', '2025-09-12', 1600000),
    ('E7649', 'Денис', 'Ткаченко', 'Кухар', '0978901237', 'denys.tkachenko@example.com', '2025-11-05', 2000000),
    ('E8751', 'Юлія', 'Мельник', 'Касир', '0669012348', 'yuliia.melnyk@example.com', '2026-01-18', 1800000),
]


def initialize_people_database():
    """Безпечна міграція без втрати меню, рецептів і складських залишків."""
    with db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT COLLATE NOCASE UNIQUE,
                address TEXT NOT NULL DEFAULT '',
                registration_date TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                position TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT COLLATE NOCASE UNIQUE,
                hire_date TEXT NOT NULL,
                salary_cents INTEGER NOT NULL DEFAULT 0 CHECK (salary_cents >= 0)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            )
        ''')
        # Зберігаємо лічильники в БД: видалення останнього запису
        # не призведе до повторного використання його ідентифікатора.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS people_id_sequences (
                kind TEXT PRIMARY KEY,
                next_number INTEGER NOT NULL CHECK (next_number > 0)
            )
        ''')
        for table, marker, rows, sql in [
            ('customers', 'seed_customers_excel_v1', STARTER_CUSTOMERS,
             '''INSERT INTO customers (customer_id, first_name, last_name, phone,
                  email, address, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?)'''),
            ('employees', 'seed_employees_excel_v1', STARTER_EMPLOYEES,
             '''INSERT INTO employees (employee_id, first_name, last_name, position,
                  phone, email, hire_date, salary_cents) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''),
        ]:
            seeded = conn.execute('SELECT 1 FROM app_meta WHERE key=?', (marker,)).fetchone()
            if not seeded:
                # Якщо користувач уже створив записи в старій версії,
                # не домішуємо до них тестову таблицю з Excel.
                count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
                if count == 0:
                    conn.executemany(sql, rows)
                conn.execute('INSERT INTO app_meta (key, value) VALUES (?, ?)', (marker, 'done'))
        for kind, table, field, prefix in [
            ('customer', 'customers', 'customer_id', 'C'),
            ('employee', 'employees', 'employee_id', 'E'),
        ]:
            values = [int(row[0][1:]) for row in conn.execute(
                f'SELECT {field} FROM {table}'
            ).fetchall() if re.fullmatch(rf'{prefix}[0-9]+', row[0])]
            first_unused = max(values, default=999) + 1
            conn.execute('''
                INSERT INTO people_id_sequences (kind, next_number)
                VALUES (?, ?)
                ON CONFLICT(kind) DO UPDATE SET
                    next_number = MAX(next_number, excluded.next_number)
            ''', (kind, first_unused))


def _new_id(conn, kind):
    prefix = {'customer': 'C', 'employee': 'E'}[kind]
    row = conn.execute('SELECT next_number FROM people_id_sequences WHERE kind=?', (kind,)).fetchone()
    if row is None:
        raise RuntimeError('Не ініціалізовано таблицю ID. Перезапустіть застосунок.')
    number = row['next_number']
    conn.execute('UPDATE people_id_sequences SET next_number=? WHERE kind=?', (number + 1, kind))
    return f'{prefix}{number:04d}'


def _clean(value, label, max_length=100, required=True):
    result = str(value or '').strip()
    if required and not result:
        raise ValueError(f'Поле «{label}» не може бути порожнім')
    if len(result) > max_length:
        raise ValueError(f'Поле «{label}» має бути не довшим за {max_length} символів')
    return result


def _phone(value):
    phone = _clean(value, 'Телефон', 40)
    simplified = re.sub(r'[\s()\-]', '', phone)
    if not re.fullmatch(r'\+?[0-9]{9,15}', simplified):
        raise ValueError('Вкажіть коректний номер телефону')
    if re.fullmatch(r'[0-9]{9}', simplified):
        simplified = '0' + simplified
    return simplified


def _email(value):
    email = _clean(value, 'Email', 150, required=False)
    if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise ValueError('Вкажіть коректний Email або залиште поле порожнім')
    return email or None


def _date(value, label):
    raw = _clean(value or date.today().isoformat(), label, 10)
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f'Поле «{label}»: дата має бути у форматі РРРР-ММ-ДД') from exc
    return parsed.isoformat()


def _salary_cents(value):
    try:
        amount = Decimal(str(value).strip().replace(',', '.'))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('Вкажіть коректну зарплату') from exc
    cents = amount * 100
    if (not amount.is_finite() or amount < 0 or amount > 10000000
            or cents != cents.to_integral_value()):
        raise ValueError('Зарплата має бути невід’ємним числом (до 2 знаків після коми)')
    return int(cents)


def _customer_payload(first_name, last_name, phone, email, address, registration_date):
    return (
        _clean(first_name, 'Ім’я', 80),
        _clean(last_name, 'Прізвище', 80),
        _phone(phone), _email(email),
        _clean(address, 'Адреса', 200, required=False),
        _date(registration_date, 'Дата реєстрації'),
    )


def _employee_payload(first_name, last_name, position, phone, email, hire_date, salary):
    return (
        _clean(first_name, 'Ім’я', 80),
        _clean(last_name, 'Прізвище', 80),
        _clean(position, 'Посада', 100),
        _phone(phone), _email(email),
        _date(hire_date, 'Дата прийняття'),
        _salary_cents(salary),
    )


def list_customers():
    with db_connection() as conn:
        rows = conn.execute('SELECT * FROM customers ORDER BY customer_id').fetchall()
        return [dict(r) for r in rows]


def get_customer(customer_id):
    with db_connection() as conn:
        row = conn.execute('SELECT * FROM customers WHERE customer_id=?', (customer_id,)).fetchone()
        return dict(row) if row else None


def add_customer(first_name, last_name, phone, email='', address='', registration_date=None):
    """Створює рядок клієнта. Майбутня реєстрація при замовленні викличе цю функцію."""
    payload = _customer_payload(first_name, last_name, phone, email, address, registration_date)
    with db_connection() as conn:
        customer_id = _new_id(conn, 'customer')
        conn.execute('''
            INSERT INTO customers (customer_id, first_name, last_name, phone,
                email, address, registration_date) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, *payload))
    return customer_id


def update_customer(customer_id, first_name, last_name, phone, email='', address='', registration_date=None):
    payload = _customer_payload(first_name, last_name, phone, email, address, registration_date)
    with db_connection() as conn:
        result = conn.execute('''
            UPDATE customers SET first_name=?, last_name=?, phone=?, email=?,
                address=?, registration_date=? WHERE customer_id=?
        ''', (*payload, customer_id))
        if result.rowcount == 0:
            raise ValueError('Користувача з таким ID не знайдено')


def delete_customer(customer_id):
    with db_connection() as conn:
        conn.execute('DELETE FROM customers WHERE customer_id=?', (customer_id,))


def list_employees():
    with db_connection() as conn:
        rows = conn.execute('SELECT * FROM employees ORDER BY employee_id').fetchall()
        return [dict(r) | {'salary': Decimal(r['salary_cents']) / 100} for r in rows]


def get_employee(employee_id):
    with db_connection() as conn:
        row = conn.execute('SELECT * FROM employees WHERE employee_id=?', (employee_id,)).fetchone()
        return dict(row) | {'salary': Decimal(row['salary_cents']) / 100} if row else None


def add_employee(first_name, last_name, position, phone, email='', hire_date=None, salary='0'):
    payload = _employee_payload(first_name, last_name, position, phone, email, hire_date, salary)
    with db_connection() as conn:
        employee_id = _new_id(conn, 'employee')
        conn.execute('''
            INSERT INTO employees (employee_id, first_name, last_name, position,
                phone, email, hire_date, salary_cents) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (employee_id, *payload))
    return employee_id


def update_employee(employee_id, first_name, last_name, position, phone, email='', hire_date=None, salary='0'):
    payload = _employee_payload(first_name, last_name, position, phone, email, hire_date, salary)
    with db_connection() as conn:
        result = conn.execute('''
            UPDATE employees SET first_name=?, last_name=?, position=?, phone=?,
                email=?, hire_date=?, salary_cents=? WHERE employee_id=?
        ''', (*payload, employee_id))
        if result.rowcount == 0:
            raise ValueError('Працівника з таким ID не знайдено')


def delete_employee(employee_id):
    with db_connection() as conn:
        conn.execute('DELETE FROM employees WHERE employee_id=?', (employee_id,))


def people_counts():
    with db_connection() as conn:
        return {
            'customers': conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0],
            'employees': conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0],
        }
