
import customtkinter as ctk
from ui.login_design import pizza_background, PressButton, login_card as make_login_card, field as login_field
from tkinter import messagebox

from database import initialize_database
from people_db import initialize_people_database
from procurement_db import initialize_procurement_database
from orders_db import initialize_orders_database
from ui.procurement_page import render_procurement_page
from ui.orders_page import render_orders_page
from ui.home_page import render_home_page
from ui.statistics_page import render_statistics_page
from ui.people_page import render_customers_page, render_employees_page
from ui.menu_page import render_menu_page
from ui.ingredients_page import render_ingredients_page
from ui.theme import COLORS
from auth_db import initialize_auth_database, initialize_demo_customer_account, authenticate, register
from ui.client_pages import render_client_menu, render_cart, render_history, render_account
from reviews_db import initialize_reviews_database
from ui.reviews_page import render_admin_reviews
from staff_db import initialize_staff_database, authenticate_staff
from ui.staff_page import render_staff_page, render_staff_password_page


# Создаёт pizza_house.db при первом запуске. При следующих запусках данные сохраняются.
initialize_database()
initialize_people_database()
initialize_procurement_database()
initialize_orders_database()
initialize_auth_database()
initialize_demo_customer_account()
initialize_reviews_database()
initialize_staff_database()

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

sidebar_subtitle = ctk.CTkLabel(
    sidebar,
    text="Система управління",
    text_color=COLORS["sidebar_hint"]
)
sidebar_subtitle.pack(pady=(0, 12))

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
    "Статистика",
    "Замовлення",
    "Відгуки",
    "Меню",
    "Інгредієнти",
    "Закупівлі",
    "Користувачі",
    "Працівники",
    "Доступ персоналу",
    "Мій пароль"
]
moderator_page_names = [
    "Головна", "Статистика", "Замовлення", "Відгуки", "Меню", "Інгредієнти",
    "Користувачі", "Мій пароль"
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
    allowed = (admin_page_names if current_role == "admin" else
               moderator_page_names if current_role == "moderator" else
               guest_page_names if current_role == "guest" else client_page_names)
    if page not in allowed:
        return

    # Подсветка активного раздела
    for name, button in buttons.items():
        button.configure(
            fg_color=("#D92335" if current_role in ("user", "guest") else COLORS["blue"]) if name == page
            else "transparent"
        )

    # Скрываем область на время построения страницы, чтобы не было наложения.
    content.pack_forget()

    # Очистка рабочей области
    for widget in content.winfo_children():
        widget.destroy()

    title = (
        ("Вітаємо, Адміністратор!" if current_role == "admin" else "Панель модератора")
        if page == "Головна" else page
    )

    ctk.CTkLabel(
        content,
        text=("Наше меню" if page == "Меню" and current_role in ("user", "guest") else title),
        font=("Arial", 26, "bold"),
        text_color=COLORS["navy"]
    ).pack(anchor="w", padx=30, pady=(30, 8))

    if page == "Головна":
        render_home_page(content, app, current_role)
    elif page == "Статистика":
        render_statistics_page(content, app, current_role)
    elif page == "Замовлення":
        render_orders_page(content, app, current_role)
    elif page == "Відгуки":
        render_admin_reviews(content, app, current_role)
    elif page == "Закупівлі":
        render_procurement_page(content, app, current_role)
    elif page == "Меню":
        if current_role in ("admin", "moderator"):
            render_menu_page(content, app, current_role)
        else:
            render_client_menu(content, app, cart, update_cart_label, customer_id)
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
    elif page == "Доступ персоналу":
        render_staff_page(content, app, current_role)
    elif page == "Мій пароль":
        render_staff_password_page(content, app, current_user)

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
        # PizzaHouse client sidebar: modern theme.
        cart_text = f"Кошик ({count})" if count else "Кошик"
        if current_role in ("user", "guest"):
            cart_text = "🛒  " + cart_text
        buttons["Кошик"].configure(text=cart_text)


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



def enter_app(role, username=None, linked_customer=None):
    global current_role, current_user, customer_id
    current_role = role
    current_user = username
    customer_id = linked_customer

    # Показываем только доступные для роли разделы.
    for button in buttons.values():
        button.pack_forget()

    visible = (admin_page_names if role == "admin" else
               moderator_page_names if role == "moderator" else
               guest_page_names if role == "guest" else client_page_names)
    for page in visible:
        buttons[page].pack(fill="x", padx=12, pady=3)

    # Customer/guest visual theme; staff sidebar remains unchanged.
    if role in ("user", "guest"):
        sidebar.configure(width=230, fg_color="#102039")
        sidebar_subtitle.configure(text="Смачна піца щодня")
        icons = {"Меню": "🍕", "Кошик": "🛒",
                 "Історія замовлень": "◷", "Акаунт": "👤"}
        for page in visible:
            buttons[page].configure(text=f"{icons.get(page, '')}  {page}",
                                    height=44, corner_radius=10,
                                    fg_color="transparent",
                                    hover_color="#B82030",
                                    text_color="white")
    update_cart_label()

    if role == "admin":
        role_label.configure(text=f"Адміністратор: {username}")
    elif role == "moderator":
        role_label.configure(text=f"Модератор: {username}")
    elif role == "user":
        role_label.configure(text=f"Користувач: {username}")
    else:
        role_label.configure(text="Гість")

    login_frame.destroy()
    show_page("Головна" if role in ("admin", "moderator") else "Меню")


def check_user():
    username = login_entry.get().strip()
    password = password_entry.get()

    linked = authenticate(username, password)
    if linked:
        enter_app("user", username, linked)
    else:
        error_label.configure(text="Невірний логін або пароль користувача")


def open_staff_login():
    panel = ctk.CTkFrame(login_frame, fg_color="#102039", corner_radius=0)
    panel.place(relx=0, rely=0, relwidth=1, relheight=1)
    pizza_background(panel)
    card = make_login_card(panel, width=380, height=510)
    ctk.CTkLabel(card, text="🍕", font=("Arial", 36)).pack(pady=(24, 0))
    ctk.CTkLabel(card, text="PIZZA HOUSE", font=("Arial", 27, "bold"),
                 text_color="#102039").pack(pady=(0, 5))
    ctk.CTkLabel(card, text="Вхід для персоналу", font=("Arial", 18, "bold"),
                 text_color="#102039").pack(pady=(15, 2))
    ctk.CTkLabel(card, text="Адміністратор / Модератор",
                 text_color="#697385").pack(pady=(0, 14))
    staff_login = ctk.CTkEntry(card, width=300, height=40,
                               placeholder_text="Логін персоналу",
                               fg_color="white", text_color="#102039",
                               border_color="#C7CCD5", corner_radius=10)
    staff_login.pack(pady=(0, 10))
    staff_password = ctk.CTkEntry(card, width=300, height=40,
                                  placeholder_text="Пароль", show="*",
                                  fg_color="white", text_color="#102039",
                                  border_color="#C7CCD5", corner_radius=10)
    staff_password.pack(pady=(0, 6))
    feedback = ctk.CTkLabel(card, text="", text_color="#D91D31", height=22,
                            wraplength=300)
    feedback.pack(pady=(0, 4))
    def submit():
        person = authenticate_staff(staff_login.get(), staff_password.get())
        if not person:
            feedback.configure(text="Невірний логін, пароль або доступ заблоковано")
            return
        enter_app(person["role"], person["login"])
    PressButton(card, text="Увійти", width=300, height=42,
                fg_color="#102039", text_color="white",
                font=("Arial", 15, "bold"), command=submit).pack(pady=(4, 14))
    PressButton(card, text="← Повернутися до входу клієнта",
                width=300, height=38, fg_color="white",
                text_color="#102039", border_width=2,
                border_color="#D91D31", command=panel.destroy).pack(pady=(0, 5))
    staff_password.bind("<Return>", lambda event: submit())
    staff_login.focus_set()




def open_registration():
    from pathlib import Path

    dialog = ctk.CTkToplevel(app)
    dialog.title("Реєстрація клієнта")
    dialog.geometry("420x590")
    dialog.transient(app)
    dialog.configure(fg_color="#102039")

    # Prefer the existing Pizza House icon used by the desktop shortcut.
    project_root = Path(__file__).resolve().parent.parent
    icons = [project_root / "pizza_house.ico", project_root / "assets" / "pizza_house.ico",
             project_root / "pizzaHouse.ico", project_root / "assets" / "pizzaHouse.ico"]
    icon = next((path for path in icons if path.is_file()), None)
    if icon is not None:
        try:
            app.iconbitmap(str(icon))
            dialog.iconbitmap(str(icon))
            dialog.after(150, lambda: dialog.winfo_exists() and dialog.iconbitmap(str(icon)))
        except Exception:
            pass

    # Compact layout: all seven fields and the submit button fit 420x590.
    body = ctk.CTkFrame(dialog, fg_color="#102039", corner_radius=0)
    body.pack(fill="both", expand=True, padx=12, pady=8)

    ctk.CTkLabel(body, text="Створити акаунт", font=("Arial", 23, "bold"),
                 text_color="white", height=38).pack(pady=(3, 7))

    fields = {}
    for key, title, secret in [
        ("login", "Логін", False),
        ("password", "Пароль (від 6 символів)", True),
        ("first", "Ім’я", False),
        ("last", "Прізвище", False),
        ("phone", "Телефон", False),
        ("email", "Email", False),
        ("address", "Адреса", False),
    ]:
        ctk.CTkLabel(body, text=title, font=("Arial", 12, "bold"),
                     text_color="white", height=18, anchor="w").pack(
                         fill="x", padx=10, pady=(3, 1))
        # Native text entry instead of font glyph icons that render as squares.
        ent = ctk.CTkEntry(body, show="*" if secret else "",
                           height=36, fg_color="white", text_color="#102039",
                           border_color="#D8E1ED", border_width=1,
                           corner_radius=9, font=("Arial", 13))
        ent.pack(fill="x", padx=10, pady=(0, 2))
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

    ctk.CTkButton(body, text="Зареєструватися", height=42,
                  fg_color="#E32636", hover_color="#F13D4B",
                  text_color="white", corner_radius=13,
                  font=("Arial", 15, "bold"), command=submit).pack(
                      fill="x", padx=10, pady=(12, 5))
    fields["login"].focus_set()




# Patterned client and guest login.
login_frame = ctk.CTkFrame(app, fg_color="#102039", corner_radius=0)
login_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
pizza_background(login_frame)

# The card and its contents use the compact proportions of the reference.
login_card = make_login_card(login_frame, width=380, height=510)
ctk.CTkLabel(login_card, text="🍕", font=("Arial", 36)).pack(pady=(19, 0))
ctk.CTkLabel(login_card, text="PIZZA HOUSE", font=("Arial", 28, "bold"),
             text_color="#102039").pack(pady=(0, 6))
ctk.CTkLabel(login_card, text="Вхід у ваш акаунт", font=("Arial", 17, "bold"),
             text_color="#102039").pack(pady=(17, 16))

login_entry = ctk.CTkEntry(login_card, width=300, height=40,
                           placeholder_text="Логін", fg_color="white",
                           text_color="#102039", border_color="#C7CCD5",
                           corner_radius=10)
login_entry.pack(pady=(0, 12))
password_entry = ctk.CTkEntry(login_card, width=300, height=40,
                              placeholder_text="Пароль", show="*",
                              fg_color="white", text_color="#102039",
                              border_color="#C7CCD5", corner_radius=10)
password_entry.pack(pady=(0, 6))
error_label = ctk.CTkLabel(login_card, text="", text_color="#D91D31",
                           height=20, wraplength=300)
error_label.pack(pady=(0, 4))

PressButton(login_card, text="Увійти", width=300, height=42,
            fg_color="#102039", text_color="white",
            font=("Arial", 15, "bold"), command=check_user).pack(pady=(5, 8))
ctk.CTkLabel(login_card, text="або", text_color="#697385",
             height=24).pack(pady=(0, 6))
PressButton(login_card, text="Продовжити як гість",
            width=300, height=42, fg_color="white", text_color="#102039",
            border_width=2, border_color="#D91D31",
            font=("Arial", 14, "bold"),
            command=lambda: enter_app("guest")).pack(pady=(0, 7))
ctk.CTkButton(login_card, text="Зареєструватися", width=220, height=28,
              fg_color="transparent", text_color="#C41529",
              hover_color="#FFF0F2",
              command=open_registration).pack(pady=(0, 0))
ctk.CTkButton(login_frame, text="Вхід для персоналу", width=200, height=34,
              fg_color="transparent", text_color="white",
              hover_color="#D91D31", command=open_staff_login).place(
              relx=1, rely=1, x=-20, y=-20, anchor="se")
password_entry.bind("<Return>", lambda event: check_user())

def run():
    app.mainloop()
