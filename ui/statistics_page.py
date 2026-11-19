"""Статистика замовлень для адміністратора та модератора."""
import sqlite3
from tkinter import messagebox
import customtkinter as ctk
from statistics_db import get_statistics
from ui.theme import COLORS, format_price

PERIODS = {'Увесь час': None, 'Останні 7 днів': 7, 'Останні 30 днів': 30}


def _label(parent, text, size=13, bold=False, color=None, **kwargs):
    return ctk.CTkLabel(parent, text=text, font=('Arial', size, 'bold' if bold else 'normal'),
                        text_color=color or COLORS['navy'], **kwargs)


def _section(parent, title):
    card = ctk.CTkFrame(parent, fg_color='white', corner_radius=12,
                        border_width=1, border_color=COLORS['light_border'])
    card.pack(fill='x', padx=4, pady=9)
    _label(card, title, 17, True).pack(anchor='w', padx=18, pady=(15, 8))
    body = ctk.CTkFrame(card, fg_color='transparent')
    body.pack(fill='x', padx=18, pady=(0, 16))
    return body


def _bars(parent, rows, label_key, value_key, suffix='', limit=10):
    rows = list(rows)[:limit]
    if not rows:
        _label(parent, 'За обраний період даних немає', color=COLORS['muted']).pack(anchor='w', pady=10)
        return
    highest = max((int(row[value_key]) for row in rows), default=1) or 1
    for row in rows:
        value = int(row[value_key])
        line = ctk.CTkFrame(parent, fg_color='transparent')
        line.pack(fill='x', pady=5)
        _label(line, str(row[label_key]), 12, width=190, anchor='w',
               wraplength=185).pack(side='left')
        track = ctk.CTkFrame(line, height=18, fg_color=COLORS['header'], corner_radius=5)
        track.pack(side='left', fill='x', expand=True, padx=(8, 10))
        track.pack_propagate(False)
        # Відносна довжина; ширина перераховується при зміні розміру вікна.
        fill = ctk.CTkFrame(track, height=18, fg_color=COLORS['blue'], corner_radius=5)
        fill.place(relx=0, rely=0, relwidth=max(.015, value / highest), relheight=1)
        _label(line, f'{value}{suffix}', 12, True, width=70, anchor='e').pack(side='right')


def render_statistics_page(content, app, role):
    if role not in ('admin', 'moderator'):
        return
    controls = ctk.CTkFrame(content, fg_color='transparent')
    controls.pack(fill='x', padx=30, pady=(2, 10))
    _label(controls, 'Період:', 13).pack(side='left', padx=(0, 8))
    selector = ctk.CTkOptionMenu(controls, fg_color=COLORS["navy"], button_color=COLORS["navy"], button_hover_color=COLORS["blue"], text_color="white", dropdown_fg_color=COLORS["navy"], dropdown_hover_color=COLORS["blue"], dropdown_text_color="white", values=list(PERIODS), width=190)
    selector.pack(side='left')
    ctk.CTkButton(controls, fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='Оновити', width=100,
                  command=lambda: draw()).pack(side='right')
    view = ctk.CTkScrollableFrame(content, fg_color='transparent')
    view.pack(fill='both', expand=True, padx=26, pady=(0, 14))

    def draw(*_):
        for child in view.winfo_children():
            child.destroy()
        try:
            data = get_statistics(PERIODS[selector.get()])
        except sqlite3.Error as exc:
            messagebox.showerror('Статистика', str(exc), parent=app)
            return
        metrics = [
            ('Усього замовлень', str(data['count']), COLORS['card_blue']),
            ('Виконано', str(data['completed']), COLORS['card_green']),
            ('Виручка (виконані)', format_price(data['revenue_cents']/100), COLORS['card_purple']),
            ('Середній чек', format_price(data['average_cents']/100), COLORS['card_orange']),
        ]
        grid = ctk.CTkFrame(view, fg_color='transparent')
        grid.pack(fill='x', padx=4, pady=(4, 12))
        for i, (title, value, color) in enumerate(metrics):
            grid.grid_columnconfigure(i, weight=1, uniform='stats')
            box = ctk.CTkFrame(grid, fg_color=color, height=115, corner_radius=10)
            box.grid(row=0, column=i, sticky='nsew', padx=5)
            box.pack_propagate(False)
            _label(box, title, 12, color=COLORS['body_heading'],
                   wraplength=180).pack(pady=(20, 8))
            _label(box, value, 20, True).pack()
        top = _section(view, 'Найпопулярніші товари · кількість порцій')
        _bars(top, data['top'], 'name', 'qty')
        _label(top, 'Скасовані замовлення не враховуються. Дані — з позицій замовлень.',
               11, color=COLORS['muted']).pack(anchor='w', pady=(8, 0))
        daily = _section(view, 'Замовлення за датами · останні 14 дат з даними')
        _bars(daily, data['daily'], 'day', 'qty', limit=14)
        statuses = _section(view, 'Замовлення за статусами')
        _bars(statuses, data['statuses'], 'status', 'qty')
        types = _section(view, 'Доставка чи самовивіз')
        _bars(types, data['kinds'], 'order_type', 'qty')
        _label(view, 'Виручка та середній чек розраховані лише за виконаними замовленнями. '
               'Початкові замовлення з Excel теж включені в статистику.',
               11, color=COLORS['muted'], wraplength=750, justify='left').pack(anchor='w', padx=10, pady=10)

    selector.configure(command=draw)
    draw()
