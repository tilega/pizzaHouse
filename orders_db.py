"""Замовлення: зареєстрований клієнт за customer_id або гість (NULL).

Початкові 10 замовлень з Excel зберігаються в оригінальному вигляді.
Для майбутнього кошика є create_order із нормалізованими order_lines.
"""
from datetime import datetime
from decimal import Decimal
import re
from database import db_connection

ORDER_STATUSES = ['Нове', 'Готується', 'Доставляється', 'Виконане', 'Скасоване']
ORDER_TYPES = ['Доставка', 'Самовивіз']
PAYMENT_TYPES = ['Картка', 'Готівка']

STARTER_ORDERS = [{'order_id': 101,
  'customer_id': 'C1042',
  'customer_name': 'Анна Коваленко',
  'phone': '0501234567',
  'order_date': '2026-10-19 12:15:00',
  'order_type': 'Доставка',
  'address': 'вул. Шевченка, 12',
  'total_cents': 56000,
  'status': 'Виконане',
  'payment_method': 'Картка',
  'order_list': 'Маргарита × 2, Coca-Cola × 2'},
 {'order_id': 102,
  'customer_id': 'C2087',
  'customer_name': 'Максим Бондаренко',
  'phone': '0672345678',
  'order_date': '2026-10-19 12:30:00',
  'order_type': 'Самовивіз',
  'address': '',
  'total_cents': 28000,
  'status': 'Виконане',
  'payment_method': 'Готівка',
  'order_list': 'Пепероні × 1'},
 {'order_id': 103,
  'customer_id': 'C3156',
  'customer_name': 'Софія Мельник',
  'phone': '0933456789',
  'order_date': '2026-10-19 13:05:00',
  'order_type': 'Доставка',
  'address': 'вул. Франка, 25',
  'total_cents': 39000,
  'status': 'Доставляється',
  'payment_method': 'Картка',
  'order_list': 'Чотири сири × 1, Часниковий соус × 1, Sprite × 1'},
 {'order_id': 104,
  'customer_id': 'C4271',
  'customer_name': 'Артем Шевченко',
  'phone': '0954567890',
  'order_date': '2026-10-19 13:20:00',
  'order_type': 'Самовивіз',
  'address': '',
  'total_cents': 37000,
  'status': 'Готується',
  'payment_method': 'Готівка',
  'order_list': 'Гавайська × 1, Coca-Cola × 1'},
 {'order_id': 105,
  'customer_id': 'C5368',
  'customer_name': 'Марія Ткаченко',
  'phone': '0635678901',
  'order_date': '2026-10-19 14:00:00',
  'order_type': 'Доставка',
  'address': 'вул. Садова, 8',
  'total_cents': 68000,
  'status': 'Нове',
  'payment_method': 'Картка',
  'order_list': "М'ясна × 2, Картопля фрі × 1"},
 {'order_id': 106,
  'customer_id': 'C6429',
  'customer_name': 'Дмитро Кравченко',
  'phone': '0996789012',
  'order_date': '2026-10-19 14:15:00',
  'order_type': 'Доставка',
  'address': 'вул. Центральна, 41',
  'total_cents': 32000,
  'status': 'Виконане',
  'payment_method': 'Готівка',
  'order_list': 'BBQ Chicken × 1, Coca-Cola × 1'},
 {'order_id': 107,
  'customer_id': 'C7513',
  'customer_name': 'Ольга Лисенко',
  'phone': '0977890123',
  'order_date': '2026-10-19 15:10:00',
  'order_type': 'Самовивіз',
  'address': '',
  'total_cents': 25000,
  'status': 'Виконане',
  'payment_method': 'Картка',
  'order_list': 'Кальцоне × 1'},
 {'order_id': 108,
  'customer_id': 'C8645',
  'customer_name': 'Владислав Поліщук',
  'phone': '0668901234',
  'order_date': '2026-10-19 16:25:00',
  'order_type': 'Доставка',
  'address': 'вул. Молодіжна, 17',
  'total_cents': 51000,
  'status': 'Готується',
  'payment_method': 'Картка',
  'order_list': 'Пепероні × 1, Чотири сири × 1'},
 {'order_id': 109,
  'customer_id': None,
  'customer_name': 'Ірина Савченко',
  'phone': '0989012345',
  'order_date': '2026-10-19 17:00:00',
  'order_type': 'Доставка',
  'address': 'вул. Миру, 33',
  'total_cents': 45000,
  'status': 'Скасоване',
  'payment_method': 'Готівка',
  'order_list': 'Маргарита × 1, Лимонад × 1'},
 {'order_id': 110,
  'customer_id': 'C9732',
  'customer_name': 'Назар Романенко',
  'phone': '0500123456',
  'order_date': '2026-10-19 18:40:00',
  'order_type': 'Самовивіз',
  'address': '',
  'total_cents': 62000,
  'status': 'Нове',
  'payment_method': 'Картка',
  'order_list': "М'ясна × 1, Гавайська × 1"}]


def initialize_orders_database():
    with db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT REFERENCES customers(customer_id) ON DELETE RESTRICT,
            source_customer_id TEXT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            order_date TEXT NOT NULL,
            order_type TEXT NOT NULL,
            address TEXT NOT NULL DEFAULT '',
            total_cents INTEGER NOT NULL CHECK(total_cents >= 0),
            status TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            order_list TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT 'app'
        )''')
        cols = {r['name'] for r in conn.execute('PRAGMA table_info(orders)')}
        if 'source_customer_id' not in cols:
            conn.execute('ALTER TABLE orders ADD COLUMN source_customer_id TEXT')
            conn.execute('UPDATE orders SET source_customer_id=customer_id WHERE customer_id IS NOT NULL')
        conn.execute('''CREATE TABLE IF NOT EXISTS order_lines (
            order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
            line_number INTEGER NOT NULL,
            menu_id INTEGER REFERENCES menu_items(id) ON DELETE SET NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price_cents INTEGER CHECK(unit_price_cents >= 0),
            PRIMARY KEY(order_id,line_number)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        )''')
        mark='orders_excel_2026_v1'
        if conn.execute('SELECT 1 FROM app_meta WHERE key=?',(mark,)).fetchone() is None:
            if conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0] == 0:
                for order in STARTER_ORDERS:
                    # Зберігаємо Excel-суми без перерахунку: вони не завжди
                    # відповідають поточним цінам меню (історичні дані).
                    ref = order['customer_id']
                    linked = (ref if ref and conn.execute(
                        'SELECT 1 FROM customers WHERE customer_id=?',(ref,)).fetchone() else None)
                    conn.execute('''INSERT INTO orders (order_id,customer_id,source_customer_id,
                        customer_name,phone,order_date,order_type,address,total_cents,
                        status,payment_method,order_list,source)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (order['order_id'],linked,ref,order['customer_name'],
                         order['phone'],order['order_date'],order['order_type'],
                         order['address'],order['total_cents'],order['status'],
                         order['payment_method'],order['order_list'],'excel'))
                    for line_i,piece in enumerate(order['order_list'].split(', '),1):
                        matched=re.fullmatch(r'(.+?)\s*[×x]\s*(\d+)',piece.strip())
                        name=matched.group(1).strip() if matched else piece.strip()
                        qty=int(matched.group(2)) if matched else 1
                        menu=conn.execute('SELECT id FROM menu_items WHERE name_key=?',
                                          (name.casefold(),)).fetchone()
                        conn.execute('''INSERT INTO order_lines
                            (order_id,line_number,menu_id,item_name,quantity,unit_price_cents)
                            VALUES(?,?,?,?,?,NULL)''',
                            (order['order_id'],line_i,menu['id'] if menu else None,name,qty))
            conn.execute('INSERT INTO app_meta(key,value) VALUES(?,?)',(mark,'done'))


def _order_from_row(row):
    result=dict(row)
    result['total']=Decimal(result['total_cents'])/100
    result['customer_kind']='Зареєстрований' if (result['customer_id'] or result['source_customer_id']) else 'Гість'
    return result


def list_orders():
    with db_connection() as conn:
        return [_order_from_row(r) for r in conn.execute(
            'SELECT * FROM orders ORDER BY order_date DESC,order_id DESC')]


def get_order(order_id):
    with db_connection() as conn:
        row=conn.execute('SELECT * FROM orders WHERE order_id=?',(order_id,)).fetchone()
        if not row:return None
        result=_order_from_row(row)
        result['lines']=[dict(r) for r in conn.execute(
            'SELECT * FROM order_lines WHERE order_id=? ORDER BY line_number',(order_id,))]
        return result


def update_order_status(order_id,status):
    if status not in ORDER_STATUSES: raise ValueError('Невідомий статус замовлення')
    with db_connection() as conn:
        r=conn.execute('UPDATE orders SET status=? WHERE order_id=?',(status,order_id))
        if not r.rowcount: raise ValueError('Замовлення не знайдено')



def delete_order(order_id):
    """Видаляє замовлення та його рядки однією транзакцією."""
    with db_connection() as conn:
        conn.execute('DELETE FROM order_lines WHERE order_id=?', (order_id,))
        result = conn.execute('DELETE FROM orders WHERE order_id=?', (order_id,))
        if not result.rowcount:
            raise ValueError('Замовлення не знайдено')


def _required(value,label):
    value=str(value or '').strip()
    if not value:raise ValueError(f'Заповніть поле «{label}»')
    if len(value)>200:raise ValueError(f'Занадто довге поле «{label}»')
    return value


def create_order(*,customer_id=None,customer_name='',phone='',order_type='Доставка',
                 address='',payment_method='Картка',items=()):
    """Майбутній кошик викликатиме цей метод для гостей і зареєстрованих.

    items — послідовність (menu_id, quantity). Сума береться з БД, не з форми.
    Поки НЕ списує інгредієнти: резервування/списання — окремий етап.
    """
    if order_type not in ORDER_TYPES or payment_method not in PAYMENT_TYPES:
        raise ValueError('Некоректний спосіб доставки або оплати')
    if not items:raise ValueError('Кошик порожній')
    if len(items)>100:raise ValueError('У кошику забагато позицій')
    with db_connection() as conn:
        if customer_id:
            user=conn.execute('SELECT * FROM customers WHERE customer_id=?',(customer_id,)).fetchone()
            if user is None:raise ValueError('Користувача не знайдено')
            customer_name=f"{user['first_name']} {user['last_name']}"
            phone=phone or user['phone']
            address=address or user['address']
        customer_name=_required(customer_name,'Ім’я клієнта')
        phone=_required(phone,'Телефон')
        if order_type=='Доставка':address=_required(address,'Адреса')
        else:address=''
        lines=[]; total=0
        for menu_id,qty in items:
            try:qty=int(qty);menu_id=int(menu_id)
            except (ValueError,TypeError) as exc:raise ValueError('Невірна позиція кошика') from exc
            if qty<1 or qty>100:raise ValueError('Кількість має бути від 1 до 100')
            item=conn.execute('SELECT id,name,price_cents FROM menu_items WHERE id=?',(menu_id,)).fetchone()
            if not item:raise ValueError('Позиція меню не знайдена')
            lines.append((menu_id,item['name'],qty,item['price_cents']))
            total+=qty*item['price_cents']
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        list_text=', '.join(f'{name} × {qty}' for _,name,qty,_ in lines)
        cur=conn.execute('''INSERT INTO orders
            (customer_id,source_customer_id,customer_name,phone,order_date,order_type,address,total_cents,
             status,payment_method,order_list,source)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
            (customer_id,customer_id,customer_name,phone,now,order_type,address,total,
             'Нове',payment_method,list_text,'app'))
        order_id=cur.lastrowid
        conn.executemany('''INSERT INTO order_lines
            (order_id,line_number,menu_id,item_name,quantity,unit_price_cents)
            VALUES(?,?,?,?,?,?)''',
            [(order_id,i,mi,name,qty,price) for i,(mi,name,qty,price) in enumerate(lines,1)])
        return order_id


def order_dashboard_stats():
    with db_connection() as conn:
        summary=conn.execute('''SELECT COUNT(*) AS all_orders,
            SUM(CASE WHEN status='Нове' THEN 1 ELSE 0 END) AS new_orders,
            SUM(CASE WHEN customer_id IS NULL AND source_customer_id IS NULL THEN 1 ELSE 0 END) AS guest_orders
            FROM orders''').fetchone()
        rows=conn.execute('''SELECT * FROM orders
            ORDER BY order_date DESC, order_id DESC LIMIT 10''').fetchall()
        return {'all_orders':summary['all_orders'] or 0,
                'new_orders':summary['new_orders'] or 0,
                'guest_orders':summary['guest_orders'] or 0,
                'recent':[_order_from_row(r) for r in rows]}
