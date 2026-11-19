"""Client and guest menu, two cards per row. No database schema changes."""

from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageOps, ImageDraw, ImageChops, UnidentifiedImageError

from database import db_connection, list_menu_catalog
from reviews_db import review_stats_for_menu
from ui.photos import resolve_photo_path
from ui.reviews_page import open_product_reviews
from ui.theme import MENU_CATEGORIES, format_price
from weekly_special_db import get_weekly_special

NAVY = "#102039"
RED = "#D92335"
RED_HOVER = "#F03749"
BORDER = "#D7E2F2"
MUTED = "#D0D9E7"
PANEL = NAVY
WHITE = "#FFFFFF"


def adaptive_photo(path, limits=(138, 156)):
    """Keep source aspect ratio and draw a pixel-tight, rounded red outline."""
    resolved = resolve_photo_path(path)
    if not resolved:
        return None, (0, 0)
    try:
        with Image.open(resolved) as source:
            source.load()
            photo = ImageOps.exif_transpose(source).convert("RGBA")
            photo.thumbnail(limits, Image.Resampling.LANCZOS)
            if not photo.width or not photo.height:
                return None, (0, 0)
            # The outline is part of the image itself, so there is no
            # separate rectangular widget leaving gaps around the photo.
            border = 3
            w, h = photo.size
            radius = min(15, w // 3, h // 3)
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, w - 1, h - 1), radius=max(1, radius - border), fill=255)
            photo.putalpha(ImageChops.multiply(photo.getchannel("A"), mask))
            framed = Image.new("RGBA", (w + border * 2, h + border * 2), (0, 0, 0, 0))
            outline_mask = Image.new("L", framed.size, 0)
            ImageDraw.Draw(outline_mask).rounded_rectangle(
                (0, 0, framed.width - 1, framed.height - 1), radius=radius, fill=255)
            outline = Image.new("RGBA", framed.size, RED)
            framed.paste(outline, (0, 0), outline_mask)
            framed.alpha_composite(photo, (border, border))
            return ctk.CTkImage(light_image=framed, dark_image=framed,
                                size=framed.size), framed.size
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError, ValueError):
        return None, (0, 0)


def txt(parent, value, size=13, weight="normal", color=NAVY, **kwargs):
    return ctk.CTkLabel(parent, text=value, font=("Arial", size, weight),
                        text_color=color, **kwargs)


def popularity_by_product():
    """Order counts for sorting; exclude canceled orders, as in staff statistics."""
    with db_connection() as conn:
        rows = conn.execute("""
            SELECT l.menu_id, COALESCE(SUM(l.quantity), 0) AS qty
            FROM order_lines l JOIN orders o ON o.order_id = l.order_id
            WHERE o.status <> 'Скасоване'
            GROUP BY l.menu_id
        """).fetchall()
    return {row["menu_id"]: row["qty"] for row in rows}


def filtered_items(items, query, category, sort_by, ratings, popularity):
    q = query.strip().casefold()
    chosen = [item for item in items
              if (category == "Усі" or item["category"] == category)
              and q in item["name"].casefold()]
    name = lambda item: item["name"].casefold()
    if sort_by == "За назвою":
        chosen.sort(key=name)
    elif sort_by == "Від дешевих":
        chosen.sort(key=lambda x: (x["price"], name(x)))
    elif sort_by == "Від дорогих":
        chosen.sort(key=lambda x: (-x["price"], name(x)))
    elif sort_by == "За рейтингом":
        chosen.sort(key=lambda x: (-ratings.get(x["id"], {}).get("average", 0),
                                   -ratings.get(x["id"], {}).get("count", 0), name(x)))
    else:
        chosen.sort(key=lambda x: (-popularity.get(x["id"], 0), name(x)))
    return chosen


def _photo_slot(parent, path, max_size=(128, 152)):
    """The visible frame follows the actual image dimensions exactly."""
    slot = ctk.CTkFrame(parent, width=150, height=180, fg_color="transparent")
    slot.grid_propagate(False)
    img, (width, height) = adaptive_photo(path, max_size)
    if img is None:
        box = ctk.CTkFrame(slot, width=126, height=118, fg_color=WHITE,
                           border_width=2, border_color=RED, corner_radius=14)
        box.place(relx=.5, rely=.5, anchor="center")
        box.pack_propagate(False)
        txt(box, "🍕\nФото немає", size=12, color=NAVY,
            justify="center").pack(expand=True)
    else:
        label = ctk.CTkLabel(slot, text="", image=img,
                             width=width, height=height)
        label.place(relx=.5, rely=.5, anchor="center")
        label._photo_ref = img
    return slot


def _weekly_banner(parent):
    banner = ctk.CTkFrame(parent, fg_color=RED, corner_radius=15)
    banner.pack(fill="x", padx=5, pady=(2, 17))
    special = get_weekly_special()
    if not special:
        txt(banner, "🔥  ХІТ ТИЖНЯ", size=13, weight="bold", color="white").pack(
            anchor="w", padx=19, pady=(15, 3))
        txt(banner, "За останні 7 днів ще немає замовлень піци або закусок.",
            size=12, color="#FFE4E8", wraplength=520, justify="left").pack(
                anchor="w", padx=19, pady=(0, 15))
        return
    image = _photo_slot(banner, special.get("image_path"), (115, 112))
    image.configure(width=132, height=128)
    image.pack(side="left", padx=(14, 8), pady=8)
    copy = ctk.CTkFrame(banner, fg_color="transparent")
    copy.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=(13, 12))
    txt(copy, "🔥  ХІТ ТИЖНЯ", size=13, weight="bold", color="white").pack(anchor="w")
    txt(copy, special["name"], size=21, weight="bold", color="white",
        wraplength=490, justify="left").pack(anchor="w", pady=(5, 4))
    txt(copy, f"Замовили {special['portions']} порц. за останні 7 днів",
        size=12, color="#FFE4E8").pack(anchor="w")


def _product_card(parent, item, rating, cart, refresh_cart_badge, app,
                  customer_id, redraw, show_notice):
    card = ctk.CTkFrame(parent, height=324, fg_color=PANEL, corner_radius=18,
                        border_width=1, border_color="#253E5D")
    card.grid_propagate(False)
    card.grid_columnconfigure(0, minsize=168)
    card.grid_columnconfigure(1, weight=1)
    card.grid_rowconfigure(0, weight=1)

    photo_slot = _photo_slot(card, item.get("image_path"), (130, 154))
    photo_slot.grid(row=0, column=0, sticky="n", padx=(14, 4), pady=(14, 0))

    right = ctk.CTkFrame(card, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew", padx=(16, 14), pady=(12, 4))

    txt(right, item["name"], size=18, weight="bold", color=WHITE,
        wraplength=210, justify="left", anchor="w").pack(anchor="w")
    txt(right, format_price(item["price"]), size=17, weight="bold", color=RED).pack(
        anchor="w", pady=(6, 0))
    weight = item.get("weight_g")
    summary = item["category"] + (f"  ·  {weight} г" if weight else "")
    txt(right, summary, size=12, color=MUTED).pack(anchor="w", pady=(2, 7))

    recipe = item.get("recipe") or []
    ingredients = ", ".join(part["name"] for part in recipe)
    if ingredients:
        short = ingredients if len(ingredients) <= 105 else ingredients[:102].rstrip() + "…"
        txt(right, "Склад: " + short, size=11, color=WHITE,
            wraplength=214, justify="left", anchor="w").pack(anchor="w")
    else:
        txt(right, "Склад не вказано", size=11, color=WHITE).pack(anchor="w")

    stats = rating.get(item["id"])
    caption = (f"★ {stats['average']:.1f} · {stats['count']} відгуків"
               if stats else "☆ Ще немає відгуків")
    txt(right, caption, size=11, color=WHITE).pack(anchor="w", pady=(8, 4))

    # Actions span BOTH card columns: their width is not limited by the text column.
    actions = ctk.CTkFrame(card, fg_color="transparent")
    actions.grid(row=1, column=0, columnspan=2, sticky="ew",
                 padx=16, pady=(0, 15))

    def add(item_id=item["id"], title=item["name"]):
        cart[item_id] = cart.get(item_id, 0) + 1
        refresh_cart_badge()
        show_notice(f"✓ {title} додано до кошика")

    ctk.CTkButton(actions, text="+ До кошика", height=40,
                  corner_radius=11, fg_color=RED, hover_color=RED_HOVER,
                  text_color="white", font=("Arial", 14, "bold"),
                  command=add).pack(fill="x", pady=(0, 8))
    ctk.CTkButton(actions, text="★ Відгуки / оцінити", height=38,
                  corner_radius=11, fg_color=WHITE, hover_color="#E8EDF4",
                  text_color=NAVY, border_width=1, border_color="#C9D4E2",
                  font=("Arial", 12, "bold"),
                  command=lambda product=item: open_product_reviews(
                      app, product, customer_id, redraw)).pack(fill="x")
    card.bind("<Enter>", lambda _e: card.configure(border_color="#D92335"), add="+")
    card.bind("<Leave>", lambda _e: card.configure(border_color="#253E5D"), add="+")
    return card


def render_modern_menu(parent, app, cart, refresh_cart_badge, customer_id=None):
    scroller = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    scroller.pack(fill="both", expand=True, padx=(23, 17), pady=(0, 13))
    _weekly_banner(scroller)

    toolbar = ctk.CTkFrame(scroller, fg_color="transparent")
    toolbar.pack(fill="x", padx=5, pady=(0, 10))
    search = ctk.CTkEntry(toolbar, width=280, height=39, corner_radius=10,
                          fg_color="white", border_color=BORDER,
                          placeholder_text="Пошук страви...")
    search.pack(side="left", fill="x", expand=True, padx=(0, 12))
    sort_options = ["За популярністю", "За назвою", "Від дешевих",
                    "Від дорогих", "За рейтингом"]
    sort = ctk.CTkOptionMenu(toolbar, width=170, height=39,
                             values=sort_options, fg_color=NAVY,
                             button_color=NAVY, button_hover_color=RED,
                             dropdown_fg_color="white", text_color="white")
    sort.pack(side="right")

    filters = ctk.CTkFrame(scroller, fg_color="transparent")
    filters.pack(fill="x", padx=5, pady=(0, 9))
    state = {"category": "Усі"}
    chips = {}

    toast = txt(scroller, "", size=12, weight="bold", color="#1E7A44")
    toast.pack(anchor="w", padx=6)
    toast.pack_forget()
    toast_job = {"id": None}

    def show_notice(message):
        if toast_job["id"] is not None:
            try:
                toast.after_cancel(toast_job["id"])
            except Exception:
                pass
        toast.configure(text=message)
        toast.pack(anchor="w", padx=6, pady=(0, 5))
        def hide():
            toast_job["id"] = None
            if toast.winfo_exists():
                toast.pack_forget()
        toast_job["id"] = toast.after(1500, hide)

    grid = ctk.CTkFrame(scroller, fg_color="transparent")
    grid.pack(fill="x", padx=0, pady=(0, 14))
    for column in range(2):
        grid.grid_columnconfigure(column, weight=1, uniform="menu_cards")

    def redraw(*_):
        for widget in grid.winfo_children():
            widget.destroy()
        items = list_menu_catalog()
        ratings = review_stats_for_menu()
        popularity = popularity_by_product()
        shown = filtered_items(items, search.get(), state["category"],
                               sort.get(), ratings, popularity)
        if not shown:
            txt(grid, "За вашим запитом нічого не знайдено.",
                size=14, color=MUTED).grid(row=0, column=0, columnspan=2,
                                           padx=12, pady=24)
            return
        for index, item in enumerate(shown):
            card = _product_card(grid, item, ratings, cart, refresh_cart_badge,
                                 app, customer_id, redraw, show_notice)
            card.grid(row=index // 2, column=index % 2, sticky="nsew",
                      padx=5, pady=6)

    def choose_category(value):
        state["category"] = value
        for key, button in chips.items():
            active = (key == value)
            button.configure(fg_color=RED if active else "white",
                             text_color="white" if active else NAVY,
                             border_width=0 if active else 1,
                             border_color=RED if active else BORDER)
        redraw()

    for value in ["Усі"] + list(MENU_CATEGORIES):
        button = ctk.CTkButton(filters, text=value, width=85, height=32,
                               corner_radius=16, fg_color="white",
                               text_color=NAVY, hover_color="#FCE7E9",
                               border_width=1, border_color=BORDER,
                               command=lambda selected=value: choose_category(selected))
        button.pack(side="left", padx=(0, 7))
        chips[value] = button
    sort.configure(command=lambda _: redraw())
    search.bind("<KeyRelease>", lambda _: redraw())
    choose_category("Усі")
