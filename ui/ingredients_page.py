"""Сторінка складського обліку (адміністратор)."""
import sqlite3
from decimal import Decimal, InvalidOperation
from tkinter import messagebox
import customtkinter as ctk
from database import (list_ingredients, get_ingredient, add_ingredient,
                      update_ingredient, remove_ingredient, menu_usage_for_ingredient)
from ui.theme import COLORS, format_price, format_quantity


def render_ingredients_page(content, app, current_role):
    # Склад ингредиентов (SQLite). Только администратор видит этот раздел.
    heading = ctk.CTkFrame(content, fg_color="transparent")
    heading.pack(fill="x", padx=30, pady=(0, 13))

    filters = ctk.CTkFrame(content, fg_color="transparent")
    filters.pack(fill="x", padx=30, pady=(0, 11))
    search_entry = ctk.CTkEntry(
        filters, placeholder_text="Пошук за назвою або кодом...", height=38
    )
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    status_filter = ctk.CTkOptionMenu(
        filters, values=["Усі залишки", "Достатньо", "Мало", "Немає"],
        width=160, height=38, fg_color=COLORS["blue"],
        button_color=COLORS["navy"], button_hover_color=COLORS["blue_hover"]
    )
    status_filter.pack(side="right")
    status_filter.set("Усі залишки")

    summary = ctk.CTkFrame(content, fg_color="transparent")
    summary.pack(fill="x", padx=30, pady=(0, 8))
    count_label = ctk.CTkLabel(
        summary, text="", font=("Arial", 12), text_color=COLORS["muted"]
    )
    count_label.pack(side="left")
    warning_label = ctk.CTkLabel(
        summary, text="", font=("Arial", 12), text_color=COLORS["red"]
    )
    warning_label.pack(side="right")

    table_card = ctk.CTkFrame(
        content, fg_color="white", corner_radius=10,
        border_width=1, border_color=COLORS["light_border"]
    )
    table_card.pack(fill="both", expand=True, padx=30, pady=(0, 22))
    ingredient_table = ctk.CTkScrollableFrame(
        table_card, fg_color="transparent", corner_radius=0
    )
    ingredient_table.pack(fill="both", expand=True, padx=10, pady=10)

    # SQLite призначає інгредієнтам числовий ID автоматично.
    # Показуємо його окремо, а назву — без коду в дужках.
    headers = ["ID", "Назва", "Од.", "Залишок", "Мінімум", "Ціна/од.", "Стан", "Дії"]
    column_weights = [0, 5, 0, 1, 1, 1, 1, 0]
    column_minwidths = [72, 158, 46, 68, 70, 82, 89, 235]
    for col, (weight, minwidth) in enumerate(zip(column_weights, column_minwidths)):
        ingredient_table.grid_columnconfigure(col, weight=weight, minsize=minwidth)

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
                or query in str(item["id"]) or query in item["code"].casefold())
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
                font=("Arial", 11, "bold"), text_color=COLORS["body_heading"],
                fg_color=COLORS["header"], height=38, width=1, anchor="center"
            ).grid(row=0, column=col, sticky="ew", padx=2, pady=2)

        if not shown:
            ctk.CTkLabel(
                ingredient_table, text="Нічого не знайдено",
                text_color=COLORS["muted"], height=60
            ).grid(row=1, column=0, columnspan=len(headers), sticky="ew")
            return

        status_colors = {
            "Немає": COLORS["red"], "Мало": COLORS["orange"],
            "Достатньо": COLORS["green"]
        }
        for row_index, item in enumerate(shown, 1):
            bg = COLORS["white"] if row_index % 2 else COLORS["alt_row"]
            values = [
                item["code"], item["name"], item["unit"],
                format_quantity(item["quantity"]),
                format_quantity(item["minimum"]),
                format_price(item["price"]), item["status"]
            ]
            for col, value in enumerate(values):
                ctk.CTkLabel(
                    ingredient_table, text=value,
                    font=("Arial", 11),
                    text_color=status_colors.get(value, COLORS["navy"]) if col == 6 else COLORS["navy"],
                    fg_color=bg, height=44, width=1, anchor="center"
                ).grid(row=row_index, column=col, sticky="ew", padx=2, pady=2)

            actions = ctk.CTkFrame(ingredient_table, fg_color=bg, height=44)
            actions.grid(row=row_index, column=7, sticky="nsew", padx=2, pady=2)
            actions.grid_columnconfigure(0, weight=1)
            actions.grid_columnconfigure(3, weight=1)
            ctk.CTkButton(
                actions, text="Змінити", width=62, height=29,
                fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
                command=lambda item_id=item["id"]: open_ingredient_editor(item_id)
            ).grid(row=0, column=1, padx=(0, 3), pady=6)
            ctk.CTkButton(
                actions, text="Видалити", width=64, height=29,
                fg_color=COLORS["soft_danger"], text_color=COLORS["red"],
                hover_color=COLORS["hover_danger"],
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
        used_in = menu_usage_for_ingredient(item_id)
        prompt = f'Видалити «{item["name"]}» зі складу?'
        if used_in:
            prompt += ("\n\nУвага: інгредієнт буде вилучено також зі складу "
                       "таких позицій меню:\n" + "\n".join(used_in[:8]))
            if len(used_in) > 8:
                prompt += f"\n...та ще {len(used_in) - 8}"
        if messagebox.askyesno(
            "Видалення інгредієнта", prompt, parent=app
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
        dialog.configure(fg_color=COLORS["background"])
        dialog.transient(app)

        form = ctk.CTkFrame(dialog, fg_color="white", corner_radius=10)
        form.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(
            form, text="Редагування інгредієнта" if editing else "Новий інгредієнт",
            font=("Arial", 20, "bold"), text_color=COLORS["navy"]
        ).pack(anchor="w", padx=20, pady=(16, 11))

        def entry_field(label, placeholder=""):
            ctk.CTkLabel(
                form, text=label, text_color=COLORS["body_heading"]
            ).pack(anchor="w", padx=20)
            entry = ctk.CTkEntry(form, height=34, placeholder_text=placeholder)
            entry.pack(fill="x", padx=20, pady=(3, 9))
            return entry

        name_entry = entry_field("Назва", "Наприклад, Сир фета")
        ctk.CTkLabel(
            form, text="Одиниця вимірювання", text_color=COLORS["body_heading"]
        ).pack(anchor="w", padx=20)
        unit_entry = ctk.CTkOptionMenu(
            form, values=["кг", "л", "шт"], height=34,
            fg_color=COLORS["blue"], button_color=COLORS["navy"]
        )
        unit_entry.pack(fill="x", padx=20, pady=(3, 9))
        quantity_entry = entry_field("Залишок на складі", "Наприклад, 2,5")
        minimum_entry = entry_field("Мінімальний залишок", "Наприклад, 1")
        price_entry = entry_field("Ціна за одиницю, грн", "Наприклад, 320")
        error_label = ctk.CTkLabel(
            form, text="", text_color=COLORS["error"], font=("Arial", 11),
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
            fg_color=COLORS["soft_button"], text_color=COLORS["navy"],
            hover_color=COLORS["hover_button"], command=dialog.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            buttons_row, text="Зберегти", height=36,
            fg_color=COLORS["navy"], hover_color=COLORS["blue"],
            command=save_ingredient
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))
        dialog.after(
            100, lambda: dialog.grab_set() if dialog.winfo_exists() else None
        )
        name_entry.focus_set()

    ctk.CTkButton(
        heading, text="+ Додати інгредієнт", width=180, height=36,
        fg_color=COLORS["navy"], hover_color=COLORS["blue"],
        command=open_ingredient_editor
    ).pack(side="right")
    search_entry.bind("<KeyRelease>", lambda event: render_ingredient_rows())
    status_filter.configure(command=lambda value: render_ingredient_rows())
    render_ingredient_rows()
