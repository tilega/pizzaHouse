
import customtkinter as ctk
from tkinter import messagebox

from database import initialize_database
from people_db import initialize_people_database
from procurement_db import initialize_procurement_database
from orders_db import initialize_orders_database
from ui.procurement_page import render_procurement_page
from ui.orders_page import render_orders_page
from ui.home_page import render_home_page
from ui.people_page import render_customers_page, render_employees_page
from ui.menu_page import render_menu_page
from ui.ingredients_page import render_ingredients_page
from ui.theme import COLORS
from auth_db import initialize_auth_database, authenticate, register
from ui.client_pages import render_client_menu, render_cart, render_history, render_account


# Создаёт pizza_house.db при первом запуске. При следующих запусках данные сохраняются.
initialize_database()
initialize_people_database()
initialize_procurement_database()
initialize_orders_database()
initialize_auth_database()

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

admin_page_names = [
    "Головна",
    "Замовлення",
    "Меню",
    "Інгредієнти",
    "Закупівлі",
    "Користувачі",
    "Працівники"
]

client_page_names = ["Меню", "Кошик", "Історія замовлень", "Акаунт"]
guest_page_names = ["Меню", "Кошик"]
pages = admin_page_names + [p for p in client_page_names if p not in admin_page_names]
buttons = {}
cart = {}
customer_id = None
current_role = None
current_user = None

admin_pages = {
    "Головна",
    "Інгредієнти",
    "Закупівлі",
    "Користувачі",
    "Працівники"
}

def update_current_login(login):
    global current_user
    current_user = login
    role_label.configure(text=f'Користувач: {login}')


def show_page(page):
    allowed = admin_page_names if current_role == "admin" else (
        guest_page_names if current_role == "guest" else client_page_names)
    if page not in allowed:
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
        render_home_page(content, app, current_role)
    elif page == "Замовлення":
        render_orders_page(content, app, current_role)
    elif page == "Закупівлі":
        render_procurement_page(content, app, current_role)
    elif page == "Меню":
        if current_role == "admin":
            render_menu_page(content, app, current_role)
        else:
            render_client_menu(content, app, cart, update_cart_label)
    elif page == "Кошик":
        render_cart(content, app, cart, customer_id, show_page, update_cart_label)
    elif page == "Історія замовлень":
        render_history(content, customer_id)
    elif page == "Акаунт":
        render_account(content, customer_id, update_current_login)
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
def update_cart_label():
    if "Кошик" in buttons:
        count = sum(cart.values())
        buttons["Кошик"].configure(text=f"Кошик ({count})" if count else "Кошик")


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


def enter_app(role, username=None, linked_customer=None):
    global current_role, current_user, customer_id
    current_role = role
    current_user = username
    customer_id = linked_customer

    # Показываем только доступные для роли разделы.
    for button in buttons.values():
        button.pack_forget()

    visible = admin_page_names if role == "admin" else (
        guest_page_names if role == "guest" else client_page_names)
    for page in visible:
        buttons[page].pack(fill="x", padx=12, pady=3)
    update_cart_label()

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

    linked = authenticate(username, password)
    if linked:
        enter_app("user", username, linked)
    elif username in demo_users and demo_users[username] == password:
        # Старий демонстраційний логін не прив'язаний до клієнта з Excel.
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


def open_registration():
    dialog = ctk.CTkToplevel(app)
    dialog.title("Реєстрація клієнта")
    dialog.geometry("420x590")
    dialog.transient(app)
    body = ctk.CTkScrollableFrame(dialog)
    body.pack(fill="both", expand=True, padx=15, pady=15)
    ctk.CTkLabel(body, text="Створити акаунт", font=("Arial", 22, "bold")).pack(pady=10)
    fields = {}
    for key, title, secret in [
        ("login", "Логін", False), ("password", "Пароль (від 6 символів)", True),
        ("first", "Ім’я", False), ("last", "Прізвище", False),
        ("phone", "Телефон", False), ("email", "Email", False),
        ("address", "Адреса", False),
    ]:
        ctk.CTkLabel(body, text=title).pack(anchor="w", pady=(8, 0))
        ent = ctk.CTkEntry(body, show="*" if secret else "")
        ent.pack(fill="x")
        fields[key] = ent
    def submit():
        try:
            customer = register(
                fields["login"].get(), fields["password"].get(),
                fields["first"].get(), fields["last"].get(),
                fields["phone"].get(), fields["email"].get(),
                fields["address"].get())
        except Exception as exc:
            messagebox.showerror("Реєстрація", str(exc), parent=dialog)
            return
        username = fields["login"].get().strip()
        dialog.destroy()
        enter_app("user", username, customer)
    ctk.CTkButton(body, text="Зареєструватися", command=submit).pack(pady=20)


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

ctk.CTkButton(
    login_card, text="Створити акаунт", width=300,
    fg_color="transparent", text_color=COLORS["navy"],
    command=open_registration
).pack(pady=(0, 3))

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
