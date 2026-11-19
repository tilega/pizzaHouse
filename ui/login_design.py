"""Shared Pizza House login styling and subtle press animation."""
import math
import tkinter as tk
import customtkinter as ctk

NAVY = "#102039"
NAVY_LIGHT = "#263C58"
RED = "#D91D31"
RED_HOVER = "#F1263D"
WHITE = "#FFFFFF"

def pizza_background(parent):
    canvas = tk.Canvas(parent, bg=NAVY, highlightthickness=0, bd=0)
    canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
    def draw(event=None):
        canvas.delete("pattern")
        w = max(canvas.winfo_width(), 1)
        h = max(canvas.winfo_height(), 1)
        # Alternating diagonal pizza slices; the grid stays consistent on resize.
        for row, cy in enumerate(range(-55, h+140, 170)):
            for col, cx in enumerate(range(-55, w+160, 195)):
                x = cx + (97 if row % 2 else 0)
                y = cy
                direction = -1 if (row+col)%2 else 1
                a = (x-54*direction, y-42)
                b = (x-54*direction, y+42)
                tip = (x+66*direction, y)
                canvas.create_polygon(*a,*b,*tip,fill="",outline=NAVY_LIGHT,
                                      width=3,tags="pattern",smooth=False)
                canvas.create_line(a[0],a[1],b[0],b[1],fill=NAVY_LIGHT,
                                   width=8,tags="pattern")
                for dx,dy,r in [(-22,-13,9),(-18,20,8),(15,0,10)]:
                    canvas.create_oval(x+dx-r,y+dy-r,x+dx+r,y+dy+r,
                                       outline=NAVY_LIGHT,width=3,tags="pattern")
        canvas.tag_lower("pattern")
    canvas.bind("<Configure>", draw)
    return canvas

class PressButton(ctk.CTkButton):
    """CTk button with hover and a small, reversible physical press effect."""
    def __init__(self, master, **kwargs):
        kwargs.setdefault("corner_radius", 13)
        kwargs.setdefault("hover_color", RED_HOVER)
        super().__init__(master, **kwargs)
        self._normal_height = int(kwargs.get("height", 44))
        self._pressed = False
        self.bind("<ButtonPress-1>", self._down, add="+")
        self.bind("<ButtonRelease-1>", self._up, add="+")
        self.bind("<Leave>", self._up, add="+")
    def _down(self, event=None):
        if self._pressed:
            return
        self._pressed = True
        self.configure(height=max(30,self._normal_height-4))
    def _up(self, event=None):
        if self._pressed:
            self._pressed = False
            self.configure(height=self._normal_height)

def login_card(parent, width=470, height=580):
    card = ctk.CTkFrame(parent,width=width,height=height,fg_color=WHITE,
                        corner_radius=24,border_width=7,border_color=RED)
    card.place(relx=.5,rely=.5,anchor="center")
    card.pack_propagate(False)
    return card

def field(parent, placeholder, secret=False):
    entry=ctk.CTkEntry(parent,width=355,height=46,placeholder_text=placeholder,
                       show="*" if secret else "",corner_radius=11,
                       fg_color="#FFFFFF",border_color="#C7CCD5",border_width=1,
                       text_color=NAVY,font=("Arial",14))
    entry.pack(pady=7)
    return entry
