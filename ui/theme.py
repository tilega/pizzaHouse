"""Візуальні налаштування та форматування значень."""
from decimal import Decimal

COLORS = {
    "navy": "#192B3A",
    "blue": "#365571",
    "blue_hover": "#2D455A",
    "background": "#F5F7FA",
    "muted": "#657587",
    "text": "#192B3A",
    "light_border": "#E3E8EE",
    "header": "#EDF1F5",
    "green": "#15803D",
    "red": "#B91C1C",
    "orange": "#B45309",
    "sidebar_hint": "#B8C5D0",
    "body_heading": "#405568",
    "error": "#DC2626",
    "card_green": "#EAF8F0",
    "card_blue": "#EAF1FF",
    "card_purple": "#F2EDFF",
    "card_orange": "#FFF3E9",
    "status_blue": "#2563EB",
    "status_yellow": "#D97706",
    "white": "#FFFFFF",
    "alt_row": "#F7F9FC",
    "soft_danger": "#FBE8E8",
    "hover_danger": "#F8D0D0",
    "soft_button": "#E8EDF2",
    "hover_button": "#D6DFE7",
    "photo_placeholder": "#B0B9C2",
}

MENU_CATEGORIES = ["Піца", "Закуска", "Напій", "Соус"]


def format_price(price):
    value = Decimal(str(price))
    if value == value.to_integral_value():
        return f"{int(value)} грн"
    return f"{value:.2f}".replace(".", ",") + " грн"


def format_quantity(quantity):
    result = format(Decimal(str(quantity)), "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result.replace(".", ",")
