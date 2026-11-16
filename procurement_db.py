"""Постачальники та фактичні закупівлі: всі зміни залишків атомарні.

Залишки у таблиці ingredients у тисячних одиницях (кг/л/шт), суми в копійках.
Ідентифікатори закупівель P3001.., постачальників S2001..
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
import sqlite3

from database import db_connection, _quantity_to_milli, _price_to_cents


STARTER_SUPPLIERS = [
    ('S2001', 'ТОВ «Млин-Сервіс»', '0501112233', 'м. Київ, вул. Промислова, 10', 'mlin@example.com'),
    ('S2002', 'ТОВ «Молочний Світ»', '0672223344', 'м. Київ, вул. Молочна, 15', 'milk@example.com'),
    ('S2003', 'ТОВ «Фуд-Постач»', '0933334455', 'м. Київ, вул. Складська, 20', 'foodpost@example.com'),
    ('S2004', "ТОВ «М'ясна Лавка»", '0954445566', "м. Київ, вул. М'ясна, 5", 'meat@example.com'),
    ('S2005', 'ТОВ «Фермер Продукт»', '0635556677', 'м. Київ, вул. Фермерська, 8', 'farmer@example.com'),
    ('S2006', 'ТОВ «Напої-Плюс»', '0996667788', 'м. Київ, вул. Торгова, 12', 'drinks@example.com'),
]


def initialize_procurement_database():
    with db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY, name TEXT NOT NULL,
            phone TEXT NOT NULL DEFAULT '', address TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL DEFAULT ''
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS purchases (
            purchase_id TEXT PRIMARY KEY,
            supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
            purchase_date TEXT NOT NULL, note TEXT NOT NULL DEFAULT ''
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS purchase_lines (
            purchase_id TEXT NOT NULL REFERENCES purchases(purchase_id) ON DELETE CASCADE,
            ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE RESTRICT,
            quantity_milli INTEGER NOT NULL CHECK(quantity_milli > 0),
            unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents > 0),
            PRIMARY KEY (purchase_id, ingredient_id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS procurement_sequences (
            kind TEXT PRIMARY KEY, next_number INTEGER NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS app_meta (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        )''')
        mark = 'suppliers_excel_v1'
        if conn.execute('SELECT 1 FROM app_meta WHERE key=?',(mark,)).fetchone() is None:
            if conn.execute('SELECT COUNT(*) FROM suppliers').fetchone()[0] == 0:
                conn.executemany('''INSERT INTO suppliers (supplier_id,name,phone,address,email)
                    VALUES (?,?,?,?,?)''', STARTER_SUPPLIERS)
            conn.execute('INSERT INTO app_meta (key,value) VALUES (?,?)', (mark,'done'))
        for kind,prefix,table,field,minimum in [
            ('supplier','S','suppliers','supplier_id',2001),
            ('purchase','P','purchases','purchase_id',3001),
        ]:
            highest = max((int(r[0][1:]) for r in conn.execute(
                f'SELECT {field} FROM {table}').fetchall()
                if re.fullmatch(rf'{prefix}\d+',r[0])), default=minimum - 1)
            next_number = max(highest + 1, minimum)
            conn.execute('''INSERT INTO procurement_sequences(kind,next_number)
                VALUES(?,?) ON CONFLICT(kind) DO UPDATE SET
                next_number = MAX(next_number,excluded.next_number)''', (kind,next_number))


def _next_id(conn, kind):
    prefix = {'supplier':'S','purchase':'P'}[kind]
    row = conn.execute('SELECT next_number FROM procurement_sequences WHERE kind=?',(kind,)).fetchone()
    if not row:
        raise RuntimeError('Не ініціалізовано лічильники ID')
    conn.execute('UPDATE procurement_sequences SET next_number=? WHERE kind=?', (row[0]+1,kind))
    return f'{prefix}{row[0]:04d}'


def _name(value,label,required=True,length=150):
    value=str(value or '').strip()
    if (required and not value) or len(value)>length:
        raise ValueError(f'Некоректне поле «{label}»')
    return value


def _supplier_fields(name, phone, address, email):
    name = _name(name,'Назва')
    phone = _name(phone,'Телефон',required=False,length=40)
    if phone and not re.fullmatch(r'\+?[0-9\s()\-]{9,25}',phone):
        raise ValueError('Некоректний номер телефону')
    address=_name(address,'Адреса',required=False,length=250)
    email=_name(email,'Email',required=False,length=150)
    if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
        raise ValueError('Некоректний email')
    return (name,phone,address,email)


def list_suppliers():
    with db_connection() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM suppliers ORDER BY supplier_id')]


def get_supplier(supplier_id):
    with db_connection() as conn:
        row=conn.execute('SELECT * FROM suppliers WHERE supplier_id=?',(supplier_id,)).fetchone()
        return dict(row) if row else None


def add_supplier(name,phone='',address='',email=''):
    payload=_supplier_fields(name,phone,address,email)
    with db_connection() as conn:
        supplier_id=_next_id(conn,'supplier')
        conn.execute('INSERT INTO suppliers VALUES(?,?,?,?,?)',(supplier_id,*payload))
        return supplier_id


def update_supplier(supplier_id,name,phone='',address='',email=''):
    payload=_supplier_fields(name,phone,address,email)
    with db_connection() as conn:
        result=conn.execute('''UPDATE suppliers SET name=?,phone=?,address=?,email=?
            WHERE supplier_id=?''',(*payload,supplier_id))
        if not result.rowcount: raise ValueError('Постачальника не знайдено')


def delete_supplier(supplier_id):
    with db_connection() as conn:
        conn.execute('DELETE FROM suppliers WHERE supplier_id=?',(supplier_id,))


def _valid_date(raw):
    if not raw: raw=date.today().isoformat()
    try: return date.fromisoformat(str(raw).strip()).isoformat()
    except ValueError as exc: raise ValueError('Дата повинна бути РРРР-ММ-ДД') from exc


def _purchase_lines(conn, lines):
    if not lines:
        raise ValueError('Додайте хоча б один інгредієнт до закупівлі')
    if len(lines)>100:
        raise ValueError('Забагато позицій у закупівлі')
    seen=set(); result=[]
    for ingredient_id,quantity,price in lines:
        try: ing_id=int(ingredient_id)
        except (ValueError,TypeError) as exc: raise ValueError('Некоректний інгредієнт') from exc
        if ing_id in seen: raise ValueError('Один інгредієнт двічі в закупівлі')
        seen.add(ing_id)
        ing=conn.execute('SELECT id,unit FROM ingredients WHERE id=?',(ing_id,)).fetchone()
        if not ing: raise ValueError('Інгредієнт відсутній у базі')
        qty=_quantity_to_milli(str(quantity).replace(',','.'),ing['unit'])
        if qty<=0: raise ValueError('Кількість має бути більшою за нуль')
        cents=_price_to_cents(str(price).replace(',','.'))
        result.append((ing_id,qty,cents))
    return result


def _apply_stock_diff(conn, before, after):
    old={ing_id:qty for ing_id,qty,_ in before}
    new={ing_id:qty for ing_id,qty,_ in after}
    for ing_id in set(old)|set(new):
        delta=new.get(ing_id,0)-old.get(ing_id,0)
        if not delta: continue
        updated=conn.execute('''UPDATE ingredients
            SET stock_milli=stock_milli+? WHERE id=? AND stock_milli+? >= 0''',
            (delta,ing_id,delta))
        if not updated.rowcount:
            raise ValueError('Недостатньо залишку для скасування або зміни закупівлі')


def _get_lines(conn,purchase_id):
    return [(r['ingredient_id'],r['quantity_milli'],r['unit_price_cents'])
        for r in conn.execute('SELECT * FROM purchase_lines WHERE purchase_id=?',(purchase_id,))]


def save_purchase(purchase_id,supplier_id,purchase_date,lines,note=''):
    """Create or update: updates stock by net delta in same transaction."""
    purchase_date=_valid_date(purchase_date)
    note=_name(note,'Примітка',False,500)
    with db_connection() as conn:
        if not conn.execute('SELECT 1 FROM suppliers WHERE supplier_id=?',(supplier_id,)).fetchone():
            raise ValueError('Оберіть постачальника зі списку')
        prepared=_purchase_lines(conn,lines)
        if purchase_id is None:
            purchase_id=_next_id(conn,'purchase')
            conn.execute('INSERT INTO purchases VALUES(?,?,?,?)',
                         (purchase_id,supplier_id,purchase_date,note))
            previous=[]
        else:
            if not conn.execute('SELECT 1 FROM purchases WHERE purchase_id=?',(purchase_id,)).fetchone():
                raise ValueError('Закупівлю не знайдено')
            previous=_get_lines(conn,purchase_id)
            conn.execute('UPDATE purchases SET supplier_id=?,purchase_date=?,note=? WHERE purchase_id=?',
                         (supplier_id,purchase_date,note,purchase_id))
        _apply_stock_diff(conn,previous,prepared)
        conn.execute('DELETE FROM purchase_lines WHERE purchase_id=?',(purchase_id,))
        conn.executemany('''INSERT INTO purchase_lines
            (purchase_id,ingredient_id,quantity_milli,unit_price_cents) VALUES (?,?,?,?)''',
            [(purchase_id,*line) for line in prepared])
        return purchase_id


def delete_purchase(purchase_id):
    with db_connection() as conn:
        if not conn.execute('SELECT 1 FROM purchases WHERE purchase_id=?',(purchase_id,)).fetchone():
            return
        _apply_stock_diff(conn,_get_lines(conn,purchase_id),[])
        conn.execute('DELETE FROM purchases WHERE purchase_id=?',(purchase_id,))


def list_purchases():
    with db_connection() as conn:
        rows=conn.execute('''SELECT p.purchase_id,p.purchase_date,p.note,
            p.supplier_id,s.name AS supplier_name,
            COALESCE(SUM(pl.quantity_milli*pl.unit_price_cents),0) AS total_milli_cents,
            COUNT(pl.ingredient_id) AS lines_count,
            COALESCE(GROUP_CONCAT(i.name, ', '),'') AS ingredients
            FROM purchases p JOIN suppliers s ON s.supplier_id=p.supplier_id
            LEFT JOIN purchase_lines pl ON pl.purchase_id=p.purchase_id
            LEFT JOIN ingredients i ON i.id=pl.ingredient_id
            GROUP BY p.purchase_id ORDER BY p.purchase_date DESC,p.purchase_id DESC''').fetchall()
        return [dict(r) | {'total':Decimal(r['total_milli_cents'])/100000} for r in rows]


def get_purchase(purchase_id):
    with db_connection() as conn:
        row=conn.execute('''SELECT p.*,s.name AS supplier_name FROM purchases p
            JOIN suppliers s ON p.supplier_id=s.supplier_id WHERE p.purchase_id=?''',
            (purchase_id,)).fetchone()
        if not row: return None
        result=dict(row); result['lines']=[]
        for li in conn.execute('''SELECT pl.*,i.name AS ingredient_name,i.unit
            FROM purchase_lines pl JOIN ingredients i ON i.id=pl.ingredient_id
            WHERE purchase_id=? ORDER BY i.name''',(purchase_id,)):
            result['lines'].append(dict(li) | {
                'quantity':Decimal(li['quantity_milli'])/1000,
                'unit_price':Decimal(li['unit_price_cents'])/100})
        result['total']=sum((line['quantity']*line['unit_price'] for line in result['lines']),Decimal(0))
        return result
