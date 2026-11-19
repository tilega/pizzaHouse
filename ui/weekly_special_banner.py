"""Compact weekly top-dish banner for customer/guest menu."""
import customtkinter as ctk
from ui.photos import load_thumbnail
from ui.theme import COLORS
from weekly_special_db import get_weekly_special


def _label(parent, text, size=13, bold=False, color=None, **kwargs):
    return ctk.CTkLabel(parent, text=text,
        font=('Arial', size, 'bold' if bold else 'normal'),
        text_color=color or COLORS['navy'], **kwargs)


def render_weekly_banner(parent):
    """Show the week's most popular dish, or an honest empty state."""
    special = get_weekly_special()
    banner = ctk.CTkFrame(parent, fg_color=COLORS['card_orange'],
                          corner_radius=12, border_width=1,
                          border_color=COLORS['light_border'])
    banner.pack(fill='x', padx=30, pady=(0, 14))

    if not special:
        _label(banner, '🔥 Страва тижня', 15, True).pack(
            anchor='w', padx=18, pady=(12, 2))
        _label(banner, 'Поки немає замовлень страв за останні 7 днів.',
               12, color=COLORS['muted']).pack(
            anchor='w', padx=18, pady=(0, 12))
        return

    image = load_thumbnail(special.get('image_path'), (78, 70))
    if image:
        image_frame = ctk.CTkFrame(banner, width=88, height=78,
                                   fg_color='white', corner_radius=8)
        image_frame.pack(side='left', padx=(13, 12), pady=12)
        image_frame.pack_propagate(False)
        ctk.CTkLabel(image_frame, text='', image=image).pack(expand=True)

    text = ctk.CTkFrame(banner, fg_color='transparent')
    text.pack(side='left', fill='both', expand=True, padx=(0, 14), pady=12)
    _label(text, '🔥 Найпопулярніша страва тижня', 12, True,
           color=COLORS['orange']).pack(anchor='w')
    _label(text, special['name'], 17, True, wraplength=500,
           justify='left').pack(anchor='w', pady=(3, 1))
    _label(text, f"Замовили {special['portions']} порц. за останні 7 днів",
           12, color=COLORS['muted']).pack(anchor='w')
