#!/usr/bin/env python3
"""BookWorm Deluxe Wordlist Editor - Help Information

Various bits of program information, including an About dialogue.

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

S.D.G."""

from os import path as op
import time
import webbrowser
import tkinter as tk
from tkinter import ttk

OP_PATH = op.dirname(__file__)  # The path of the script file's containing folder

PROGRAM_NAME = "BookWorm Deluxe Wordlist Editor"
PROGRAM_VER = "2.4.0"
ICON_PATH = op.join(OP_PATH, "bookworm_wordlist_editor.png")
LICENSE_NAME = "Apache License version 2.0"

INITIAL_COMMIT_DATE_STR = "Wed Mar 27 13:07:57 2024 -0400"
COMMIT_DATE_PARSEFORM = "%a %b %d %H:%M:%S %Y %z"
INITIAL_COMMIT_TIMESTAMP = time.mktime(
    time.strptime(INITIAL_COMMIT_DATE_STR, COMMIT_DATE_PARSEFORM)
    )


class URL:
    """URLs to various places"""

    homepage = "https://github.com/thelabcat/bookworm-wordlist-editor"
    how_to_use = homepage + "?tab=readme-ov-file#usage"
    report_issue = homepage + "/issues"
    license = "https://www.apache.org/licenses/LICENSE-2.0"


class AboutDialogue(tk.Toplevel):
    """Dialogue to show information about the program"""

    def __init__(self, parent: tk.Tk | tk.Toplevel = None):
        """Dialogue to show information about the program

        Args:
            parent (tk.Tk | tk.Toplevel): The parent Tk window this dialogue should spawn from.
                Defaults to None."""

        super().__init__(parent)
        self.grab_set()
        self.title("About")
        self.stylemanager = ttk.Style(self)
        self.build()

        # Lock built size as minimum
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        self.mainloop()

    def build(self):
        """Construct the GUI"""
        # Program name and version
        ttk.Label(self, text=PROGRAM_NAME, anchor=tk.CENTER)\
            .grid(row=0, padx=10, pady=10)
        ttk.Label(self, text="Version " + PROGRAM_VER, anchor=tk.CENTER)\
            .grid(row=1, padx=10, pady=7)

        # Program icon
        self.icon = tk.PhotoImage(file=ICON_PATH)
        ttk.Label(self, image=self.icon).grid(row=2, padx=10, pady=7)
        self.rowconfigure(1, weight=1)

        self.stylemanager.configure("Link.TLabel", foreground="blue")

        # License info
        self.license_frame = ttk.Frame(self)
        self.license_frame.grid(row=3, sticky=tk.EW, padx=10, pady=5)

        ttk.Label(self.license_frame, text="Licensed under", anchor=tk.E).grid(
            row=0, column=0, sticky=tk.NSEW
        )

        self.license_link = ttk.Label(
            self.license_frame,
            text=LICENSE_NAME,
            cursor="hand2",
            style="Link.TLabel",
            anchor=tk.W
        )
        self.license_link.grid(row=0, column=1, sticky=tk.NSEW)
        self.license_link.bind(
            "<Button-1>", lambda e: webbrowser.open(URL.license)
            )
        self.license_frame.columnconfigure(0, weight=1)
        self.license_frame.columnconfigure(1, weight=1)

        # Home page link
        self.homepage_link = ttk.Label(
            self,
            text="Project Homepage",
            cursor="hand2",
            style="Link.TLabel",
            anchor=tk.CENTER,
        )
        self.homepage_link.grid(row=4, sticky=tk.EW, padx=10, pady=5)
        self.homepage_link.bind("<Button-1>", lambda e: webbrowser.open(URL.homepage))

        # Credit to Whom it is always due
        ttk.Label(self, text="S.D.G.").grid(row=5, padx=10, pady=10)

        # Ok button
        ttk.Button(self, text="Ok", command=self.destroy).grid(row=6, padx=10, pady=10)

        self.columnconfigure(0, weight=1)


if __name__ == "__main__":
    print("This module is should only be run on its own for debugging.")
    print("Spawning About dialogue")
    AboutDialogue()
