"""Клієнтські картки меню, кошик, історія та профіль."""
import customtkinter as ctk
from tkinter import messagebox
from database import list_menu_catalog, get_menu_catalog_item
from orders_db import create_order
from people_db import get_customer
from ui.photos import load_thumbnail
from ui.theme import COLORS, MENU_CATEGORIES, format_price
from database import db_connection


def _label(parent, value, size=13, bold=False, color=None, **kwargs):
    return ctk.CTkLabel(parent, text=value,
        font=('Arial', size, 'bold' if bold else 'normal'),
        text_color=color or COLORS['navy'], **kwargs)


def render_client_menu(parent, app, cart, refresh_cart_badge):
    toolbar = ctk.CTkFrame(parent, fg_color='transparent')
    toolbar.pack(fill='x', padx=30, pady=(0, 12))
    _label(toolbar, 'Категорія:', 13).pack(side='left', padx=(0, 10))
    category = ctk.CTkOptionMenu(toolbar, values=['Усі категорії'] + MENU_CATEGORIES)
    category.pack(side='left')
    search = ctk.CTkEntry(toolbar, placeholder_text='Пошук страви', width=250)
    search.pack(side='right')

    frame = ctk.CTkScrollableFrame(parent, fg_color='transparent')
    frame.pack(fill='both', expand=True, padx=24, pady=(0, 20))
    photo_refs = []

    def redraw(*_):
        for child in frame.winfo_children():
            child.destroy()
        photo_refs.clear()
        q = search.get().strip().casefold()
        items = list_menu_catalog()
        items = [x for x in items if
                 (category.get() == 'Усі категорії' or x['category'] == category.get())
                 and q in x['name'].casefold()]
        if not items:
            _label(frame, 'Нічого не знайдено').pack(pady=30)
        for item in items:
            card = ctk.CTkFrame(frame, fg_color='white', corner_radius=12,
                                border_width=1, border_color=COLORS['light_border'])
            card.pack(fill='x', padx=5, pady=7)
            picture = ctk.CTkFrame(card, width=190, height=150,
                                   fg_color=COLORS['header'], corner_radius=8)
            picture.pack(side='left', padx=12, pady=12)
            picture.pack_propagate(False)
            photo = load_thumbnail(item.get('image_path'), (180, 140))
            if photo:
                photo_refs.append(photo)
                ctk.CTkLabel(picture, text='', image=photo).pack(expand=True)
            else:
                _label(picture, '🍕\nФото не додано', 15, color=COLORS['muted']).pack(expand=True)
            info = ctk.CTkFrame(card, fg_color='transparent')
            info.pack(side='left', fill='both', expand=True, padx=(0, 12), pady=12)
            _label(info, item['name'], 19, True).pack(anchor='w')
            _label(info, f"{item['category']}  ·  {format_price(item['price'])}", 14, True).pack(anchor='w', pady=(5, 0))
            weight = item.get('weight_g')
            _label(info, f"Вага: {weight} г" if weight else 'Вага: не вказана',
                   12, color=COLORS['muted']).pack(anchor='w', pady=(3, 0))
            recipe = item.get('recipe') or []
            parts = [f"{r['name']}" for r in recipe]
            _label(info, 'Склад: ' + (', '.join(parts) if parts else 'не вказано'),
                   12, color=COLORS['muted'], wraplength=430, justify='left').pack(anchor='w', pady=(4, 6))
            def add(item_id=item['id']):
                cart[item_id] = cart.get(item_id, 0) + 1
                refresh_cart_badge()
            ctk.CTkButton(info, text='Додати в кошик', width=165, command=add).pack(anchor='w')
    category.configure(command=redraw)
    search.bind('<KeyRelease>', redraw)
    redraw()


def render_cart(parent, app, cart, customer_id, after_order, refresh_cart_badge):
    wrap = ctk.CTkScrollableFrame(parent, fg_color='transparent')
    wrap.pack(fill='both', expand=True, padx=30, pady=(0, 15))
    total = 0
    valid = []
    for menu_id, quantity in list(cart.items()):
        item = get_menu_catalog_item(menu_id)
        if not item:
            cart.pop(menu_id, None)
            continue
        valid.append((menu_id, quantity))
        total += item['price'] * quantity
        row = ctk.CTkFrame(wrap, fg_color='white', corner_radius=10)
        row.pack(fill='x', pady=4)
        _label(row, item['name'], 14, True).pack(side='left', padx=12, pady=12)
        _label(row, f"{quantity} × {format_price(item['price'])}").pack(side='left', padx=10)
        def change(mid=menu_id, step=1):
            cart[mid] = cart.get(mid, 0) + step
            if cart[mid] <= 0:
                cart.pop(mid, None)
            refresh_cart_badge()
            after_order('Кошик')
        ctk.CTkButton(row, text='−', width=34, command=lambda mid=menu_id: change(mid,-1)).pack(side='right', padx=4)
        ctk.CTkButton(row, text='+', width=34, command=lambda mid=menu_id: change(mid,1)).pack(side='right', padx=4)
    _label(wrap, f'Разом: {format_price(total)}', 20, True).pack(anchor='e', pady=12)
    if not valid:
        _label(wrap, 'Кошик порожній').pack(anchor='w')
        return

    _label(wrap, 'Оформлення замовлення', 18, True).pack(anchor='w', pady=(8, 4))
    user = get_customer(customer_id) if customer_id else None
    def entry(placeholder, value=''):
        e = ctk.CTkEntry(wrap, placeholder_text=placeholder, height=36)
        e.pack(fill='x', pady=3)
        if value:
            e.insert(0, value)
        return e
    name = entry('Ім’я та прізвище', f"{user['first_name']} {user['last_name']}" if user else '')
    phone = entry('Телефон', user['phone'] if user else '')
    address = entry('Адреса доставки', user['address'] if user else '')
    kind = ctk.CTkOptionMenu(wrap, values=['Доставка', 'Самовивіз'])
    kind.pack(anchor='w', pady=5)
    payment = ctk.CTkOptionMenu(wrap, values=['Готівка', 'Картка'])
    payment.pack(anchor='w', pady=5)
    _label(wrap, 'Оплата карткою: спосіб фіксується, онлайн-оплата не підключена.',
           11, color=COLORS['muted']).pack(anchor='w')

    def submit():
        try:
            order_id = create_order(customer_id=customer_id,
                customer_name=name.get(), phone=phone.get(), address=address.get(),
                order_type=kind.get(), payment_method=payment.get(),
                items=list(cart.items()))
            cart.clear()
            refresh_cart_badge()
            messagebox.showinfo('Замовлення', f'Замовлення №{order_id} оформлено!')
            after_order('Історія замовлень' if customer_id else 'Меню')
        except Exception as exc:
            messagebox.showerror('Помилка', str(exc))
    ctk.CTkButton(wrap, text='Підтвердити замовлення', height=42, command=submit).pack(anchor='w', pady=14)


def render_history(parent, customer_id):
    wrap = ctk.CTkScrollableFrame(parent, fg_color='transparent')
    wrap.pack(fill='both', expand=True, padx=30, pady=(0, 20))
    if not customer_id:
        _label(wrap, 'Увійдіть до облікового запису, щоб бачити історію.').pack()
        return
    with db_connection() as conn:
        rows = conn.execute('SELECT * FROM orders WHERE customer_id=? ORDER BY order_date DESC, order_id DESC',
                            (customer_id,)).fetchall()
    if not rows:
        _label(wrap, 'Замовлень поки немає').pack()
    for r in rows:
        card = ctk.CTkFrame(wrap, fg_color='white')
        card.pack(fill='x', pady=5)
        _label(card, f"№{r['order_id']} · {r['order_date']} · {r['status']}",
               15, True).pack(anchor='w', padx=14, pady=(10, 2))
        _label(card, f"{r['order_list']} · {format_price(r['total_cents']/100)}",
               12, wraplength=650, justify='left').pack(anchor='w', padx=14, pady=(0, 10))


def render_account(parent, customer_id, on_login_change=None):
    from auth_db import get_account_login, update_account
    user = get_customer(customer_id) if customer_id else None
    if not user:
        _label(parent, 'Цей демонстраційний вхід не прив’язаний до клієнта.\n'
               'Зареєструйте власний акаунт, щоб редагувати дані.').pack(anchor='w', padx=30)
        return
    scroll = ctk.CTkScrollableFrame(parent, fg_color='transparent')
    scroll.pack(fill='both', expand=True, padx=30, pady=(0, 15))
    card = ctk.CTkFrame(scroll, fg_color='white', corner_radius=12)
    card.pack(fill='x', pady=8)
    _label(card, 'Особисті дані', 20, True).pack(anchor='w', padx=18, pady=(16, 8))
    _label(card, 'ID клієнта: ' + user['customer_id'], 12,
           color=COLORS['muted']).pack(anchor='w', padx=18)
    fields = {}
    for key, title, value in [
        ('login','Логін',get_account_login(customer_id) or ''),
        ('first_name','Ім’я',user['first_name']),
        ('last_name','Прізвище',user['last_name']),
        ('phone','Телефон',user['phone']),
        ('email','Email',user['email']),
        ('address','Адреса',user['address'])
    ]:
        _label(card, title, 12).pack(anchor='w', padx=18, pady=(7, 0))
        e = ctk.CTkEntry(card, height=36)
        e.pack(fill='x', padx=18, pady=(2, 3))
        e.insert(0, value or '')
        fields[key] = e
    _label(card, 'Зміна пароля (необов’язково)', 15, True).pack(
        anchor='w', padx=18, pady=(15, 4))
    _label(card, 'Для зміни логіна або пароля введіть поточний пароль.',
           11, color=COLORS['muted']).pack(anchor='w', padx=18)
    old = ctk.CTkEntry(card, show='*', placeholder_text='Поточний пароль', height=36)
    old.pack(fill='x', padx=18, pady=4)
    new = ctk.CTkEntry(card, show='*', placeholder_text='Новий пароль', height=36)
    new.pack(fill='x', padx=18, pady=4)
    confirm = ctk.CTkEntry(card, show='*', placeholder_text='Повторіть новий пароль', height=36)
    confirm.pack(fill='x', padx=18, pady=4)
    def save():
        if new.get() != confirm.get():
            messagebox.showerror('Помилка', 'Нові паролі не збігаються')
            return
        try:
            updated_login = update_account(customer_id, fields['login'].get(),
                fields['first_name'].get(), fields['last_name'].get(),
                fields['phone'].get(), fields['email'].get(), fields['address'].get(),
                old.get(), new.get())
        except Exception as exc:
            messagebox.showerror('Помилка збереження', str(exc))
            return
        if on_login_change:
            on_login_change(updated_login)
        old.delete(0, 'end'); new.delete(0, 'end'); confirm.delete(0, 'end')
        messagebox.showinfo('Акаунт', 'Зміни збережено в базі даних')
    ctk.CTkButton(card, text='Зберегти зміни', height=40,
                  command=save).pack(anchor='w', padx=18, pady=18)
