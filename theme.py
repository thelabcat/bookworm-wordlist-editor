"""Theme variables

Colors and other settings to theme the GUIs with.

Copyright 2025 Wilbur Jaywright d.b.a. Marswide BGL.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

S.D.G"""

import tkinter as tk

# Styling colors
COLORS = {
    "leather": "#945110",
    "dark_leather": "#732c08",
    "entry_wall": "#312018",
    "book_button": "#ef7942",
    "gold": "#f7c708",
    "paper": "#c6a66b",
    "selected_paper": "#f7db73",
    "char": "#434343",
    "dark_char": "#202020",
    "link_blue": "#00f",
    "sapphire": "#2dc3ff",
    }

# Buttons and such
LEATHER_STYLE_MAP = {
    "background": [("!disabled", COLORS["leather"]),
                   ("disabled", COLORS["dark_char"])],
    "foreground": [("active", COLORS["gold"]),
                   ("!disabled", "black"),
                   ("disabled", COLORS["char"])],
    }

# Tiles
PAPER_STYLE_MAP = {
    "fieldbackground": [  # ("focus", COLORS["selected_paper"]),
                        ("!disabled", COLORS["selected_paper"]),
                        ("disabled", COLORS["dark_char"])],
    "foreground": [("selected", "focus", "white"),
                   ("!disabled", "black"),
                   ("disabled", COLORS["char"])],
}

# The overall GUI theme
LIBRARY_THEME = {
    "TFrame": {"map": LEATHER_STYLE_MAP},
    "TScrollbar": {
        "map": {
            **LEATHER_STYLE_MAP,
            "troughcolor": [
                ("!disabled", COLORS["dark_leather"]),
                ("disabled", COLORS["dark_char"]),
                ],
            },
        },
    "TProgressbar": {
        "map": {
            "troughcolor": [
                ("!disabled", COLORS["leather"]),
                ("disabled", COLORS["dark_char"]),
                ],
            }
        },
    "TButton": {
        "map": {
            **LEATHER_STYLE_MAP,
            "relief": [
                ("!pressed", "raised"),
                ("pressed", "sunken"),
                ],
            "anchor": tk.CENTER,
            }
        },
    "TEntry": {"map": PAPER_STYLE_MAP},
    "TLabel": {"map": LEATHER_STYLE_MAP},
    "Score.TLabel": {
        "map": {
            "background": [
                ("!disabled", COLORS["gold"]),
                ("disabled", COLORS["dark_char"]),
                ],
            "foreground": [
                ("!disabled", "black"),
                ("disabled", COLORS["char"]),
                ],
            }
        },
    "WordDisplay.TLabel": {
        "map": {
            "background": [
                ("!disabled", COLORS["entry_wall"]),
                ("disabled", COLORS["dark_char"]),
                ],
            "foreground": [
                ("!disabled", COLORS["selected_paper"]),
                ("disabled", COLORS["char"]),
                ],
            }
        },
    "Link.TLabel": {
        "map": {
            "foreground": [
                ("!disabled", COLORS["link_blue"]),
                ("disabled", COLORS["char"]),
                ],
            }
        }
    }


# Menubar parameters dict
MENU_STYLING_KWARGS = {
    "bg": COLORS["dark_leather"],
    # "fg": COLORS["selected_paper"],
    "activebackground": COLORS["leather"],
    "activeforeground": "white",
    "disabledforeground": COLORS["char"],
    }
