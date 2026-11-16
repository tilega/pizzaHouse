"""Адміністративний розділ закупівель і постачальників."""
from datetime import date
from tkinter import messagebox
import sqlite3
import customtkinter as ctk
from ui.people_page import _ScrollTable
from ui.theme import COLORS,format_quantity,format_price
from database import list_ingredients
from procurement_db import (
    list_suppliers,get_supplier,add_supplier,update_supplier,delete_supplier,
    list_purchases,get_purchase,save_purchase,delete_purchase,
)


def render_procurement_page(content,app,role):
    if role!='admin':return
    top=ctk.CTkFrame(content,fg_color='transparent')
    top.pack(fill='x',padx=30,pady=(0,8))
    mode=ctk.CTkSegmentedButton(top,values=['Закупівлі','Постачальники'],
                                fg_color=COLORS['header'],selected_color=COLORS['blue'],
                                selected_hover_color=COLORS['blue_hover'])
    mode.pack(side='left')
    new_button=ctk.CTkButton(top,text='+ Нова закупівля',width=175,height=36,
                             fg_color=COLORS['blue'],hover_color=COLORS['blue_hover'])
    new_button.pack(side='right')
    search=ctk.CTkEntry(content,height=37,placeholder_text='Пошук за ID, назвою, датою або інгредієнтом')
    search.pack(fill='x',padx=30,pady=(0,6))
    count=ctk.CTkLabel(content,text='',font=('Arial',12),text_color=COLORS['muted'])
    count.pack(anchor='w',padx=30,pady=(0,7))
    table=_ScrollTable(content)

    def render_grid(columns,records,renderer):
        table.clear()
        table.set_columns([width for _,width in columns])
        for j,(heading,_) in enumerate(columns):
            widget=ctk.CTkLabel(table.inner,text=heading,font=('Arial',11,'bold'),
                                text_color=COLORS['body_heading'],fg_color=COLORS['header'],
                                height=40,width=1,anchor='center')
            widget.grid(row=0,column=j,sticky='nsew',padx=2,pady=2)
            table.enable_wheel(widget)
        if not records:
            ctk.CTkLabel(table.inner,text='Нічого не знайдено',height=70,
                         text_color=COLORS['muted']).grid(row=1,column=0,columnspan=len(columns),sticky='ew')
        for i,item in enumerate(records,1):renderer(i,item)
        table.inner.update_idletasks()
        table._resize_content()

    def label_cell(row,col,text,width,background,accent=None):
        w=ctk.CTkLabel(table.inner,text=str(text),font=('Arial',11),
            text_color=accent or COLORS['navy'],fg_color=background,
            anchor='center',justify='center',height=60,width=1,wraplength=max(width-12,40))
        w.grid(row=row,column=col,sticky='nsew',padx=2,pady=2)
        table.enable_wheel(w)

    def action_cell(row,col,background,first,second):
        frame=ctk.CTkFrame(table.inner,fg_color=background,height=60)
        frame.grid(row=row,column=col,sticky='nsew',padx=2,pady=2)
        frame.grid_columnconfigure(0,weight=1)
        frame.grid_columnconfigure(3,weight=1)
        edit=ctk.CTkButton(frame,text='Змінити',width=63,height=29,
            fg_color=COLORS['blue'],hover_color=COLORS['blue_hover'],command=first)
        edit.grid(row=0,column=1,padx=(0,3),pady=15)
        delete=ctk.CTkButton(frame,text='Видалити',width=70,height=29,
            fg_color=COLORS['soft_danger'],text_color=COLORS['red'],
            hover_color=COLORS['hover_danger'],command=second)
        delete.grid(row=0,column=2,padx=(3,0),pady=15)
        for el in [frame,edit,delete]:table.enable_wheel(el)

    def refresh(*_):
        try:
            term=search.get().strip().casefold()
            if mode.get()=='Постачальники':
                all_items=list_suppliers()
                shown=[r for r in all_items if not term or any(term in str(x).casefold() for x in r.values())]
                count.configure(text=f'Показано: {len(shown)} із {len(all_items)} постачальників')
                # 6 колонок разом вміщаються у вікно 1050 px без порожньої прокрутки.
                widths=[55,125,100,145,133,151]
                heads=['ID','Назва','Телефон','Адреса','Email','Дії']
                def draw(row,item):
                    shade=COLORS['white'] if row%2 else COLORS['alt_row']
                    for c,key in enumerate(['supplier_id','name','phone','address','email']):
                        label_cell(row,c,item[key] or '—',widths[c],shade)
                    action_cell(row,5,shade,
                        lambda pk=item['supplier_id']:open_supplier(pk),
                        lambda pk=item['supplier_id']:remove_supplier(pk))
                render_grid(list(zip(heads,widths)),shown,draw)
            else:
                all_items=list_purchases()
                shown=[r for r in all_items if not term or any(term in str(r.get(k,'')).casefold()
                    for k in ['purchase_id','purchase_date','supplier_id','supplier_name','note','ingredients'])]
                count.configure(text=f'Показано: {len(shown)} із {len(all_items)} закупівель')
                widths=[85,125,250,100,130,250,210,165]
                heads=['ID','Дата','Постачальник','Позицій','Сума, грн','Інгредієнти','Примітка','Дії']
                def draw(row,item):
                    shade=COLORS['white'] if row%2 else COLORS['alt_row']
                    vals=[item['purchase_id'],item['purchase_date'],
                          item['supplier_name']+' ('+item['supplier_id']+')',
                          item['lines_count'],format_price(item['total']),
                          item['ingredients'] or '—',item['note'] or '—']
                    for c,value in enumerate(vals):label_cell(row,c,value,widths[c],shade)
                    action_cell(row,7,shade,
                        lambda pk=item['purchase_id']:open_purchase(pk),
                        lambda pk=item['purchase_id']:remove_purchase(pk))
                render_grid(list(zip(heads,widths)),shown,draw)
        except (sqlite3.Error,ValueError) as exc:
            messagebox.showerror('Помилка БД',str(exc),parent=app)

    def open_supplier(pk=None):
        try:existing=get_supplier(pk) if pk else None
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка',str(exc),parent=app);return
        dialog=ctk.CTkToplevel(app)
        dialog.title('Редагувати постачальника' if pk else 'Новий постачальник')
        dialog.geometry('520x520');dialog.minsize(450,475);dialog.transient(app)
        body=ctk.CTkFrame(dialog,fg_color=COLORS['white'])
        body.pack(fill='both',expand=True,padx=18,pady=18)
        ctk.CTkLabel(body,text=('Редагування '+pk) if pk else 'Додати постачальника',
            font=('Arial',19,'bold'),text_color=COLORS['navy']).pack(anchor='w',padx=18,pady=(12,15))
        entries={}
        for key,label in [('name','Назва'),('phone','Телефон'),('address','Адреса'),('email','Email')]:
            ctk.CTkLabel(body,text=label,text_color=COLORS['navy']).pack(anchor='w',padx=18)
            ent=ctk.CTkEntry(body,height=35)
            ent.pack(fill='x',padx=18,pady=(3,12))
            if existing:ent.insert(0,existing[key] or '')
            entries[key]=ent
        feedback=ctk.CTkLabel(body,text='',text_color=COLORS['red'],wraplength=435)
        feedback.pack(padx=18)
        def save():
            vals=[entries[key].get() for key in ['name','phone','address','email']]
            try:
                if pk:update_supplier(pk,*vals)
                else:add_supplier(*vals)
            except (ValueError,sqlite3.Error) as exc:
                feedback.configure(text=str(exc));return
            dialog.destroy();refresh()
        ctk.CTkButton(body,text='Зберегти',command=save,fg_color=COLORS['blue']).pack(pady=10)
        dialog.grab_set()

    def remove_supplier(pk):
        if not messagebox.askyesno('Підтвердження',f'Видалити постачальника {pk}?',parent=app):return
        try:delete_supplier(pk)
        except sqlite3.IntegrityError:
            messagebox.showerror('Видалення неможливе','Постачальник є у закупівлях.',parent=app);return
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка',str(exc),parent=app);return
        refresh()

    def open_purchase(pk=None):
        try:
            existing=get_purchase(pk) if pk else None
            suppliers=list_suppliers();ingredients=list_ingredients()
        except sqlite3.Error as exc:
            messagebox.showerror('Помилка БД',str(exc),parent=app);return
        if not suppliers or not ingredients:
            messagebox.showwarning('Немає даних','Додайте постачальників та інгредієнти.',parent=app);return
        dialog=ctk.CTkToplevel(app)
        dialog.title('Закупівля '+pk if pk else 'Нова закупівля')
        dialog.geometry('850x690');dialog.minsize(720,580);dialog.transient(app)
        frame=ctk.CTkScrollableFrame(dialog,fg_color=COLORS['white'])
        frame.pack(fill='both',expand=True,padx=15,pady=15)
        ctk.CTkLabel(frame,text=('Редагування '+pk if pk else 'Нова закупівля'),
            font=('Arial',20,'bold'),text_color=COLORS['navy']).pack(anchor='w',padx=17,pady=(10,12))
        ctk.CTkLabel(frame,text='Постачальник',text_color=COLORS['navy']).pack(anchor='w',padx=17)
        supplier_labels={f"{s['supplier_id']} — {s['name']}":s['supplier_id'] for s in suppliers}
        supplier_box=ctk.CTkOptionMenu(frame,values=list(supplier_labels),fg_color=COLORS['blue'])
        supplier_box.pack(fill='x',padx=17,pady=(3,10))
        if existing:
            supplier_box.set(next(label for label,sid in supplier_labels.items() if sid==existing['supplier_id']))
        ctk.CTkLabel(frame,text='Дата (РРРР-ММ-ДД)',text_color=COLORS['navy']).pack(anchor='w',padx=17)
        date_entry=ctk.CTkEntry(frame,height=35)
        date_entry.pack(fill='x',padx=17,pady=(3,10))
        date_entry.insert(0,existing['purchase_date'] if existing else date.today().isoformat())
        ctk.CTkLabel(frame,text='Інгредієнти, кількість і ціна за 1 кг/л/шт',
            font=('Arial',13,'bold'),text_color=COLORS['navy']).pack(anchor='w',padx=17,pady=(5,6))
        list_frame=ctk.CTkFrame(frame,fg_color=COLORS['alt_row'])
        list_frame.pack(fill='x',padx=17,pady=(0,7))
        ingredient_labels={f"{i['code']} — {i['name']} ({i['unit']})":i for i in ingredients}
        by_id={i['id']:label for label,i in ingredient_labels.items()}
        lines=[]
        def add_line(ing_id=None,quantity='1',price=None):
            holder=ctk.CTkFrame(list_frame,fg_color='transparent')
            holder.pack(fill='x',padx=8,pady=6)
            ing_box=ctk.CTkOptionMenu(holder,values=list(ingredient_labels),width=310,
                fg_color=COLORS['blue'],button_color=COLORS['navy'])
            ing_box.pack(side='left',fill='x',expand=True,padx=(0,7))
            if ing_id in by_id:ing_box.set(by_id[ing_id])
            qty=ctk.CTkEntry(holder,width=90,placeholder_text='Кількість')
            qty.pack(side='left',padx=(0,7));qty.insert(0,str(quantity))
            price_box=ctk.CTkEntry(holder,width=95,placeholder_text='Ціна')
            price_box.pack(side='left',padx=(0,7))
            item=ingredient_labels[ing_box.get()]
            price_box.insert(0,str(price if price is not None else item['price']))
            def update_price(value):
                ingredient=ingredient_labels[value]
                price_box.delete(0,'end');price_box.insert(0,str(ingredient['price']))
            ing_box.configure(command=update_price)
            line={'holder':holder,'ingredient':ing_box,'quantity':qty,'price':price_box}
            lines.append(line)
            def remove_line():
                lines.remove(line);holder.destroy()
            ctk.CTkButton(holder,text='×',width=30,fg_color=COLORS['soft_danger'],
                text_color=COLORS['red'],hover_color=COLORS['hover_danger'],
                command=remove_line).pack(side='left')
        if existing:
            for line in existing['lines']:
                add_line(line['ingredient_id'],str(line['quantity']),line['unit_price'])
        else:add_line()
        ctk.CTkButton(frame,text='+ Додати інгредієнт',fg_color=COLORS['soft_button'],
            text_color=COLORS['navy'],hover_color=COLORS['hover_button'],
            command=add_line).pack(anchor='w',padx=17,pady=(3,12))
        ctk.CTkLabel(frame,text='Примітка (необов’язково)',text_color=COLORS['navy']).pack(anchor='w',padx=17)
        note=ctk.CTkEntry(frame,height=35)
        note.pack(fill='x',padx=17,pady=(3,8))
        if existing:note.insert(0,existing['note'])
        feedback=ctk.CTkLabel(frame,text='',text_color=COLORS['red'],wraplength=680)
        feedback.pack(padx=15)
        def save():
            raw=[]
            for line in lines:
                ingredient=ingredient_labels[line['ingredient'].get()]
                raw.append((ingredient['id'],line['quantity'].get(),line['price'].get()))
            try:
                saved=save_purchase(pk,supplier_labels[supplier_box.get()],date_entry.get(),raw,note.get())
            except (ValueError,sqlite3.Error) as exc:
                feedback.configure(text=str(exc));return
            dialog.destroy();refresh()
            messagebox.showinfo('Збережено',f'Закупівля {saved} збережена. Залишки оновлено.',parent=app)
        ctk.CTkButton(frame,text='Зберегти закупівлю',fg_color=COLORS['blue'],
                      command=save).pack(pady=(8,16))
        dialog.grab_set()

    def remove_purchase(pk):
        if not messagebox.askyesno('Підтвердження',
            f'Видалити закупівлю {pk}? Надходження будуть відняті зі складу.',parent=app):return
        try:delete_purchase(pk)
        except (sqlite3.Error,ValueError) as exc:
            messagebox.showerror('Видалення неможливе',str(exc),parent=app);return
        refresh()

    def change_mode(value):
        if value=='Постачальники':
            new_button.configure(text='+ Додати постачальника',command=lambda:open_supplier())
        else:new_button.configure(text='+ Нова закупівля',command=lambda:open_purchase())
        refresh()
    mode.configure(command=change_mode)
    mode.set('Закупівлі')
    new_button.configure(command=lambda:open_purchase())
    search.bind('<KeyRelease>',refresh)
    refresh()
