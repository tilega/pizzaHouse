
import customtkinter as ctk
from tkinter import messagebox
from decimal import Decimal, InvalidOperation
import sqlite3

from database import (
    initialize_database,
    list_menu_items,
    get_menu_item,
    add_menu_item,
    update_menu_item,
    remove_menu_item,
    list_ingredients,
    get_ingredient,
    add_ingredient,
    update_ingredient,
    remove_ingredient,
)

initialize_database()

ctk.set_appearance_mode("light")

app = ctk.CTk()
app.title("Pizza House — Система управління")
app.geometry("1100x700")
app.minsize(1050, 650)
app.configure(fg_color="#F5F7FA")

sidebar = ctk.CTkFrame(
    app,
    width=210,
    corner_radius=0,
    fg_color="#192B3A"
)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar,
    text="🍕 Pizza House",
    font=("Arial", 21, "bold"),
    text_color="white"
).pack(pady=(30, 5))

ctk.CTkLabel(
    sidebar,
    text="Система управління",
    text_color="#B8C5D0"
).pack(pady=(0, 12))

role_label = ctk.CTkLabel(
    sidebar,
    text="",
    text_color="#B8C5D0",
    font=("Arial", 12)
)
role_label.pack(pady=(0, 18))

content = ctk.CTkFrame(
    app,
    corner_radius=0,
    fg_color="#F5F7FA"
)
content.pack(side="left", fill="both", expand=True)

pages = [
    "Головна",
    "Замовлення",
    "Меню",
    "Інгредієнти",
    "Закупівлі",
    "Користувачі",
    "Працівники"
]

buttons = {}
current_role = None
current_user = None

admin_pages = {
    "Головна",
    "Інгредієнти",
    "Закупівлі",
    "Користувачі",
    "Працівники"
}

menu_categories = ["Піца", "Закуска", "Напій", "Соус"]


def format_price(price):
    """Выводим цену в гривнах без лишних нулей."""
    amount = Decimal(str(price))
    if amount == amount.to_integral_value():
        return f"{int(amount)} грн"
    return f"{amount:.2f}".replace(".", ",") + " грн"


def format_quantity(quantity):
    """Отображать 1,5 / 0,25 / 3 без лишних нулей."""
    result = format(Decimal(str(quantity)), "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result.replace(".", ",")


def show_page(page):
    if current_role != "admin" and page in admin_pages:
        return

    for name, button in buttons.items():
        button.configure(
            fg_color="#365571" if name == page
            else "transparent"
        )

    content.pack_forget()

    for widget in content.winfo_children():
        widget.destroy()

    title = (
        "Вітаємо, Адміністратор!"
        if page == "Головна" else page
    )

    ctk.CTkLabel(
        content,
        text=title,
        font=("Arial", 26, "bold"),
        text_color="#192B3A"
    ).pack(anchor="w", padx=30, pady=(30, 8))

    if page == "Головна":
        ctk.CTkLabel(
            content,
            text="Оберіть розділ для роботи з системою",
            text_color="#657587"
        ).pack(anchor="w", padx=30)

        cards_frame = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )
        cards_frame.pack(
            fill="x",
            padx=25,
            pady=(25, 0)
        )

        stats = [
            ("Нові замовлення", "3", "#EAF8F0"),
            ("Всього замовлень", "128", "#EAF1FF"),
            ("Користувачі", "9", "#F2EDFF"),
            ("Працівники", "8", "#FFF3E9")
        ]

        for i, (name, value, color) in enumerate(stats):
            cards_frame.grid_columnconfigure(
                i,
                weight=1,
                uniform="cards"
            )

            card = ctk.CTkFrame(
                cards_frame,
                fg_color=color,
                corner_radius=10,
                height=105
            )
            card.grid(
                row=0,
                column=i,
                padx=5,
                sticky="nsew"
            )
            card.grid_propagate(False)

            ctk.CTkLabel(
                card,
                text=name,
                font=("Arial", 12),
                text_color="#405568"
            ).pack(pady=(18, 5))

            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 27, "bold"),
                text_color="#192B3A"
            ).pack(pady=(0, 15))

        orders_frame = ctk.CTkFrame(
            content,
            fg_color="white",
            corner_radius=10,
            border_width=1,
            border_color="#E3E8EE"
        )
        orders_frame.pack(
            fill="x",
            padx=30,
            pady=(25, 0)
        )

        ctk.CTkLabel(
            orders_frame,
            text="Останні замовлення",
            font=("Arial", 17, "bold"),
            text_color="#192B3A"
        ).pack(
            anchor="w",
            padx=15,
            pady=(15, 10)
        )

        table = ctk.CTkFrame(
            orders_frame,
            fg_color="transparent"
        )
        table.pack(
            fill="x",
            padx=15,
            pady=(0, 15)
        )

        headers = [
            "ID", "Клієнт", "Дата", "Сума", "Статус"
        ]

        for col, header in enumerate(headers):
            table.grid_columnconfigure(col, weight=1)

            ctk.CTkLabel(
                table,
                text=header,
                font=("Arial", 12, "bold"),
                text_color="#405568",
                fg_color="#EDF1F5",
                height=35
            ).grid(
                row=0,
                column=col,
                sticky="ew"
            )

        orders = [
            ("110", "Назар Романенко", "19.10.2026", "620", "Нове"),
            ("109", "Ірина Савченко", "19.10.2026", "450", "Скасоване"),
            ("108", "Владислав Поліщук", "19.10.2026", "510", "Готується"),
            ("107", "Ольга Лисенко", "19.10.2026", "250", "Виконане"),
            ("106", "Дмитро Кравченко", "19.10.2026", "320", "Виконане")
        ]

        status_colors = {
            "Нове": "#2563EB",
            "Скасоване": "#DC2626",
            "Готується": "#D97706",
            "Виконане": "#15803D"
        }

        for row_index, order in enumerate(orders, start=1):
            bg = (
                "#FFFFFF" if row_index % 2
                else "#F7F9FC"
            )

            for col, value in enumerate(order):
                ctk.CTkLabel(
                    table,
                    text=value,
                    font=("Arial", 12),
                    text_color=(
                        status_colors.get(value, "#192B3A")
                        if col == 4 else "#192B3A"
                    ),
                    fg_color=bg,
                    height=38
                ).grid(
                    row=row_index,
                    column=col,
                    sticky="ew"
                )

   
    elif page == "Меню":
        is_admin = current_role == "admin"

        menu_heading = ctk.CTkFrame(content, fg_color="transparent")
        menu_heading.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(
            menu_heading,
            text="Керування асортиментом" if is_admin else "Асортимент піцерії",
            font=("Arial", 14),
            text_color="#657587"
        ).pack(side="left")

        filters = ctk.CTkFrame(content, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 10))

        search_entry = ctk.CTkEntry(
            filters,
            placeholder_text="Пошук за назвою або ID...",
            height=38
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        category_filter = ctk.CTkOptionMenu(
            filters,
            values=["Усі категорії"] + menu_categories,
            width=175,
            height=38,
            fg_color="#365571",
            button_color="#192B3A",
            button_hover_color="#2D455A"
        )
        category_filter.pack(side="right")
        category_filter.set("Усі категорії")

        count_label = ctk.CTkLabel(
            content, text="", text_color="#657587", font=("Arial", 12)
        )
        count_label.pack(anchor="w", padx=30, pady=(0, 8))

        table_card = ctk.CTkFrame(
            content, fg_color="white", corner_radius=10,
            border_width=1, border_color="#E3E8EE"
        )
        table_card.pack(fill="both", expand=True, padx=30, pady=(0, 25))

        menu_table = ctk.CTkScrollableFrame(
            table_card, fg_color="transparent", corner_radius=0
        )
        menu_table.pack(fill="both", expand=True, padx=12, pady=12)

        column_weights = [1, 4, 2, 2, 3] if is_admin else [1, 4, 2, 2]
        for col, weight in enumerate(column_weights):
            menu_table.grid_columnconfigure(col, weight=weight, minsize=142 if (is_admin and col == 4) else 0)

        def render_menu_rows():
            try:
                menu_items = list_menu_items()
            except sqlite3.Error as exc:
                messagebox.showerror(
                    "Помилка бази даних", f"Не вдалося завантажити меню:\n{exc}",
                    parent=app
                )
                return

            for widget in menu_table.winfo_children():
                widget.destroy()

            query = search_entry.get().strip().casefold()
            selected_category = category_filter.get()
            visible_items = [
                item for item in menu_items
                if (not query or query in item["name"].casefold()
                    or query in str(item["id"]))
                and (selected_category == "Усі категорії"
                     or item["category"] == selected_category)
            ]
            count_label.configure(
                text=f"Показано позицій: {len(visible_items)} із {len(menu_items)}"
            )

            headers = ["ID", "Назва", "Категорія", "Ціна"]
            if is_admin:
                headers.append("Дії")

            for col, header in enumerate(headers):
                ctk.CTkLabel(
                    menu_table, text=header, font=("Arial", 12, "bold"),
                    text_color="#405568", fg_color="#EDF1F5", height=38,
                    width=1, anchor="center"
                ).grid(row=0, column=col, sticky="ew", padx=2, pady=2)

            if not visible_items:
                ctk.CTkLabel(
                    menu_table, text="За вашим запитом нічого не знайдено",
                    text_color="#657587", height=60
                ).grid(row=1, column=0, columnspan=len(headers), sticky="ew")
                return

            for row_index, item in enumerate(visible_items, start=1):
                bg = "#FFFFFF" if row_index % 2 else "#F7F9FC"
                values = (
                    str(item["id"]), item["name"], item["category"],
                    format_price(item["price"])
                )
                for col, value in enumerate(values):
                    ctk.CTkLabel(
                        menu_table, text=value, font=("Arial", 12),
                        text_color="#192B3A", fg_color=bg,
                        height=44, width=1, anchor="center"
                    ).grid(row=row_index, column=col, sticky="ew", padx=2, pady=2)

                if is_admin:
                    actions = ctk.CTkFrame(menu_table, fg_color=bg, height=44)
                    actions.grid(row=row_index, column=4, sticky="nsew", padx=2, pady=2)
                    actions.grid_columnconfigure(0, weight=1)
                    actions.grid_columnconfigure(3, weight=1)
                    ctk.CTkButton(
                        actions, text="Змінити", width=62, height=30,
                        fg_color="#365571", hover_color="#2D455A",
                        command=lambda item_id=item["id"]: open_menu_editor(item_id)
                    ).grid(row=0, column=1, padx=(0, 3), pady=6)
                    ctk.CTkButton(
                        actions, text="Видалити", width=64, height=30,
                        fg_color="#FBE8E8", text_color="#B91C1C",
                        hover_color="#F8D0D0",
                        command=lambda item_id=item["id"]: delete_menu_item(item_id)
                    ).grid(row=0, column=2, padx=(3, 0), pady=6)

        def delete_menu_item(item_id):
            if current_role != "admin":
                return
            try:
                item = get_menu_item(item_id)
            except sqlite3.Error as exc:
                messagebox.showerror("Помилка бази даних", str(exc), parent=app)
                return
            if item is None:
                return
            confirmed = messagebox.askyesno(
                "Видалення позиції",
                f"Видалити «{item['name']}» з меню?",
                parent=app
            )
            if confirmed:
                try:
                    remove_menu_item(item_id)
                except sqlite3.Error as exc:
                    messagebox.showerror("Помилка бази даних", str(exc), parent=app)
                    return
                render_menu_rows()

        def open_menu_editor(item_id=None):
            if current_role != "admin":
                return
            try:
                item = get_menu_item(item_id) if item_id is not None else None
            except sqlite3.Error as exc:
                messagebox.showerror("Помилка бази даних", str(exc), parent=app)
                return
            editing = item is not None

            dialog = ctk.CTkToplevel(app)
            dialog.title("Змінити позицію" if editing else "Додати позицію")
            dialog.geometry("420x445")
            dialog.resizable(False, False)
            dialog.configure(fg_color="#F5F7FA")
            dialog.transient(app)

            form = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
            form.pack(fill="both", expand=True, padx=18, pady=18)

            ctk.CTkLabel(
                form,
                text="Редагування позиції" if editing else "Нова позиція меню",
                font=("Arial", 20, "bold"), text_color="#192B3A"
            ).pack(anchor="w", padx=20, pady=(18, 12))

            ctk.CTkLabel(
                form, text="Назва", text_color="#405568"
            ).pack(anchor="w", padx=20)
            name_entry = ctk.CTkEntry(form, height=36)
            name_entry.pack(fill="x", padx=20, pady=(4, 10))

            ctk.CTkLabel(
                form, text="Категорія", text_color="#405568"
            ).pack(anchor="w", padx=20)
            category_entry = ctk.CTkOptionMenu(
                form, values=menu_categories, height=36,
                fg_color="#365571", button_color="#192B3A"
            )
            category_entry.pack(fill="x", padx=20, pady=(4, 10))

            ctk.CTkLabel(
                form, text="Ціна, грн", text_color="#405568"
            ).pack(anchor="w", padx=20)
            price_entry = ctk.CTkEntry(form, height=36, placeholder_text="Наприклад, 220")
            price_entry.pack(fill="x", padx=20, pady=(4, 5))

            error_label = ctk.CTkLabel(
                form, text="", text_color="#DC2626", font=("Arial", 11),
                height=30
            )
            error_label.pack(padx=20, pady=(0, 3))

            if editing:
                name_entry.insert(0, item["name"])
                category_entry.set(item["category"])
                price_entry.insert(0, str(item["price"]))

            def save_item():
                name = name_entry.get().strip()
                category = category_entry.get()
                price_text = price_entry.get().strip().replace(",", ".")

                if not name:
                    error_label.configure(text="Введіть назву позиції")
                    return
                try:
                    price = Decimal(price_text)
                    if (not price.is_finite() or price <= 0
                            or price > Decimal("1000000")
                            or price.as_tuple().exponent < -2):
                        raise ValueError("Неправильна ціна")
                    price = price.quantize(Decimal("0.01"))
                except (InvalidOperation, ValueError):
                    error_label.configure(text="Вкажіть коректну ціну (більше 0)")
                    return

                try:
                    if editing:
                        update_menu_item(item_id, name, category, price)
                    else:
                        add_menu_item(name, category, price)
                except sqlite3.IntegrityError:
                    error_label.configure(text="Позиція з такою назвою вже існує")
                    return
                except (sqlite3.Error, ValueError) as exc:
                    messagebox.showerror(
                        "Помилка збереження", f"Не вдалося зберегти позицію:\n{exc}",
                        parent=dialog
                    )
                    return

                dialog.destroy()
                render_menu_rows()

            buttons_row = ctk.CTkFrame(form, fg_color="transparent")
            buttons_row.pack(fill="x", padx=20, pady=(0, 16))
            ctk.CTkButton(
                buttons_row, text="Скасувати", height=36,
                fg_color="#E8EDF2", text_color="#192B3A",
                hover_color="#D6DFE7", command=dialog.destroy
            ).pack(side="left", fill="x", expand=True, padx=(0, 6))
            ctk.CTkButton(
                buttons_row, text="Зберегти", height=36,
                fg_color="#192B3A", hover_color="#365571",
                command=save_item
            ).pack(side="left", fill="x", expand=True, padx=(6, 0))

            dialog.after(100, lambda: dialog.grab_set() if dialog.winfo_exists() else None)
            name_entry.focus_set()

        if is_admin:
            ctk.CTkButton(
                menu_heading, text="+ Додати позицію", width=160,
                height=36, fg_color="#192B3A", hover_color="#365571",
                command=open_menu_editor
            ).pack(side="right")

        search_entry.bind("<KeyRelease>", lambda event: render_menu_rows())
        category_filter.configure(command=lambda value: render_menu_rows())
        render_menu_rows()

    elif page == "Інгредієнти":
        heading = ctk.CTkFrame(content, fg_color="transparent")
        heading.pack(fill="x", padx=30, pady=(0, 13))
        ctk.CTkLabel(
            heading, text="Облік запасів на складі",
            font=("Arial", 14), text_color="#657587"
        ).pack(side="left")

        filters = ctk.CTkFrame(content, fg_color="transparent")
        filters.pack(fill="x", padx=30, pady=(0, 11))
        search_entry = ctk.CTkEntry(
            filters, placeholder_text="Пошук за назвою або кодом...", height=38
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        status_filter = ctk.CTkOptionMenu(
            filters, values=["Усі залишки", "Достатньо", "Мало", "Немає"],
            width=160, height=38, fg_color="#365571",
            button_color="#192B3A", button_hover_color="#2D455A"
        )
        status_filter.pack(side="right")
        status_filter.set("Усі залишки")

        summary = ctk.CTkFrame(content, fg_color="transparent")
        summary.pack(fill="x", padx=30, pady=(0, 8))
        count_label = ctk.CTkLabel(
            summary, text="", font=("Arial", 12), text_color="#657587"
        )
        count_label.pack(side="left")
        warning_label = ctk.CTkLabel(
            summary, text="", font=("Arial", 12), text_color="#B91C1C"
        )
        warning_label.pack(side="right")

        table_card = ctk.CTkFrame(
            content, fg_color="white", corner_radius=10,
            border_width=1, border_color="#E3E8EE"
        )
        table_card.pack(fill="both", expand=True, padx=30, pady=(0, 22))
        ingredient_table = ctk.CTkScrollableFrame(
            table_card, fg_color="transparent", corner_radius=0
        )
        ingredient_table.pack(fill="both", expand=True, padx=10, pady=10)

        headers = ["Назва (код)", "Од.", "Залишок", "Мінімум", "Ціна/од.", "Стан", "Дії"]
        for col, weight in enumerate([5, 1, 2, 2, 2, 2, 3]):
            ingredient_table.grid_columnconfigure(col, weight=weight, minsize=142 if col == 6 else 0)

        def render_ingredient_rows():
            try:
                all_items = list_ingredients()
            except sqlite3.Error as exc:
                messagebox.showerror(
                    "Помилка бази даних", f"Не вдалося завантажити склад:\n{exc}",
                    parent=app
                )
                return

            for widget in ingredient_table.winfo_children():
                widget.destroy()

            query = search_entry.get().strip().casefold()
            selection = status_filter.get()
            shown = [
                item for item in all_items
                if (not query or query in item["name"].casefold()
                    or query in item["code"].casefold())
                and (selection == "Усі залишки" or item["status"] == selection)
            ]
            count_label.configure(
                text=f"Показано: {len(shown)} із {len(all_items)}"
            )
            no_stock = sum(item["status"] == "Немає" for item in all_items)
            low_stock = sum(item["status"] == "Мало" for item in all_items)
            warning_label.configure(text=f"Немає: {no_stock}    Мало: {low_stock}")

            for col, title_text in enumerate(headers):
                ctk.CTkLabel(
                    ingredient_table, text=title_text,
                    font=("Arial", 11, "bold"), text_color="#405568",
                    fg_color="#EDF1F5", height=38, width=1, anchor="center"
                ).grid(row=0, column=col, sticky="ew", padx=2, pady=2)

            if not shown:
                ctk.CTkLabel(
                    ingredient_table, text="Нічого не знайдено",
                    text_color="#657587", height=60
                ).grid(row=1, column=0, columnspan=len(headers), sticky="ew")
                return

            status_colors = {
                "Немає": "#B91C1C", "Мало": "#B45309",
                "Достатньо": "#15803D"
            }
            for row_index, item in enumerate(shown, 1):
                bg = "#FFFFFF" if row_index % 2 else "#F7F9FC"
                values = [
                    f'{item["name"]} ({item["code"]})', item["unit"],
                    format_quantity(item["quantity"]),
                    format_quantity(item["minimum"]),
                    format_price(item["price"]), item["status"]
                ]
                for col, value in enumerate(values):
                    ctk.CTkLabel(
                        ingredient_table, text=value,
                        font=("Arial", 11),
                        text_color=status_colors.get(value, "#192B3A") if col == 5 else "#192B3A",
                        fg_color=bg, height=44, width=1, anchor="center"
                    ).grid(row=row_index, column=col, sticky="ew", padx=2, pady=2)

                actions = ctk.CTkFrame(ingredient_table, fg_color=bg, height=44)
                actions.grid(row=row_index, column=6, sticky="nsew", padx=2, pady=2)
                actions.grid_columnconfigure(0, weight=1)
                actions.grid_columnconfigure(3, weight=1)
                ctk.CTkButton(
                    actions, text="Змінити", width=62, height=29,
                    fg_color="#365571", hover_color="#2D455A",
                    command=lambda item_id=item["id"]: open_ingredient_editor(item_id)
                ).grid(row=0, column=1, padx=(0, 3), pady=6)
                ctk.CTkButton(
                    actions, text="Видалити", width=64, height=29,
                    fg_color="#FBE8E8", text_color="#B91C1C",
                    hover_color="#F8D0D0",
                    command=lambda item_id=item["id"]: delete_ingredient(item_id)
                ).grid(row=0, column=2, padx=(3, 0), pady=6)

        def delete_ingredient(item_id):
            if current_role != "admin":
                return
            try:
                item = get_ingredient(item_id)
            except sqlite3.Error as exc:
                messagebox.showerror("Помилка бази даних", str(exc), parent=app)
                return
            if item is None:
                return
            if messagebox.askyesno(
                "Видалення інгредієнта",
                f'Видалити «{item["name"]}» зі складу?', parent=app
            ):
                try:
                    remove_ingredient(item_id)
                except sqlite3.Error as exc:
                    messagebox.showerror("Помилка бази даних", str(exc), parent=app)
                    return
                render_ingredient_rows()

        def open_ingredient_editor(item_id=None):
            if current_role != "admin":
                return
            try:
                item = get_ingredient(item_id) if item_id is not None else None
            except sqlite3.Error as exc:
                messagebox.showerror("Помилка бази даних", str(exc), parent=app)
                return
            editing = item is not None

            dialog = ctk.CTkToplevel(app)
            dialog.title("Змінити інгредієнт" if editing else "Додати інгредієнт")
            dialog.geometry("450x600")
            dialog.resizable(False, False)
            dialog.configure(fg_color="#F5F7FA")
            dialog.transient(app)

            form = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
            form.pack(fill="both", expand=True, padx=16, pady=16)
            ctk.CTkLabel(
                form, text="Редагування інгредієнта" if editing else "Новий інгредієнт",
                font=("Arial", 20, "bold"), text_color="#192B3A"
            ).pack(anchor="w", padx=20, pady=(16, 11))

            def entry_field(label, placeholder=""):
                ctk.CTkLabel(
                    form, text=label, text_color="#405568"
                ).pack(anchor="w", padx=20)
                entry = ctk.CTkEntry(form, height=34, placeholder_text=placeholder)
                entry.pack(fill="x", padx=20, pady=(3, 9))
                return entry

            name_entry = entry_field("Назва", "Наприклад, Сир фета")
            ctk.CTkLabel(
                form, text="Одиниця вимірювання", text_color="#405568"
            ).pack(anchor="w", padx=20)
            unit_entry = ctk.CTkOptionMenu(
                form, values=["кг", "л", "шт"], height=34,
                fg_color="#365571", button_color="#192B3A"
            )
            unit_entry.pack(fill="x", padx=20, pady=(3, 9))
            quantity_entry = entry_field("Залишок на складі", "Наприклад, 2,5")
            minimum_entry = entry_field("Мінімальний залишок", "Наприклад, 1")
            price_entry = entry_field("Ціна за одиницю, грн", "Наприклад, 320")
            error_label = ctk.CTkLabel(
                form, text="", text_color="#DC2626", font=("Arial", 11),
                height=27
            )
            error_label.pack(padx=20, pady=(0, 2))

            if editing:
                name_entry.insert(0, item["name"])
                unit_entry.set(item["unit"])
                quantity_entry.insert(0, format_quantity(item["quantity"]))
                minimum_entry.insert(0, format_quantity(item["minimum"]))
                price_entry.insert(0, str(item["price"]))
            else:
                unit_entry.set("кг")
                quantity_entry.insert(0, "0")
                minimum_entry.insert(0, "0")

            def save_ingredient():
                name = name_entry.get().strip()
                unit = unit_entry.get()
                if not name or len(name) > 100:
                    error_label.configure(text="Введіть назву (до 100 символів)")
                    return
                try:
                    quantity = Decimal(quantity_entry.get().strip().replace(",", "."))
                    minimum = Decimal(minimum_entry.get().strip().replace(",", "."))
                    price = Decimal(price_entry.get().strip().replace(",", "."))
                    if (not price.is_finite() or price <= 0
                            or price > Decimal("1000000")
                            or price * 100 != (price * 100).to_integral_value()):
                        raise ValueError("Вкажіть коректну ціну")
                    if editing:
                        update_ingredient(item_id, name, unit, quantity, minimum, price)
                    else:
                        add_ingredient(name, unit, quantity, minimum, price)
                except (InvalidOperation, ValueError) as exc:
                    error_label.configure(text=str(exc) or "Перевірте кількість та ціну")
                    return
                except sqlite3.IntegrityError:
                    error_label.configure(text="Інгредієнт із такою назвою вже існує")
                    return
                except sqlite3.Error as exc:
                    messagebox.showerror("Помилка бази даних", str(exc), parent=dialog)
                    return
                dialog.destroy()
                render_ingredient_rows()

            buttons_row = ctk.CTkFrame(form, fg_color="transparent")
            buttons_row.pack(fill="x", padx=20, pady=(0, 12))
            ctk.CTkButton(
                buttons_row, text="Скасувати", height=36,
                fg_color="#E8EDF2", text_color="#192B3A",
                hover_color="#D6DFE7", command=dialog.destroy
            ).pack(side="left", fill="x", expand=True, padx=(0, 6))
            ctk.CTkButton(
                buttons_row, text="Зберегти", height=36,
                fg_color="#192B3A", hover_color="#365571",
                command=save_ingredient
            ).pack(side="left", fill="x", expand=True, padx=(6, 0))
            dialog.after(
                100, lambda: dialog.grab_set() if dialog.winfo_exists() else None
            )
            name_entry.focus_set()

        ctk.CTkButton(
            heading, text="+ Додати інгредієнт", width=180, height=36,
            fg_color="#192B3A", hover_color="#365571",
            command=open_ingredient_editor
        ).pack(side="right")
        search_entry.bind("<KeyRelease>", lambda event: render_ingredient_rows())
        status_filter.configure(command=lambda value: render_ingredient_rows())
        render_ingredient_rows()

    else:
        ctk.CTkLabel(
            content,
            text="Тут буде вміст розділу",
            text_color="#657587"
        ).pack(anchor="w", padx=30)

    content.pack(side="left", fill="both", expand=True)


for page in pages:
    button = ctk.CTkButton(
        sidebar,
        text=page,
        anchor="w",
        height=40,
        fg_color="transparent",
        hover_color="#2D455A",
        text_color="white",
        command=lambda p=page: show_page(p)
    )
    button.pack(fill="x", padx=12, pady=3)
    buttons[page] = button

ctk.CTkButton(
    sidebar,
    text="Вихід",
    fg_color="transparent",
    hover_color="#2D455A",
    command=app.destroy
).pack(
    side="bottom",
    fill="x",
    padx=12,
    pady=20
)


demo_users = {"client": "1234"}
admin_login = "admin"
admin_password = "1234"


def enter_app(role, username=None):
    global current_role, current_user
    current_role = role
    current_user = username

    for button in buttons.values():
        button.pack_forget()

    for page in pages:
        if role == "admin" or page not in admin_pages:
            buttons[page].pack(fill="x", padx=12, pady=3)

    if role == "admin":
        role_label.configure(text="Адміністратор")
    elif role == "user":
        role_label.configure(text=f"Користувач: {username}")
    else:
        role_label.configure(text="Гість")

    login_frame.destroy()
    show_page("Головна" if role == "admin" else "Меню")


def check_user():
    username = login_entry.get().strip()
    password = password_entry.get()

    if username in demo_users and demo_users[username] == password:
        enter_app("user", username)
    else:
        error_label.configure(text="Невірний логін або пароль користувача")


def check_admin():
    username = login_entry.get().strip()
    password = password_entry.get()

    if username == admin_login and password == admin_password:
        enter_app("admin", username)
    else:
        error_label.configure(text="Невірні дані адміністратора")


login_frame = ctk.CTkFrame(
    app,
    fg_color="#F5F7FA",
    corner_radius=0
)
login_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

login_card = ctk.CTkFrame(
    login_frame,
    width=380,
    height=430,
    fg_color="white",
    corner_radius=15,
    border_width=1,
    border_color="#E3E8EE"
)
login_card.place(relx=0.5, rely=0.5, anchor="center")
login_card.pack_propagate(False)

ctk.CTkLabel(
    login_card,
    text="🍕 Pizza House",
    font=("Arial", 28, "bold"),
    text_color="#192B3A"
).pack(pady=(32, 5))

ctk.CTkLabel(
    login_card,
    text="Увійдіть до свого облікового запису",
    text_color="#657587"
).pack(pady=(0, 24))

login_entry = ctk.CTkEntry(
    login_card,
    width=300,
    height=40,
    placeholder_text="Логін"
)
login_entry.pack(pady=7)

password_entry = ctk.CTkEntry(
    login_card,
    width=300,
    height=40,
    placeholder_text="Пароль",
    show="*"
)
password_entry.pack(pady=7)

error_label = ctk.CTkLabel(
    login_card,
    text="",
    text_color="#DC2626",
    height=24
)
error_label.pack(pady=(6, 0))

ctk.CTkButton(
    login_card,
    text="Увійти",
    width=300,
    height=42,
    fg_color="#192B3A",
    hover_color="#365571",
    command=check_user
).pack(pady=5)

ctk.CTkButton(
    login_card,
    text="Продовжити як гість",
    width=300,
    height=42,
    fg_color="transparent",
    text_color="#192B3A",
    border_width=1,
    border_color="#B8C5D0",
    hover_color="#EDF1F5",
    command=lambda: enter_app("guest")
).pack(pady=9)

ctk.CTkButton(
    login_frame,
    text="Вхід для адміністратора",
    width=185,
    height=30,
    fg_color="transparent",
    text_color="#657587",
    hover_color="#E3E8EE",
    command=check_admin
).place(relx=1, rely=1, x=-18, y=-18, anchor="se")

password_entry.bind("<Return>", lambda event: check_user())

app.mainloop()
