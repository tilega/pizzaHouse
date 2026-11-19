"""Перегляд та керування відгуками про товари."""
from tkinter import messagebox
import customtkinter as ctk
from ui.theme import COLORS
from reviews_db import (list_product_reviews, get_own_review, save_review,
                        delete_own_review, review_stats_for_menu,
                        list_all_reviews, delete_review_as_admin)


def _label(parent, text, size=12, bold=False, **kwargs):
    return ctk.CTkLabel(parent, text=text, font=('Arial',size,'bold' if bold else 'normal'),
                        text_color=COLORS['navy'], **kwargs)


def open_product_reviews(app, menu_item, customer_id=None, on_change=None):
    """Гість читає відгуки, клієнт із акаунтом може створити/змінити свій."""
    item_id=menu_item['id']
    reviews=list_product_reviews(item_id)
    own=get_own_review(item_id,customer_id)
    dialog=ctk.CTkToplevel(app)
    dialog.title(f"Відгуки — {menu_item['name']}")
    dialog.geometry('670x680')
    dialog.minsize(490,520)
    dialog.transient(app)
    scroll=ctk.CTkScrollableFrame(dialog,fg_color=COLORS['background'])
    scroll.pack(fill='both',expand=True,padx=12,pady=12)
    _label(scroll,menu_item['name'],21,True).pack(anchor='w',padx=12,pady=(12,5))
    stats=review_stats_for_menu().get(item_id)
    summary=(f"★ {stats['average']:.1f} / 5   ·   {stats['count']} відгуків" if stats
             else 'Ще немає оцінок')
    _label(scroll,summary,14,True).pack(anchor='w',padx=12,pady=(0,10))

    if customer_id:
        form=ctk.CTkFrame(scroll,fg_color='white',corner_radius=10)
        form.pack(fill='x',padx=8,pady=(2,16))
        _label(form,'Ваш відгук' if own else 'Залишити відгук',17,True).pack(
            anchor='w',padx=14,pady=(14,5))
        score=ctk.CTkOptionMenu(form,fg_color=COLORS["navy"], button_color=COLORS["navy"], button_hover_color=COLORS["blue"], text_color="white", dropdown_fg_color=COLORS["navy"], dropdown_hover_color=COLORS["blue"], dropdown_text_color="white", values=[f'{i} ★' for i in range(5,0,-1)],width=130)
        score.pack(anchor='w',padx=14,pady=(0,8))
        score.set(f"{own['rating'] if own else 5} ★")
        comment=ctk.CTkTextbox(form,height=105,wrap='word')
        comment.pack(fill='x',padx=14,pady=(0,8))
        if own:comment.insert('1.0',own['comment'])
        else:comment.insert('1.0','')
        hint=_label(form,'Коментар: від 3 до 1000 символів. Один відгук на товар.',11)
        hint.pack(anchor='w',padx=14)
        actions=ctk.CTkFrame(form,fg_color='transparent')
        actions.pack(fill='x',padx=14,pady=(10,14))
        def changed():
            if on_change:
                on_change()
            dialog.destroy()
        def save():
            try:
                save_review(item_id,customer_id,int(score.get().split()[0]),
                            comment.get('1.0','end').strip())
            except Exception as exc:
                messagebox.showerror('Помилка',str(exc),parent=dialog)
                return
            messagebox.showinfo('Відгук','Відгук збережено!',parent=dialog)
            changed()
        ctk.CTkButton(actions,fg_color=COLORS["navy"], hover_color=COLORS["blue"], text_color="white", border_color=COLORS["navy"], text='Оновити відгук' if own else 'Опублікувати відгук',
                      width=175,command=save).pack(side='left')
        if own:
            def remove():
                if not messagebox.askyesno('Видалення','Видалити ваш відгук?',parent=dialog):
                    return
                try:
                    delete_own_review(item_id,customer_id)
                except Exception as exc:
                    messagebox.showerror('Помилка',str(exc),parent=dialog)
                    return
                changed()
            ctk.CTkButton(actions,hover_color=COLORS["error"], text_color="white", border_color=COLORS["red"], text='Видалити мій відгук',width=155,
                          fg_color=COLORS["red"],command=remove).pack(side='left',padx=10)
    else:
        _label(scroll,'Щоб залишити відгук, увійдіть або зареєструйтеся.',12).pack(
            anchor='w',padx=12,pady=(4,14))

    _label(scroll,'Відгуки покупців',17,True).pack(anchor='w',padx=12,pady=(5,9))
    if not reviews:
        _label(scroll,'Будьте першими, хто оцінить цю страву!',13).pack(anchor='w',padx=12,pady=15)
    for review in reviews:
        card=ctk.CTkFrame(scroll,fg_color='white',corner_radius=9)
        card.pack(fill='x',padx=8,pady=5)
        author=review['first_name']+' '+(review['last_name'][:1]+'.' if review['last_name'] else '')
        head=ctk.CTkFrame(card,fg_color='transparent')
        head.pack(fill='x',padx=12,pady=(10,2))
        _label(head,author,13,True).pack(side='left')
        _label(head,'★' * review['rating']+'☆'*(5-review['rating']),14,True).pack(side='right')
        _label(card,review['updated_at'][:16].replace('T',' '),10).pack(anchor='w',padx=12)
        _label(card,review['comment'],12,wraplength=545,justify='left',anchor='w').pack(
            fill='x',padx=12,pady=(6,12))
    dialog.grab_set()


def render_admin_reviews(parent,app,role):
    """Окрема вкладка адміністратора для перегляду та модерації."""
    if role not in ('admin','moderator'):
        _label(parent,'Доступ лише для адміністратора').pack(padx=30)
        return
    filters=ctk.CTkFrame(parent,fg_color='transparent')
    filters.pack(fill='x',padx=30,pady=(0,9))
    search=ctk.CTkEntry(filters,placeholder_text='Пошук за товаром, клієнтом або текстом...',height=36)
    search.pack(side='left',fill='x',expand=True,padx=(0,12))
    rating=ctk.CTkOptionMenu(filters,fg_color=COLORS["navy"], button_color=COLORS["navy"], button_hover_color=COLORS["blue"], text_color="white", dropdown_fg_color=COLORS["navy"], dropdown_hover_color=COLORS["blue"], dropdown_text_color="white", values=['Усі оцінки']+[f'{i} ★' for i in range(5,0,-1)],width=135)
    rating.pack(side='right')
    count=_label(parent,'',12)
    count.pack(anchor='w',padx=30,pady=(0,9))
    scroll=ctk.CTkScrollableFrame(parent,fg_color='transparent')
    scroll.pack(fill='both',expand=True,padx=25,pady=(0,15))
    def refresh(*_):
        for child in scroll.winfo_children(): child.destroy()
        records=list_all_reviews()
        q=search.get().strip().casefold()
        selected=rating.get()
        records=[r for r in records if
                 (selected=='Усі оцінки' or r['rating']==int(selected[0]))
                 and (not q or q in (' '.join((r['product_name'],r['first_name'],
                    r['last_name'],r['customer_id'],r['comment']))).casefold())]
        count.configure(text=f'Знайдено відгуків: {len(records)}')
        if not records:
            _label(scroll,'Відгуків не знайдено',13).pack(pady=25)
        for r in records:
            card=ctk.CTkFrame(scroll,fg_color='white',corner_radius=10)
            card.pack(fill='x',padx=5,pady=5)
            head=ctk.CTkFrame(card,fg_color='transparent')
            head.pack(fill='x',padx=14,pady=(10,1))
            _label(head,r['product_name'],16,True).pack(side='left')
            _label(head,f"★ {r['rating']} / 5",14,True).pack(side='right')
            _label(card,f"{r['first_name']} {r['last_name']} · {r['customer_id']} · {r['updated_at']}",
                   11).pack(anchor='w',padx=14)
            _label(card,r['comment'],12,wraplength=640,justify='left',anchor='w').pack(
                fill='x',padx=14,pady=(6,9))
            def remove(review_id=r['id']):
                if not messagebox.askyesno('Модерація','Видалити цей відгук без можливості відновлення?',parent=app):
                    return
                try: delete_review_as_admin(review_id)
                except Exception as exc:
                    messagebox.showerror('Помилка',str(exc),parent=app)
                    return
                refresh()
            ctk.CTkButton(card,hover_color=COLORS["error"], text_color="white", border_color=COLORS["red"], text='Видалити відгук',width=150,height=30,
                          fg_color=COLORS["red"],command=remove).pack(anchor='e',padx=14,pady=(0,12))
    search.bind('<KeyRelease>',refresh)
    rating.configure(command=refresh)
    refresh()
