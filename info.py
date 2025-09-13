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
import webbrowser
import tkinter as tk

OP_PATH = op.dirname(__file__)  # The path of the script file's containing folder

PROGRAM_NAME = "BookWorm Deluxe Wordlist Editor"
PROGRAM_VER = "1.10.0"
ICON_PATH = op.join(OP_PATH, "bookworm_wordlist_editor.png")
LICENSE_NAME = "Apache License version 2.0"


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

        self.build()

        # Lock built size as minimum
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        self.mainloop()

    def build(self):
        """Construct the GUI"""
        # Program name and version
        tk.Label(self, text=PROGRAM_NAME + "\nVersion " + PROGRAM_VER).grid(
            row=0, padx=10, pady=10
        )

        # Program icon
        self.icon = tk.PhotoImage(file=ICON_PATH)
        tk.Label(self, image=self.icon).grid(row=1, padx=10, pady=3)
        self.rowconfigure(1, weight=1)

        # License info
        self.license_frame = tk.Frame(self)
        self.license_frame.grid(row=2, sticky=tk.EW, padx=10, pady=5)

        tk.Label(self.license_frame, text="Licensed under ").grid(
            row=0, column=0, sticky=tk.E
        )

        self.license_link = tk.Label(
            self.license_frame,
            text=LICENSE_NAME,
            cursor="hand2",
            foreground="blue",
        )
        self.license_link.grid(row=0, column=1, sticky=tk.W)
        self.license_link.bind("<Button-1>", lambda e: webbrowser.open(URL.license))
        self.license_frame.columnconfigure(0, weight=1)
        self.license_frame.columnconfigure(1, weight=1)

        # Home page link
        self.homepage_link = tk.Label(
            self, text="Project Homepage", cursor="hand2", foreground="blue"
        )
        self.homepage_link.grid(row=3, sticky=tk.EW, padx=10, pady=5)
        self.homepage_link.bind("<Button-1>", lambda e: webbrowser.open(URL.homepage))

        # Credit to Whom it is always due
        tk.Label(self, text="S.D.G.").grid(row=4, padx=10, pady=10)

        # Ok button
        tk.Button(self, text="Ok", command=self.destroy).grid(row=5, padx=10, pady=10)

        self.columnconfigure(0, weight=1)


if __name__ == "__main__":
    print("This module is should only be run on its own for debugging.")
    print("Spawning About dialogue")
    AboutDialogue()
