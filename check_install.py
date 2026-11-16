"""Перевіряє файли та навігацію версії 3.0, нічого не змінюючи у БД."""
from pathlib import Path
from sys import version
root=Path(__file__).resolve().parent
expected=[
    'pizzaHouse.py','database.py','people_db.py','procurement_db.py','orders_db.py',
    'ui/app.py','ui/menu_page.py','ui/ingredients_page.py','ui/people_page.py',
    'ui/procurement_page.py','ui/orders_page.py','ui/home_page.py',
    'ui/photos.py','ui/theme.py','requirements.txt',
]
print('Python:',version.split()[0])
print('Папка програми:',root)
missing=[]
for name in expected:
    found=(root/name).is_file()
    print(('OK  ' if found else 'НЕТ ')+name)
    if not found:missing.append(name)
app=root/'ui/app.py'
if app.exists():
    source=app.read_text(encoding='utf8')
    checks={
        'версія 3.0':'Оновлення 3.0' in source,
        'кнопка закупівель':'render_procurement_page(content, app, current_role)' in source,
        'кнопка замовлень':'render_orders_page(content, app, current_role)' in source,
        'панель Головна':'render_home_page(content, app, current_role)' in source,
        'запуск БД закупівель':'initialize_procurement_database()' in source,
        'запуск БД замовлень':'initialize_orders_database()' in source,
    }
    for label,okay in checks.items():
        print(('OK  ' if okay else 'НЕТ ')+label)
    if not all(checks.values()):missing.append('підключення ui/app.py')
print('БД НЕ змінювалася цим скриптом.')
print('РЕЗУЛЬТАТ:', 'OK — все на місці' if not missing else 'НЕ ВСЕ ВСТАНОВЛЕНО')
