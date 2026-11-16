"""Адміністративний реєстр замовлень.

Гість/покупець тут не бачить чужі замовлення; кошик буде в іншому етапі.
"""
import sqlite3
from tkinter import messagebox
import customtkinter as ctk

from orders_db import list_orders,get_order,update_order_status,delete_order,ORDER_STATUSES
from ui.people_page import _ScrollTable
from ui.theme import COLORS,format_price


def render_orders_page(content,app,role):
    if role!='admin':
        ctk.CTkLabel(content,text='Оформлення замовлення та кошик будуть додані пізніше.',
            font=('Arial',14),text_color=COLORS['muted']).pack(anchor='w',padx=30,pady=20)
        ctk.CTkLabel(content,text='Тут не показуються замовлення інших клієнтів.',
            font=('Arial',12),text_color=COLORS['muted']).pack(anchor='w',padx=30)
        return

    filters=ctk.CTkFrame(content,fg_color='transparent')
    filters.pack(fill='x',padx=30,pady=(0,8))
    search=ctk.CTkEntry(filters,placeholder_text='Пошук за ID, клієнтом, телефоном, стравами...',height=36)
    search.pack(side='left',fill='x',expand=True,padx=(0,9))
    statuses=ctk.CTkOptionMenu(filters,values=['Усі стани']+ORDER_STATUSES,
        fg_color=COLORS['blue'],button_color=COLORS['navy'],width=165)
    statuses.pack(side='right');statuses.set('Усі стани')
    counter=ctk.CTkLabel(content,text='',text_color=COLORS['muted'],font=('Arial',12))
    counter.pack(anchor='w',padx=30,pady=(0,8))
    table=_ScrollTable(content)
    columns=[('ID',70),('ID клієнта',95),('Клієнт',175),('Тип клієнта',125),
             ('Телефон',135),('Дата',150),('Отримання',120),('Адреса',190),
             ('Сума',120),('Статус',145),('Оплата',105),('Склад замовлення',320),('Дії',360)]
    status_colors={'Нове':COLORS['status_blue'],'Готується':COLORS['orange'],
         'Доставляється':COLORS['orange'],'Виконане':COLORS['green'],'Скасоване':COLORS['red']}

    def open_order(order_id):
        try:order=get_order(order_id)
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка БД',str(exc),parent=app);return
        if not order:return
        dialog=ctk.CTkToplevel(app)
        dialog.title(f'Замовлення №{order_id}');dialog.geometry('570x650');dialog.minsize(490,510)
        dialog.transient(app)
        body=ctk.CTkScrollableFrame(dialog,fg_color='white')
        body.pack(fill='both',expand=True,padx=15,pady=15)
        ctk.CTkLabel(body,text=f'Замовлення №{order_id}',font=('Arial',20,'bold'),
            text_color=COLORS['navy']).pack(anchor='w',padx=16,pady=(12,12))
        details=[('Тип клієнта',order['customer_kind']),
            ('ID клієнта',order['customer_id'] or order['source_customer_id'] or 'Гість — немає акаунта'),
            ('Ім’я',order['customer_name']),('Телефон',order['phone']),
            ('Дата',order['order_date']),('Отримання',order['order_type']),
            ('Адреса',order['address'] or 'Самовивіз'),
            ('Спосіб оплати',order['payment_method']),
            ('Склад замовлення',order['order_list']),
            ('Сума',format_price(order['total']))]
        for label,value in details:
            row=ctk.CTkFrame(body,fg_color=COLORS['alt_row'])
            row.pack(fill='x',padx=12,pady=3)
            ctk.CTkLabel(row,text=label+':',width=145,text_color=COLORS['body_heading'],
                anchor='w').pack(side='left',padx=7,pady=7)
            ctk.CTkLabel(row,text=str(value),text_color=COLORS['navy'],
                anchor='w',justify='left',wraplength=330).pack(side='left',fill='x',expand=True,padx=4)
        if order['source']=='excel':
            ctk.CTkLabel(body,text='Імпорт з Excel. Сума збережена як в оригіналі.',
                text_color=COLORS['muted'],font=('Arial',11)).pack(anchor='w',padx=15,pady=8)
        ctk.CTkLabel(body,text='Статус замовлення',text_color=COLORS['navy'],
            font=('Arial',12,'bold')).pack(anchor='w',padx=16,pady=(10,4))
        status=ctk.CTkOptionMenu(body,values=ORDER_STATUSES,
            fg_color=COLORS['blue'],button_color=COLORS['navy'])
        status.pack(fill='x',padx=16)
        status.set(order['status'])
        feedback=ctk.CTkLabel(body,text='',text_color=COLORS['red'])
        feedback.pack(padx=16)
        def save():
            try:update_order_status(order_id,status.get())
            except (ValueError,sqlite3.Error) as exc:
                feedback.configure(text=str(exc));return
            dialog.destroy();refresh()
        ctk.CTkButton(body,text='Зберегти статус',fg_color=COLORS['blue'],
                      command=save).pack(pady=(8,16))
        dialog.grab_set()

    def confirm_delete(order_id):
        if not messagebox.askyesno(
            'Видалення замовлення',
            f'Видалити замовлення №{order_id} назавжди?\nЦю дію неможливо скасувати.',
            icon='warning', parent=app
        ):
            return
        try:
            delete_order(order_id)
        except (ValueError, sqlite3.Error) as exc:
            messagebox.showerror('Помилка видалення', str(exc), parent=app)
            return
        refresh()

    def refresh(*_):
        try:orders=list_orders()
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка БД',str(exc),parent=app);return
        query=search.get().strip().casefold()
        current=statuses.get()
        visible=[o for o in orders if
            (current=='Усі стани' or o['status']==current)
            and (not query or any(query in str(o.get(k) or '').casefold()
                for k in ['order_id','customer_id','source_customer_id','customer_name','phone','order_list','order_date','status',
                          'address','order_type','payment_method']))]
        counter.configure(text=f'Показано: {len(visible)} із {len(orders)} замовлень')
        table.clear()
        table.set_columns([width for _,width in columns])
        for i,(header,width) in enumerate(columns):
            w=ctk.CTkLabel(table.inner,text=header,height=39,width=1,
                fg_color=COLORS['header'],text_color=COLORS['body_heading'],
                font=('Arial',11,'bold'),anchor='center')
            w.grid(row=0,column=i,sticky='nsew',padx=2,pady=2);table.enable_wheel(w)
        if not visible:
            ctk.CTkLabel(table.inner,text='Замовлень не знайдено',
                text_color=COLORS['muted'],height=70).grid(row=1,column=0,columnspan=len(columns),sticky='ew')
        for idx,order in enumerate(visible,1):
            shade=COLORS['white'] if idx%2 else COLORS['alt_row']
            vals=[order['order_id'],order['customer_id'] or order['source_customer_id'] or '—',order['customer_name'],
                  order['customer_kind'],order['phone'],order['order_date'],
                  order['order_type'],order['address'] or '—',
                  format_price(order['total']),order['status'],order['payment_method'],
                  order['order_list']]
            for j,value in enumerate(vals):
                w=ctk.CTkLabel(table.inner,text=str(value),height=48,width=1,
                    fg_color=shade,text_color=(status_colors.get(value,COLORS['navy']) if j==9 else COLORS['navy']),
                    font=('Arial',11),anchor='center',justify='center',wraplength=columns[j][1]-10)
                w.grid(row=idx,column=j,sticky='nsew',padx=2,pady=2);table.enable_wheel(w)
            # Компактні дії без переповнення клітинки.
            # Відкриття деталей та зміна статусу залишаються в одному діалозі.
            cell=ctk.CTkFrame(table.inner,fg_color=shade,height=48)
            cell.grid(row=idx,column=len(columns)-1,sticky='nsew',padx=2,pady=2)
            cell.grid_propagate(False)
            buttons_row=ctk.CTkFrame(cell,fg_color='transparent')
            buttons_row.place(relx=0.5,rely=0.5,anchor='center')
            btn=ctk.CTkButton(buttons_row,text='Деталі / статус',width=145,height=30,
                font=('Arial',11),fg_color=COLORS['blue'],hover_color=COLORS['blue_hover'],
                command=lambda pk=order['order_id']:open_order(pk))
            btn.pack(side='left',padx=(0,6))
            delete_btn=ctk.CTkButton(buttons_row,text='Видалити',width=95,height=30,
                font=('Arial',11),fg_color=COLORS['red'],hover_color=COLORS['red'],
                command=lambda pk=order['order_id']:confirm_delete(pk))
            delete_btn.pack(side='left')
            for w in [cell,buttons_row,btn,delete_btn]:table.enable_wheel(w)
        table.inner.update_idletasks();table._resize_content()
    search.bind('<KeyRelease>',refresh)
    statuses.configure(command=refresh)
    refresh()
