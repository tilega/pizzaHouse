"""Панель керування: показники із живих SQLite-таблиць, а не фіктивні числа."""
import sqlite3
from tkinter import messagebox
import customtkinter as ctk
from orders_db import order_dashboard_stats
from people_db import people_counts
from procurement_db import list_purchases
from ui.theme import COLORS, format_price


def render_home_page(content,app,role):
    if role!='admin':return
    try:
        orders=order_dashboard_stats()
        people=people_counts()
        purchases=list_purchases()
    except sqlite3.Error as exc:
        messagebox.showerror('Помилка БД',str(exc),parent=app);return
    cards=ctk.CTkFrame(content,fg_color='transparent')
    cards.pack(fill='x',padx=25,pady=(8,0))
    metrics=[('Нові замовлення',orders['new_orders'],COLORS['card_green']),
             ('Всього замовлень',orders['all_orders'],COLORS['card_blue']),
             ('Користувачі',people['customers'],COLORS['card_purple']),
             ('Працівники',people['employees'],COLORS['card_orange'])]
    # Карточки имеют фиксированную высоту: внутри используется pack(),
    # поэтому отключаем именно pack_propagate(), а не grid_propagate().
    cards.grid_rowconfigure(0, minsize=180)
    for i,(name,value,color) in enumerate(metrics):
        cards.grid_columnconfigure(i, weight=1, uniform='cards')
        card = ctk.CTkFrame(cards, fg_color=color, corner_radius=12, height=180)
        card.grid(row=0, column=i, padx=5, sticky='nsew')
        card.pack_propagate(False)

        # Центрируем надпись и число как единый блок, без ручной подгонки отступов.
        center = ctk.CTkFrame(card, fg_color='transparent')
        center.pack(expand=True)
        ctk.CTkLabel(center, text=name, font=('Arial',14),
                     text_color=COLORS['body_heading']).pack(pady=(0,8))
        ctk.CTkLabel(center, text=str(value), font=('Arial',39,'bold'),
                     text_color=COLORS['navy']).pack()
    notes=ctk.CTkLabel(content,text=f"Гостьових замовлень: {orders['guest_orders']}   •   Закупівель: {len(purchases)}",
        font=('Arial',12),text_color=COLORS['muted'])
    notes.pack(anchor='w',padx=31,pady=(14,0))
    box=ctk.CTkFrame(content,fg_color='white',corner_radius=10,
        border_width=1,border_color=COLORS['light_border'])
    box.pack(fill='both',expand=True,padx=30,pady=(18,20))
    ctk.CTkLabel(box,text='Останні замовлення',font=('Arial',17,'bold'),
        text_color=COLORS['navy']).pack(anchor='w',padx=15,pady=(15,11))
    table=ctk.CTkScrollableFrame(box,fg_color='transparent',height=320,
        scrollbar_button_color=COLORS['muted'])
    table.pack(fill='both',expand=True,padx=15,pady=(0,15))
    headers=['ID','Клієнт','Тип','Дата','Сума','Статус']
    for i,heading in enumerate(headers):
        table.grid_columnconfigure(i,weight=1,uniform='order-columns')
        ctk.CTkLabel(table,text=heading,font=('Arial',11,'bold'),height=36,
           fg_color=COLORS['header'],text_color=COLORS['body_heading'],anchor='center',
           width=1).grid(row=0,column=i,sticky='nsew',padx=2,pady=2)
    if not orders['recent']:
        ctk.CTkLabel(table,text='Замовлень ще немає',height=50,
            text_color=COLORS['muted']).grid(row=1,column=0,columnspan=len(headers))
    for row,order in enumerate(orders['recent'],1):
        values=[order['order_id'],order['customer_name'],order['customer_kind'],
                order['order_date'],format_price(order['total']),order['status']]
        bg=COLORS['white'] if row%2 else COLORS['alt_row']
        for col,value in enumerate(values):
            ctk.CTkLabel(table,text=str(value),height=40,width=1,font=('Arial',11),
                fg_color=bg,text_color=COLORS['navy'],anchor='center',
                wraplength=125).grid(row=row,column=col,sticky='nsew',padx=2,pady=2)
