"""Адміністративні права та власний пароль персоналу."""
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import COLORS
from staff_db import (
    list_staff_accounts, create_moderator, set_moderator_enabled,
    reset_moderator_password, delete_moderator, change_staff_password
)


def _heading(parent, text):
    ctk.CTkLabel(parent, text=text, font=('Arial', 17, 'bold'),
                 text_color=COLORS['navy']).pack(anchor='w', padx=18, pady=(14,8))


def render_staff_page(parent, app, role):
    if role != 'admin':
        return
    form = ctk.CTkFrame(parent, fg_color='white', corner_radius=12)
    form.pack(fill='x', padx=30, pady=(0,12))
    _heading(form, 'Додати модератора')
    ctk.CTkLabel(form, text='Новий модератор отримує обмежений доступ до панелі керування.',
                 text_color=COLORS['muted']).pack(anchor='w', padx=18)
    row = ctk.CTkFrame(form, fg_color='transparent')
    row.pack(fill='x', padx=18, pady=(8,16))
    new_login = ctk.CTkEntry(row, placeholder_text='Логін', width=190)
    new_login.pack(side='left', padx=(0,8))
    new_password = ctk.CTkEntry(row, placeholder_text='Пароль (від 8 символів)', show='*', width=205)
    new_password.pack(side='left', padx=(0,8))

    records_frame = ctk.CTkScrollableFrame(parent, fg_color='transparent')
    records_frame.pack(fill='both', expand=True, padx=25, pady=(0,15))

    def refresh():
        for child in records_frame.winfo_children():
            child.destroy()
        _heading(records_frame, 'Облікові записи персоналу')
        for person in list_staff_accounts():
            item = ctk.CTkFrame(records_frame, fg_color='white', corner_radius=10)
            item.pack(fill='x', padx=4, pady=5)
            title = f"{person['login']} · {'Головний адміністратор' if person['role']=='admin' else 'Модератор'}"
            ctk.CTkLabel(item,text=title,font=('Arial',14,'bold'),text_color=COLORS['navy']).pack(
                anchor='w',padx=13,pady=(10,1))
            status = 'Активний' if person['enabled'] else 'Заблокований'
            ctk.CTkLabel(item,text=f"{status} · створено {person['created_at']}",
                         text_color=COLORS['muted'],font=('Arial',11)).pack(anchor='w',padx=13)
            if person['role'] != 'moderator':
                ctk.CTkLabel(item,text='Повний доступ · захищений від видалення',
                             font=('Arial',11),text_color=COLORS['muted']).pack(
                                 anchor='w',padx=13,pady=(3,10))
                continue
            controls = ctk.CTkFrame(item, fg_color='transparent')
            controls.pack(anchor='w', padx=12, pady=(7,12))
            login = person['login']
            def toggle(key=login, is_enabled=person['enabled']):
                try:
                    set_moderator_enabled(key, not is_enabled)
                    refresh()
                except Exception as exc:
                    messagebox.showerror('Помилка',str(exc),parent=app)
            ctk.CTkButton(controls, fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='Заблокувати' if person['enabled'] else 'Активувати',
                          width=114, command=toggle).pack(side='left',padx=(0,7))
            def change_password(key=login):
                dialog = ctk.CTkToplevel(app)
                dialog.title('Новий пароль модератора')
                dialog.geometry('385x245');dialog.transient(app)
                ctk.CTkLabel(dialog,text=f'Новий пароль для {key}',font=('Arial',16,'bold')).pack(pady=(23,12))
                entry = ctk.CTkEntry(dialog,show='*',placeholder_text='Новий пароль (8+ символів)',width=290)
                entry.pack(pady=8)
                def save():
                    try: reset_moderator_password(key,entry.get())
                    except Exception as exc:
                        messagebox.showerror('Помилка',str(exc),parent=dialog);return
                    dialog.destroy();messagebox.showinfo('Пароль','Пароль змінено.',parent=app)
                ctk.CTkButton(dialog,fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='Зберегти',command=save).pack(pady=12)
                dialog.after(50, lambda: dialog.grab_set() if dialog.winfo_exists() else None)
            ctk.CTkButton(controls,fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='Новий пароль',width=120,
                          command=change_password).pack(side='left',padx=(0,7))
            def remove(key=login):
                if not messagebox.askyesno('Видалення',f'Видалити акаунт «{key}»?',parent=app):return
                try:delete_moderator(key)
                except Exception as exc:
                    messagebox.showerror('Помилка',str(exc),parent=app);return
                refresh()
            ctk.CTkButton(controls,hover_color=COLORS["error"], text_color="white", border_color=COLORS["red"], text='Видалити',width=95,fg_color=COLORS["red"],
                          command=remove).pack(side='left')

    def create():
        try:
            create_moderator(new_login.get(), new_password.get())
        except Exception as exc:
            messagebox.showerror('Помилка',str(exc),parent=app);return
        new_login.delete(0,'end');new_password.delete(0,'end')
        refresh()
        messagebox.showinfo('Готово','Обліковий запис модератора створено.',parent=app)
    ctk.CTkButton(row,fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='+ Створити',width=110,command=create).pack(side='left')
    refresh()


def render_staff_password_page(parent, app, login):
    box=ctk.CTkFrame(parent,fg_color='white',corner_radius=12)
    box.pack(fill='x',padx=30,pady=(0,12))
    _heading(box,f'Змінити пароль: {login}')
    old = ctk.CTkEntry(box,show='*',placeholder_text='Поточний пароль',width=340)
    old.pack(anchor='w',padx=18,pady=5)
    new = ctk.CTkEntry(box,show='*',placeholder_text='Новий пароль (від 8 символів)',width=340)
    new.pack(anchor='w',padx=18,pady=5)
    confirm = ctk.CTkEntry(box,show='*',placeholder_text='Повторіть новий пароль',width=340)
    confirm.pack(anchor='w',padx=18,pady=5)
    def save():
        if new.get()!=confirm.get():
            messagebox.showerror('Помилка','Паролі не збігаються',parent=app);return
        try: change_staff_password(login,old.get(),new.get())
        except Exception as exc:
            messagebox.showerror('Помилка',str(exc),parent=app);return
        old.delete(0,'end');new.delete(0,'end');confirm.delete(0,'end')
        messagebox.showinfo('Готово','Пароль змінено',parent=app)
    ctk.CTkButton(box,fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='Змінити пароль',command=save,width=175).pack(
        anchor='w',padx=18,pady=(12,18))
    ctk.CTkLabel(parent,text='Пароль використовується лише для входу персоналу.',
                 text_color=COLORS['muted']).pack(anchor='w',padx=32)
