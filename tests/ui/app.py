
import customtkinter as ctk
from tkinter import messagebox

from database import initialize_database
from people_db import initialize_people_database, people_counts
from ui.people_page import render_customers_page, render_employees_page
from ui.menu_page import render_menu_page
from ui.ingredients_page import render_ingredients_page
from ui.theme import COLORS


# Создаёт pizza_house.db при первом запуске. При следующих запусках данные сохраняются.
initialize_database()
initialize_people_database()

ctk.set_appearance_mode("light")

app = ctk.CTk()
app.title("Pizza House — Система управління")
app.geometry("1100x700")
app.minsize(1050, 650)
app.configure(fg_color=COLORS["background"])

# Боковая панель
sidebar = ctk.CTkFrame(
    app,
    width=210,
    corner_radius=0,
    fg_color=COLORS["navy"]
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
    text_color=COLORS["sidebar_hint"]
).pack(pady=(0, 12))

role_label = ctk.CTkLabel(
    sidebar,
    text="",
    text_color=COLORS["sidebar_hint"],
    font=("Arial", 12)
)
role_label.pack(pady=(0, 18))

# Основная область
content = ctk.CTkFrame(
    app,
    corner_radius=0,
    fg_color=COLORS["background"]
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

def show_page(page):
    if current_role != "admin" and page in admin_pages:
        return

    # Подсветка активного раздела
    for name, button in buttons.items():
        button.configure(
            fg_color=COLORS["blue"] if name == page
            else "transparent"
        )

    # Скрываем область на время построения страницы, чтобы не было наложения.
    content.pack_forget()

    # Очистка рабочей области
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
        text_color=COLORS["navy"]
    ).pack(anchor="w", padx=30, pady=(30, 8))

    if page == "Головна":
        ctk.CTkLabel(
            content,
            text="Оберіть розділ для роботи з системою",
            text_color=COLORS["muted"]
        ).pack(anchor="w", padx=30)

        # Контейнер карточек
        cards_frame = ctk.CTkFrame(
            content,
            fg_color="transparent"
        )
        cards_frame.pack(
            fill="x",
            padx=25,
            pady=(25, 0)
        )

        # Кількість людей береться з SQLite; замовлення поки демонстраційні.
        counts = people_counts()
        stats = [
            ("Нові замовлення", "3", COLORS["card_green"]),
            ("Всього замовлень", "128", COLORS["card_blue"]),
            ("Користувачі", str(counts["customers"]), COLORS["card_purple"]),
            ("Працівники", str(counts["employees"]), COLORS["card_orange"])
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
                text_color=COLORS["body_heading"]
            ).pack(pady=(18, 5))

            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 27, "bold"),
                text_color=COLORS["navy"]
            ).pack(pady=(0, 15))

        # Таблица последних заказов
        orders_frame = ctk.CTkFrame(
            content,
            fg_color="white",
            corner_radius=10,
            border_width=1,
            border_color=COLORS["light_border"]
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
            text_color=COLORS["navy"]
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
                text_color=COLORS["body_heading"],
                fg_color=COLORS["header"],
                height=35
            ).grid(
                row=0,
                column=col,
                sticky="ew"
            )

        # Тестовые заказы
        orders = [
            ("110", "Назар Романенко", "19.10.2026", "620", "Нове"),
            ("109", "Ірина Савченко", "19.10.2026", "450", "Скасоване"),
            ("108", "Владислав Поліщук", "19.10.2026", "510", "Готується"),
            ("107", "Ольга Лисенко", "19.10.2026", "250", "Виконане"),
            ("106", "Дмитро Кравченко", "19.10.2026", "320", "Виконане")
        ]

        status_colors = {
            "Нове": COLORS["status_blue"],
            "Скасоване": COLORS["error"],
            "Готується": COLORS["status_yellow"],
            "Виконане": COLORS["green"]
        }

        for row_index, order in enumerate(orders, start=1):
            bg = (
                COLORS["white"] if row_index % 2
                else COLORS["alt_row"]
            )

            for col, value in enumerate(order):
                ctk.CTkLabel(
                    table,
                    text=value,
                    font=("Arial", 12),
                    text_color=(
                        status_colors.get(value, COLORS["navy"])
                        if col == 4 else COLORS["navy"]
                    ),
                    fg_color=bg,
                    height=38
                ).grid(
                    row=row_index,
                    column=col,
                    sticky="ew"
                )

   
    elif page == "Меню":
        render_menu_page(content, app, current_role)
    elif page == "Інгредієнти":
        render_ingredients_page(content, app, current_role)
    elif page == "Користувачі":
        render_customers_page(content, app, current_role)
    elif page == "Працівники":
        render_employees_page(content, app, current_role)

    else:
        ctk.CTkLabel(
            content,
            text="Тут буде вміст розділу",
            text_color=COLORS["muted"]
        ).pack(anchor="w", padx=30)

    # Показываем страницу только после создания всех её элементов.
    content.pack(side="left", fill="both", expand=True)


# Кнопки бокового меню — восстановлены
for page in pages:
    button = ctk.CTkButton(
        sidebar,
        text=page,
        anchor="w",
        height=40,
        fg_color="transparent",
        hover_color=COLORS["blue_hover"],
        text_color="white",
        command=lambda p=page: show_page(p)
    )
    button.pack(fill="x", padx=12, pady=3)
    buttons[page] = button

# Кнопка выхода
ctk.CTkButton(
    sidebar,
    text="Вихід",
    fg_color="transparent",
    hover_color=COLORS["blue_hover"],
    command=app.destroy
).pack(
    side="bottom",
    fill="x",
    padx=12,
    pady=20
)


# Тестовые аккаунты пока НЕ подключены к SQLite.
# Таблиця клієнтів тепер у SQLite, але авторизація client/1234
# ще демонстраційна. Реєстрацію при оформленні замовлення додамо пізніше.
demo_users = {"client": "1234"}
admin_login = "admin"
admin_password = "1234"


def enter_app(role, username=None):
    global current_role, current_user
    current_role = role
    current_user = username

    # Показываем только доступные для роли разделы.
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


# Экран входа поверх основного интерфейса.
login_frame = ctk.CTkFrame(
    app,
    fg_color=COLORS["background"],
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
    border_color=COLORS["light_border"]
)
login_card.place(relx=0.5, rely=0.5, anchor="center")
login_card.pack_propagate(False)

ctk.CTkLabel(
    login_card,
    text="🍕 Pizza House",
    font=("Arial", 28, "bold"),
    text_color=COLORS["navy"]
).pack(pady=(32, 5))

ctk.CTkLabel(
    login_card,
    text="Увійдіть до свого облікового запису",
    text_color=COLORS["muted"]
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
    text_color=COLORS["error"],
    height=24
)
error_label.pack(pady=(6, 0))

ctk.CTkButton(
    login_card,
    text="Увійти",
    width=300,
    height=42,
    fg_color=COLORS["navy"],
    hover_color=COLORS["blue"],
    command=check_user
).pack(pady=5)

ctk.CTkButton(
    login_card,
    text="Продовжити як гість",
    width=300,
    height=42,
    fg_color="transparent",
    text_color=COLORS["navy"],
    border_width=1,
    border_color=COLORS["sidebar_hint"],
    hover_color=COLORS["header"],
    command=lambda: enter_app("guest")
).pack(pady=9)

# Кнопка администратора находится в нижнем правом углу всего окна.
# Она проверяет логин и пароль из тех же полей.
ctk.CTkButton(
    login_frame,
    text="Вхід для адміністратора",
    width=185,
    height=30,
    fg_color="transparent",
    text_color=COLORS["muted"],
    hover_color=COLORS["light_border"],
    command=check_admin
).place(relx=1, rely=1, x=-18, y=-18, anchor="se")

# Enter в поле пароля запускает обычный пользовательский вход.
password_entry.bind("<Return>", lambda event: check_user())

def run():
    app.mainloop()
