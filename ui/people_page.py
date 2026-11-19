"""Спільний інтерфейс адміністратора для «Користувачі» та «Працівники».

Кожен розділ використовує окрему SQLite-таблицю; форма редагує всі
поля, а таблична частина має горизонтальну та вертикальну прокрутку.
"""
import sqlite3
import tkinter as tk
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from people_db import (
    list_customers, get_customer, add_customer, update_customer, delete_customer,
    list_employees, get_employee, add_employee, update_employee, delete_employee,
)
from ui.theme import COLORS


CUSTOMER_FIELDS = [
    ('first_name', 'Ім’я'),
    ('last_name', 'Прізвище'),
    ('phone', 'Телефон'),
    ('email', 'Email'),
    ('address', 'Адреса'),
    ('registration_date', 'Дата реєстрації (РРРР-ММ-ДД)'),
]
EMPLOYEE_FIELDS = [
    ('first_name', 'Ім’я'),
    ('last_name', 'Прізвище'),
    ('position', 'Посада'),
    ('phone', 'Телефон'),
    ('email', 'Email'),
    ('hire_date', 'Дата прийняття (РРРР-ММ-ДД)'),
    ('salary', 'Зарплата, грн'),
]

CUSTOMER_COLUMNS = [
    ('customer_id', 'ID', 68),
    ('first_name', 'Ім’я', 112),
    ('last_name', 'Прізвище', 130),
    ('phone', 'Телефон', 120),
    ('email', 'Email', 280),
    ('address', 'Адреса', 165),
    ('registration_date', 'Дата реєстрації', 125),
]
EMPLOYEE_COLUMNS = [
    ('employee_id', 'ID', 68),
    ('first_name', 'Ім’я', 118),
    ('last_name', 'Прізвище', 130),
    ('position', 'Посада', 135),
    ('phone', 'Телефон', 120),
    ('email', 'Email', 280),
    ('hire_date', 'Дата прийняття', 125),
    ('salary', 'Зарплата', 115),
]


def _format_value(key, value):
    if value is None:
        return '—'
    if key in ('registration_date', 'hire_date'):
        try:
            return date.fromisoformat(str(value)).strftime('%d.%m.%Y')
        except ValueError:
            return str(value)
    if key == 'salary':
        return f'{value:,.2f}'.replace(',', ' ').replace('.00', '') + ' грн'
    return str(value) if str(value) else '—'


class _ScrollTable:
    """Таблиця з прокруткою тільки в межах фактичних стовпців.

    Після перемикання підрозділів попередні grid-стовпці скидаються;
    інакше Tk залишає їхню мінімальну ширину, навіть коли вони порожні,
    а горизонтальна прокрутка веде до пустого місця.
    """

    def __init__(self, parent):
        self.box = ctk.CTkFrame(
            parent, fg_color=COLORS['white'], corner_radius=10,
            border_width=1, border_color=COLORS['light_border'],
        )
        self.box.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        self.box.grid_rowconfigure(0, weight=1)
        self.box.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self.box, bg=COLORS['white'], highlightthickness=0,
            bd=0, relief='flat',
        )
        self.canvas.grid(row=0, column=0, sticky='nsew', padx=(8, 0), pady=(8, 0))
        self.vertical = ctk.CTkScrollbar(
            self.box, orientation='vertical', command=self.canvas.yview, width=12,
        )
        self.vertical.grid(row=0, column=1, sticky='ns', pady=(8, 0), padx=(0, 4))
        self.horizontal = ctk.CTkScrollbar(
            self.box, orientation='horizontal', command=self.canvas.xview, height=12,
        )
        self.horizontal.grid(row=1, column=0, sticky='ew', padx=(8, 0), pady=(2, 6))
        self.canvas.configure(
            yscrollcommand=self.vertical.set,
            xscrollcommand=self.horizontal.set,
        )
        self.inner = ctk.CTkFrame(
            self.canvas, fg_color=COLORS['white'], corner_radius=0,
        )
        self.window_id = self.canvas.create_window(
            (0, 0), window=self.inner, anchor='nw',
        )
        self._column_count = 0
        self._min_content_width = 0
        self._horizontal_shown = True
        self.inner.bind('<Configure>', self._resize_content)
        self.canvas.bind('<Configure>', self._resize_viewport)

    def clear(self):
        """Очистити рядки та скинути ширину ВСІХ старих колонок."""
        for child in self.inner.winfo_children():
            child.destroy()
        for col in range(self._column_count):
            self.inner.grid_columnconfigure(col, minsize=0, weight=0)
        self._column_count = 0
        self._min_content_width = 0
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

    def set_columns(self, widths):
        """Задати фактичні колонки; відсутні праворуч не залишають порожнього місця."""
        widths = [int(width) for width in widths]
        for col in range(max(self._column_count, len(widths))):
            self.inner.grid_columnconfigure(col, minsize=0, weight=0)
        for col, width in enumerate(widths):
            self.inner.grid_columnconfigure(col, minsize=width, weight=1)
        self._column_count = len(widths)
        # Кожна клітинка має padx=2 зліва та справа.
        self._min_content_width = sum(widths) + 4 * len(widths)

    def _resize_viewport(self, event=None):
        viewport = event.width if event is not None else self.canvas.winfo_width()
        if viewport <= 1:
            return
        # Не користуємося шириною попереднього набору колонок.
        desired = max(viewport, self._min_content_width)
        current = self.canvas.itemcget(self.window_id, 'width')
        if not current or abs(float(current) - desired) > 1:
            self.canvas.itemconfigure(self.window_id, width=desired)
        self._update_scroll_area(desired, viewport)

    def _resize_content(self, _event=None):
        self._resize_viewport()

    def _update_scroll_area(self, width, viewport):
        height = max(self.inner.winfo_height(), 1)
        self.canvas.configure(scrollregion=(0, 0, width, height))
        needs_horizontal = width > viewport + 2
        if needs_horizontal != self._horizontal_shown:
            if needs_horizontal:
                self.horizontal.grid()
            else:
                self.horizontal.grid_remove()
                self.canvas.xview_moveto(0)
            self._horizontal_shown = needs_horizontal

    def _wheel(self, event):
        delta = -int(event.delta / 120)
        if event.state & 0x0001:  # Shift + колесо — горизонтально
            self.canvas.xview_scroll(delta, 'units')
        else:
            self.canvas.yview_scroll(delta, 'units')

    def enable_wheel(self, widget):
        widget.bind('<MouseWheel>', self._wheel, add='+')
        widget.bind('<Shift-MouseWheel>', self._wheel, add='+')

def _render_people_page(content, app, role, kind):
    if role not in ('admin', 'moderator') or (kind == 'employee' and role != 'admin'):
        return
    is_customer = kind == 'customer'
    label = 'користувача' if is_customer else 'працівника'
    title = 'Облік клієнтів' if is_customer else 'Облік персоналу'
    fields = CUSTOMER_FIELDS if is_customer else EMPLOYEE_FIELDS
    columns = CUSTOMER_COLUMNS if is_customer else EMPLOYEE_COLUMNS
    id_key = 'customer_id' if is_customer else 'employee_id'
    list_records = list_customers if is_customer else list_employees
    get_record = get_customer if is_customer else get_employee
    add_record = add_customer if is_customer else add_employee
    update_record = update_customer if is_customer else update_employee
    delete_record = delete_customer if is_customer else delete_employee

    heading = ctk.CTkFrame(content, fg_color='transparent')
    heading.pack(fill='x', padx=30, pady=(0, 12))

    search_frame = ctk.CTkFrame(content, fg_color='transparent')
    search_frame.pack(fill='x', padx=30, pady=(0, 10))
    search = ctk.CTkEntry(
        search_frame, height=38,
        placeholder_text='Пошук за ID, ПІБ, телефоном, email' +
        ('' if is_customer else ', посадою'),
    )
    search.pack(side='left', fill='x', expand=True)

    counter = ctk.CTkLabel(
        content, text='', font=('Arial', 12), text_color=COLORS['muted'],
    )
    counter.pack(anchor='w', padx=30, pady=(0, 8))

    table = _ScrollTable(content)
    actions_width = 240

    def refresh():
        try:
            people = list_records()
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка бази даних', str(exc), parent=app)
            return
        query = search.get().strip().casefold()
        visible = [person for person in people if not query or any(
            query in str(person.get(key) or '').casefold()
            for key in (id_key, 'first_name', 'last_name', 'phone', 'email',
                        'position' if not is_customer else 'address')
        )]
        counter.configure(text=f'Показано: {len(visible)} із {len(people)}')
        table.clear()
        all_columns = columns + [('actions', 'Дії', actions_width)]
        table.set_columns([width for _, _, width in all_columns])
        for i, (_, label_text, _) in enumerate(all_columns):
            cell = ctk.CTkLabel(
                table.inner, text=label_text,
                text_color=COLORS['body_heading'],
                font=('Arial', 11, 'bold'),
                fg_color=COLORS['header'], height=40,
                anchor='center', width=1,
            )
            cell.grid(row=0, column=i, sticky='nsew', padx=2, pady=2)
            table.enable_wheel(cell)
        if not visible:
            empty = ctk.CTkLabel(
                table.inner, text='Нічого не знайдено',
                height=64, text_color=COLORS['muted'],
            )
            empty.grid(row=1, column=0, columnspan=len(all_columns), sticky='ew')
            table.inner.update_idletasks()
            table._resize_content()
            return
        for row_i, person in enumerate(visible, start=1):
            shade = COLORS['white'] if row_i % 2 else COLORS['alt_row']
            for col_i, (key, _, width) in enumerate(columns):
                value = _format_value(key, person.get(key))
                cell = ctk.CTkLabel(
                    table.inner, text=value, text_color=COLORS['navy'],
                    font=('Arial', 11), fg_color=shade,
                    anchor='center', justify='center',
                    height=45, width=1, wraplength=width - 8,
                )
                cell.grid(row=row_i, column=col_i, sticky='nsew', padx=2, pady=2)
                table.enable_wheel(cell)
            person_id = person[id_key]
            col_i = len(columns)
            action_box = ctk.CTkFrame(table.inner, fg_color=shade, height=45)
            action_box.grid(row=row_i, column=col_i, sticky='nsew', padx=2, pady=2)
            action_box.grid_columnconfigure(0, weight=1)
            action_box.grid_columnconfigure(3, weight=1)
            edit_button = ctk.CTkButton(
                action_box, text_color="white", border_color=COLORS["navy"], text='Змінити', width=65, height=28,
                fg_color=COLORS["navy"], hover_color=COLORS["blue"],
                command=lambda record_id=person_id: open_editor(record_id),
            )
            edit_button.grid(row=0, column=1, pady=8, padx=(0, 3))
            shown_widgets = [action_box, edit_button]
            if role == 'admin':
                del_button = ctk.CTkButton(
                    action_box, border_color=COLORS["red"], text='Видалити', width=69, height=28,
                    fg_color=COLORS["red"], text_color="white",
                    hover_color=COLORS["error"],
                    command=lambda record_id=person_id: remove(record_id),
                )
                del_button.grid(row=0, column=2, pady=8, padx=(3, 0))
                shown_widgets.append(del_button)
            for w in shown_widgets:
                table.enable_wheel(w)
        table.inner.update_idletasks()
        table._resize_content()

    def remove(record_id):
        if role != 'admin':
            return
        try:
            person = get_record(record_id)
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка бази даних', str(exc), parent=app)
            return
        if person is None:
            refresh()
            return
        fullname = f"{person['first_name']} {person['last_name']}"
        question = f'Видалити {label} «{fullname}» (ID: {record_id})?'
        if messagebox.askyesno('Підтвердження видалення', question, parent=app):
            try:
                delete_record(record_id)
            except sqlite3.IntegrityError:
                messagebox.showerror(
                    'Помилка', 'Запис використовується в інших таблицях і не може бути видалений.',
                    parent=app,
                )
                return
            except sqlite3.Error as exc:
                messagebox.showerror('Помилка бази даних', str(exc), parent=app)
                return
            refresh()

    def open_editor(record_id=None):
        try:
            person = get_record(record_id) if record_id is not None else None
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка бази даних', str(exc), parent=app)
            return
        editing = person is not None
        if record_id is not None and not editing:
            messagebox.showwarning('Увага', 'Запис уже видалено.', parent=app)
            refresh()
            return
        dlg = ctk.CTkToplevel(app)
        dlg.title(('Змінити ' if editing else 'Додати ') + label)
        dlg.geometry('490x655')
        dlg.minsize(450, 540)
        dlg.configure(fg_color=COLORS['background'])
        dlg.transient(app)
        panel = ctk.CTkScrollableFrame(
            dlg, fg_color=COLORS['white'], corner_radius=10,
        )
        panel.pack(fill='both', expand=True, padx=16, pady=(16, 9))
        ctk.CTkLabel(
            panel,
            text=f"{title}: {record_id}" if editing else f'Новий {label}',
            font=('Arial', 19, 'bold'), text_color=COLORS['navy'],
        ).pack(anchor='w', padx=17, pady=(12, 6))
        ctk.CTkLabel(
            panel,
            text='ID призначається автоматично' if not editing else 'ID не редагується',
            text_color=COLORS['muted'], font=('Arial', 11),
        ).pack(anchor='w', padx=17, pady=(0, 14))
        entries = {}
        for field_key, field_caption in fields:
            ctk.CTkLabel(
                panel, text=field_caption, font=('Arial', 12),
                text_color=COLORS['body_heading'],
            ).pack(anchor='w', padx=17)
            placeholder = 'РРРР-ММ-ДД' if field_key.endswith('_date') else ''
            entry = ctk.CTkEntry(panel, height=34, placeholder_text=placeholder)
            entry.pack(fill='x', padx=17, pady=(4, 10))
            entries[field_key] = entry
            if editing:
                value = person.get(field_key)
                if value is not None:
                    entry.insert(0, str(value))
            elif field_key.endswith('_date'):
                entry.insert(0, date.today().isoformat())
            elif field_key == 'salary':
                entry.insert(0, '0')
        error_label = ctk.CTkLabel(
            dlg, text='', height=28,
            text_color=COLORS['error'], font=('Arial', 11),
        )
        error_label.pack(fill='x', padx=17)

        def save():
            vals = {name: field.get().strip() for name, field in entries.items()}
            try:
                if editing:
                    update_record(record_id, **vals)
                else:
                    add_record(**vals)
            except ValueError as exc:
                error_label.configure(text=str(exc))
                return
            except sqlite3.IntegrityError as exc:
                msg = ('Такий Email уже є у таблиці.' if 'email' in str(exc).lower()
                       else 'Помилка збереження: запис уже існує.')
                error_label.configure(text=msg)
                return
            except sqlite3.Error as exc:
                messagebox.showerror('Помилка бази даних', str(exc), parent=dlg)
                return
            dlg.destroy()
            refresh()

        footer = ctk.CTkFrame(dlg, fg_color='transparent')
        footer.pack(fill='x', padx=16, pady=(5, 15))
        ctk.CTkButton(
            footer, border_color=COLORS["navy"], text='Скасувати', height=36,
            fg_color=COLORS["navy"], text_color="white",
            hover_color=COLORS["blue"], command=dlg.destroy,
        ).pack(side='left', fill='x', expand=True, padx=(0, 5))
        ctk.CTkButton(
            footer, text_color="white", border_color=COLORS["navy"], text='Зберегти', height=36,
            fg_color=COLORS["navy"], hover_color=COLORS["blue"], command=save,
        ).pack(side='right', fill='x', expand=True, padx=(5, 0))
        dlg.after(100, lambda: dlg.grab_set() if dlg.winfo_exists() else None)
        entries['first_name'].focus_set()

    ctk.CTkButton(
        heading, text_color="white", border_color=COLORS["navy"], text='+ Додати ' + label, height=37, width=190,
        fg_color=COLORS["navy"], hover_color=COLORS["blue"],
        command=open_editor,
    ).pack(side='right', padx=(10, 0))
    search.bind('<KeyRelease>', lambda _event: refresh())
    refresh()


def render_customers_page(content, app, role):
    _render_people_page(content, app, role, 'customer')


def render_employees_page(content, app, role):
    _render_people_page(content, app, role, 'employee')
