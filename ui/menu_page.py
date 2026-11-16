"""Сторінка меню: рецептури, перевірка запасів та фото страв."""
import sqlite3
from decimal import Decimal, InvalidOperation
from tkinter import filedialog, messagebox

import customtkinter as ctk

from database import (
    list_menu_catalog, get_menu_catalog_item, save_menu_with_recipe,
    remove_menu_item, list_ingredients,
)
from ui.photos import load_thumbnail, store_photo
from ui.theme import COLORS, MENU_CATEGORIES, format_price, format_quantity


def render_menu_page(content, app, role):
    is_admin = role == "admin"

    heading = ctk.CTkFrame(content, fg_color="transparent")
    heading.pack(fill="x", padx=22, pady=(0, 12))

    filters = ctk.CTkFrame(content, fg_color="transparent")
    filters.pack(fill="x", padx=22, pady=(0, 9))
    search = ctk.CTkEntry(
        filters, height=36, placeholder_text="Пошук назви або ID..."
    )
    search.pack(side="left", fill="x", expand=True, padx=(0, 8))
    categories = ctk.CTkOptionMenu(
        filters, width=140, height=36,
        values=["Усі категорії"] + MENU_CATEGORIES,
        fg_color=COLORS["blue"], button_color=COLORS["navy"],
    )
    categories.pack(side="left", padx=(0, 8))
    categories.set("Усі категорії")
    statuses = ctk.CTkOptionMenu(
        filters, width=150, height=36,
        values=["Усі стани", "Можна готувати", "Бракує", "Склад не задано"],
        fg_color=COLORS["blue"], button_color=COLORS["navy"],
    )
    statuses.pack(side="left")
    statuses.set("Усі стани")

    count = ctk.CTkLabel(
        content, text="", font=("Arial", 12), text_color=COLORS["muted"]
    )
    count.pack(anchor="w", padx=22, pady=(0, 6))

    card = ctk.CTkFrame(
        content, fg_color="white", corner_radius=10,
        border_width=1, border_color=COLORS["light_border"],
    )
    card.pack(fill="both", expand=True, padx=22, pady=(0, 18))
    table = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
    table.pack(fill="both", expand=True, padx=8, pady=8)

    headers = ["ID", "Позиція / фото", "Категорія", "Ціна", "Склад", "Наявність"]
    mins = [35, 122, 82, 75, 152, 110]
    weights = [0, 2, 1, 1, 2, 1]
    if is_admin:
        headers.append("Дії")
        mins.append(235)
        weights.append(0)
    for col, minimum in enumerate(mins):
        table.grid_columnconfigure(col, weight=weights[col], minsize=minimum)

    def draw():
        try:
            catalog = list_menu_catalog()
        except sqlite3.Error as exc:
            messagebox.showerror("Помилка БД", str(exc), parent=app)
            return
        for child in table.winfo_children():
            child.destroy()

        query = search.get().strip().casefold()
        chosen_category = categories.get()
        chosen_status = statuses.get()
        results = [
            item for item in catalog
            if (not query or query in item["name"].casefold() or query in str(item["id"])
                or any(query in part["name"].casefold() for part in item["recipe"]))
            and (chosen_category == "Усі категорії" or item["category"] == chosen_category)
            and (chosen_status == "Усі стани" or item["availability"] == chosen_status)
        ]
        count.configure(text=f"Показано позицій: {len(results)} із {len(catalog)}")
        for col, label in enumerate(headers):
            ctk.CTkLabel(
                table, text=label, font=("Arial", 11, "bold"),
                text_color=COLORS["body_heading"], fg_color=COLORS["header"],
                height=38, width=1, anchor="center",
            ).grid(row=0, column=col, sticky="ew", padx=2, pady=2)
        if not results:
            ctk.CTkLabel(
                table, text="Нічого не знайдено", text_color=COLORS["muted"],
                height=60,
            ).grid(row=1, column=0, columnspan=len(headers), sticky="ew")
            return

        availability_colors = {
            "Можна готувати": COLORS["green"],
            "Бракує": COLORS["red"],
            "Склад не задано": COLORS["muted"],
        }
        for row, item in enumerate(results, start=1):
            bg = COLORS["white"] if row % 2 else COLORS["alt_row"]
            ctk.CTkLabel(
                table, text=str(item["id"]), height=64, width=1,
                fg_color=bg, text_color=COLORS["text"], anchor="center",
            ).grid(row=row, column=0, sticky="nsew", padx=2, pady=2)

            name_frame = ctk.CTkFrame(table, fg_color=bg, height=64)
            name_frame.grid(row=row, column=1, sticky="nsew", padx=2, pady=2)
            thumb = load_thumbnail(item["image_path"], size=(42, 42))
            if thumb:
                ctk.CTkLabel(name_frame, image=thumb, text="", width=44).pack(
                    side="left", padx=(3, 5), pady=9
                )
            else:
                ctk.CTkLabel(
                    name_frame, text="▧", width=33, height=42,
                    text_color=COLORS["photo_placeholder"], font=("Arial", 19),
                ).pack(side="left", padx=(3, 5), pady=9)
            ctk.CTkLabel(
                name_frame, text=item["name"], anchor="w", justify="left",
                wraplength=100, font=("Arial", 11),
                text_color=COLORS["text"],
            ).pack(side="left", fill="both", expand=True, padx=(0, 2))
            for col, value in [(2, item["category"]), (3, format_price(item["price"]))]:
                ctk.CTkLabel(
                    table, text=value, height=64, width=1,
                    fg_color=bg, text_color=COLORS["text"], anchor="center",
                    font=("Arial", 11),
                ).grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

            composition = (
                "\n".join(f"{part['name']}: {format_quantity(part['amount'])} {part['unit']}"
                          for part in item["recipe"])
                if item["recipe"] else "—"
            )
            # Показуємо весь склад (у таблиці є вертикальне прокручування).
            ctk.CTkLabel(
                table, text=composition, font=("Arial", 10),
                fg_color=bg, text_color=COLORS["text"], width=1,
                height=64, anchor="center", justify="left", wraplength=150,
            ).grid(row=row, column=4, sticky="nsew", padx=2, pady=2)

            status_text = item["availability"]
            if item["availability"] == "Бракує":
                status_text += "\n" + ", ".join(part["name"] for part in item["missing"])
            ctk.CTkLabel(
                table, text=status_text, font=("Arial", 11), width=1,
                fg_color=bg, text_color=availability_colors[item["availability"]],
                height=64, anchor="center", justify="center", wraplength=106,
            ).grid(row=row, column=5, sticky="nsew", padx=2, pady=2)

            if is_admin:
                actions = ctk.CTkFrame(table, fg_color=bg, height=64)
                actions.grid(row=row, column=6, sticky="nsew", padx=2, pady=2)
                actions.grid_columnconfigure(0, weight=1)
                actions.grid_columnconfigure(3, weight=1)
                ctk.CTkButton(
                    actions, text="Змінити", width=62, height=30,
                    fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
                    command=lambda pk=item["id"]: open_editor(pk),
                ).grid(row=0, column=1, padx=(0, 3), pady=15)
                ctk.CTkButton(
                    actions, text="Видалити", width=64, height=30,
                    fg_color=COLORS["soft_danger"], text_color=COLORS["red"],
                    hover_color=COLORS["hover_danger"],
                    command=lambda pk=item["id"]: delete_item(pk),
                ).grid(row=0, column=2, padx=(3, 0), pady=15)

    def delete_item(pk):
        if not is_admin:
            return
        item = get_menu_catalog_item(pk)
        if item and messagebox.askyesno(
            "Видалення позиції", f"Видалити «{item['name']}» з меню?", parent=app
        ):
            try:
                remove_menu_item(pk)
                draw()
            except sqlite3.Error as exc:
                messagebox.showerror("Помилка бази", str(exc), parent=app)

    def open_editor(pk=None):
        if not is_admin:
            return
        try:
            item = get_menu_catalog_item(pk) if pk is not None else None
            ingredients = list_ingredients()
        except sqlite3.Error as exc:
            messagebox.showerror("Помилка бази", str(exc), parent=app)
            return
        editing = item is not None
        by_id = {i["id"]: i for i in ingredients}
        dialog = ctk.CTkToplevel(app)
        dialog.title("Змінити позицію" if editing else "Додати позицію")
        dialog.geometry("625x750")
        dialog.minsize(540, 590)
        dialog.configure(fg_color=COLORS["background"])
        dialog.transient(app)

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="white", corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        ctk.CTkLabel(
            scroll, text="Редагування позиції" if editing else "Нова позиція меню",
            font=("Arial", 21, "bold"), text_color=COLORS["navy"],
        ).pack(anchor="w", padx=16, pady=(10, 16))

        def field(label, placeholder=""):
            ctk.CTkLabel(scroll, text=label, text_color=COLORS["body_heading"]).pack(
                anchor="w", padx=16,
            )
            ent = ctk.CTkEntry(scroll, height=35, placeholder_text=placeholder)
            ent.pack(fill="x", padx=16, pady=(3, 11))
            return ent

        name = field("Назва", "Наприклад, Маргарита")
        ctk.CTkLabel(scroll, text="Категорія", text_color=COLORS["body_heading"]).pack(
            anchor="w", padx=16,
        )
        category = ctk.CTkOptionMenu(
            scroll, values=MENU_CATEGORIES, height=35,
            fg_color=COLORS["blue"], button_color=COLORS["navy"],
        )
        category.pack(fill="x", padx=16, pady=(3, 11))
        price = field("Ціна, грн", "Наприклад, 220")
        weight = field("Вага, г (необов’язково)", "Наприклад, 450")
        if editing:
            name.insert(0, item["name"])
            category.set(item["category"])
            price.insert(0, str(item["price"]))
            if item.get("weight_g"):
                weight.insert(0, str(item["weight_g"]))
        else:
            category.set(MENU_CATEGORIES[0])

        ctk.CTkLabel(
            scroll, text="Фотографія (необов'язково)",
            font=("Arial", 13, "bold"), text_color=COLORS["navy"],
        ).pack(anchor="w", padx=16, pady=(7, 4))
        photo = {"path": item["image_path"] if item else None, "selected": None}
        photo_row = ctk.CTkFrame(scroll, fg_color=COLORS["alt_row"], height=70)
        photo_row.pack(fill="x", padx=16, pady=(0, 12))
        preview = ctk.CTkLabel(photo_row, text="Немає фото", width=105)
        preview.pack(side="left", padx=8, pady=6)
        photo_buttons = ctk.CTkFrame(photo_row, fg_color="transparent")
        photo_buttons.pack(side="left", fill="x", expand=True)

        def refresh_photo():
            source = photo["selected"] if photo["selected"] else photo["path"]
            image = load_thumbnail(source, size=(75, 60), selected=bool(photo["selected"]))
            preview.configure(image=image, text="" if image else "Немає фото")
            preview.image_ref = image

        def select_photo():
            selected = filedialog.askopenfilename(
                parent=dialog, title="Оберіть фотографію",
                filetypes=[("Зображення", "*.jpg *.jpeg *.png *.webp *.bmp *.gif")],
            )
            if selected:
                photo["selected"] = selected
                refresh_photo()

        def clear_photo():
            photo["path"] = None
            photo["selected"] = None
            refresh_photo()

        ctk.CTkButton(
            photo_buttons, text="Обрати фото", height=30, width=110,
            fg_color=COLORS["blue"], command=select_photo,
        ).pack(side="left", padx=(0, 5))
        ctk.CTkButton(
            photo_buttons, text="Прибрати", height=30, width=93,
            fg_color=COLORS["soft_button"], text_color=COLORS["text"],
            hover_color=COLORS["hover_button"], command=clear_photo,
        ).pack(side="left")
        refresh_photo()

        ctk.CTkLabel(
            scroll, text="Склад (на одну порцію)",
            font=("Arial", 15, "bold"), text_color=COLORS["navy"],
        ).pack(anchor="w", padx=16, pady=(9, 3))
        ctk.CTkLabel(
            scroll, text="Почніть вводити назву. Натисніть на підказку, "
                 "щоб додати інгредієнт, і вкажіть його кількість.",
            font=("Arial", 11), text_color=COLORS["muted"],
            wraplength=480, justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        finder = ctk.CTkEntry(
            scroll, height=35, placeholder_text="Наприклад, Сир моцарела..."
        )
        finder.pack(fill="x", padx=16, pady=(0, 3))
        suggestion_frame = ctk.CTkFrame(scroll, fg_color=COLORS["header"])
        recipe_frame = ctk.CTkFrame(scroll, fg_color=COLORS["alt_row"])
        recipe_frame.pack(fill="x", padx=16, pady=(8, 12))
        chosen = {}

        def update_suggestions(_event=None):
            for widget in suggestion_frame.winfo_children():
                widget.destroy()
            suggestion_frame.pack_forget()
            query = finder.get().strip().casefold()
            if not query:
                return
            matches = [i for i in ingredients if query in i["name"].casefold()
                       and i["id"] not in chosen][:7]
            if not matches:
                return
            suggestion_frame.pack(fill="x", padx=16, pady=(0, 5), before=recipe_frame)
            for candidate in matches:
                ctk.CTkButton(
                    suggestion_frame,
                    text=f"{candidate['name']} ({candidate['unit']})",
                    anchor="w", height=28,
                    fg_color=COLORS["header"], text_color=COLORS["text"],
                    hover_color=COLORS["hover_button"],
                    command=lambda ing=candidate: add_component(ing),
                ).pack(fill="x", padx=3, pady=1)

        def remove_component(ingredient_id):
            chosen[ingredient_id]["frame"].destroy()
            del chosen[ingredient_id]
            update_suggestions()

        def add_component(ingredient, amount=None):
            ing_id = ingredient["id"]
            if ing_id in chosen:
                return
            frame = ctk.CTkFrame(recipe_frame, fg_color=COLORS["alt_row"])
            frame.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(
                frame, text=ingredient["name"], font=("Arial", 11),
                text_color=COLORS["text"], anchor="w", wraplength=245,
            ).pack(side="left", fill="x", expand=True, padx=(4, 6))
            quantity = ctk.CTkEntry(
                frame, height=30, width=70, placeholder_text="К-сть",
            )
            quantity.pack(side="left", padx=(0, 3))
            if amount is not None:
                quantity.insert(0, format_quantity(amount))
            ctk.CTkLabel(
                frame, text=ingredient["unit"], width=25,
                text_color=COLORS["muted"], font=("Arial", 11),
            ).pack(side="left", padx=(0, 3))
            ctk.CTkButton(
                frame, text="×", width=30, height=30,
                fg_color=COLORS["soft_danger"], text_color=COLORS["red"],
                hover_color=COLORS["hover_danger"],
                command=lambda: remove_component(ing_id),
            ).pack(side="left", padx=(0, 4))
            chosen[ing_id] = {"frame": frame, "entry": quantity, "ingredient": ingredient}
            finder.delete(0, "end")
            update_suggestions()

        finder.bind("<KeyRelease>", update_suggestions)
        if editing:
            for part in item["recipe"]:
                ing = by_id.get(part["ingredient_id"])
                if ing:
                    add_component(ing, part["amount"])

        error_label = ctk.CTkLabel(
            dialog, text="", font=("Arial", 11), text_color=COLORS["error"],
            height=30, wraplength=560,
        )
        error_label.pack(fill="x", padx=18)

        def save():
            label = name.get().strip()
            raw_price = price.get().strip().replace(",", ".")
            try:
                amount = Decimal(raw_price)
                if not amount.is_finite() or amount <= 0:
                    raise ValueError("Вкажіть ціну більше нуля")
                components = []
                for ing_id, selected in chosen.items():
                    text = selected["entry"].get().strip().replace(",", ".")
                    quantity = Decimal(text)
                    if not quantity.is_finite() or quantity <= 0:
                        raise ValueError(
                            f"Вкажіть кількість для «{selected['ingredient']['name']}»"
                        )
                    components.append((ing_id, quantity))
                photo_path = photo["path"]
                if photo["selected"]:
                    photo_path = store_photo(photo["selected"])
                raw_weight = weight.get().strip()
                grams = None
                if raw_weight:
                    try:
                        grams = int(raw_weight)
                    except ValueError:
                        raise ValueError("Вага має бути цілим числом грамів")
                    if not 1 <= grams <= 100000:
                        raise ValueError("Вага має бути від 1 до 100000 г")
                saved_id = save_menu_with_recipe(
                    pk, label, category.get(), amount, components, photo_path
                )
                from database import db_connection
                with db_connection() as conn:
                    conn.execute("UPDATE menu_items SET weight_g=? WHERE id=?", (grams, saved_id))
            except (InvalidOperation, ValueError) as exc:
                error_label.configure(text=str(exc) or "Перевірте введені дані")
                return
            except sqlite3.IntegrityError:
                error_label.configure(text="Позиція з такою назвою вже існує")
                return
            except (sqlite3.Error, OSError) as exc:
                messagebox.showerror("Помилка збереження", str(exc), parent=dialog)
                return
            dialog.destroy()
            draw()

        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkButton(
            buttons, text="Скасувати", height=36,
            fg_color=COLORS["soft_button"], text_color=COLORS["text"],
            hover_color=COLORS["hover_button"], command=dialog.destroy,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            buttons, text="Зберегти", height=36,
            fg_color=COLORS["navy"], hover_color=COLORS["blue"],
            command=save,
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))
        dialog.after(100, lambda: dialog.grab_set() if dialog.winfo_exists() else None)
        name.focus_set()

    if is_admin:
        ctk.CTkButton(
            heading, text="+ Додати позицію", width=160, height=36,
            fg_color=COLORS["navy"], hover_color=COLORS["blue"],
            command=open_editor,
        ).pack(side="right")
    search.bind("<KeyRelease>", lambda _event: draw())
    categories.configure(command=lambda _value: draw())
    statuses.configure(command=lambda _value: draw())
    draw()
