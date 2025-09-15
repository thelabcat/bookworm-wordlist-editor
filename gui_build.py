#!/usr/bin/env python3
"""BookWorm Wordlist Editor main GUI construction

Provide a build(tk.Tk) function to be run by the main Tk window on itself.

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

import tkinter as tk
import webbrowser
import info

# The definition field size
DEFFIELD_SIZE = (15, 5)


def __build_menubar(self: tk.Tk):
    """Construct the GUI's menubar

    Args:
        self (tk.Tk): The root window to build on."""

    # Base menubar
    self.menubar = tk.Menu(self)
    self["menu"] = self.menubar

    # File menu
    self.file_menu = tk.Menu(self.menubar, tearoff=1)
    self.menu_labels["file"] = "🗃️ File"

    # Open
    self.bind("<Control-o>", lambda _: self.load_files(select=True))
    self.file_menu.add_command(
        label="📂 Open",
        underline=3,
        command=lambda: self.load_files(select=True),
    )

    # Reload
    self.bind("<Control-r>", lambda _: self.load_files(select=False))
    self.file_menu.add_command(
        label="🔃 Reload",
        underline=3,
        command=lambda: self.load_files(select=False),
    )

    # Save
    self.bind("<Control-s>", lambda _: self.save_files)
    self.file_menu.add_command(
        label="💾 Save",
        underline=3,
        command=self.save_files
        )

    self.file_menu.add_separator()

    # Backup existing
    self.bind("<Control-b>", self.make_backup)
    self.file_menu.add_command(
        label="🕞 Backup existing",
        underline=3,
        command=self.make_backup
        )

    self.menubar.add_cascade(
        label=self.menu_labels["file"],
        menu=self.file_menu
        )

    # Edit menu
    self.edit_menu = tk.Menu(self.menubar, tearoff=1)
    self.menu_labels["edit"] = "🖊️ Edit"

    self.edit_menu.add_command(
        label="➕ Add several words", command=self.mass_add_words
    )
    self.edit_menu.add_command(
        label="📚 Auto-define undefined rare words",
        command=self.mass_auto_define
    )

    self.edit_menu.add_separator()
    self.edit_menu.add_command(
        label="🗑️ Delete several words", command=self.mass_delete_words
    )
    self.edit_menu.add_command(
        label="📏 Delete words of invalid length",
        command=self.del_invalid_len_words
    )
    self.edit_menu.add_command(
        label="⛓️‍💥 Delete orphaned definitions",
        command=self.del_orphaned_defs
    )
    self.edit_menu.add_command(
        label="👬 Delete duplicate word listings",
        command=self.del_dupe_words
    )
    self.menubar.add_cascade(
        label=self.menu_labels["edit"], menu=self.edit_menu
        )

    # Help menu
    self.help_menu = tk.Menu(self.menubar, tearoff=1)
    self.menu_labels["help"] = "❔ Help"

    self.help_menu.add_command(
        label="🪧 About", command=lambda: info.AboutDialogue(self)
    )

    self.help_menu.add_separator()
    self.help_menu.add_command(
        label="📖 How to use",
        foreground="blue",
        command=lambda: webbrowser.open(info.URL.how_to_use),
    )
    self.help_menu.add_command(
        label="⁉️ Report an issue",
        foreground="blue",
        command=lambda: webbrowser.open(info.URL.report_issue),
    )
    self.menubar.add_cascade(
        label=self.menu_labels["help"], menu=self.help_menu
        )


def __build_list_pane(self: tk.Tk, list_frame: tk.Frame):
    """Construct the word list pane

    Args:
        self (tk.Tk): The root window.
        list_frame (tk.Frame): The frame to build on."""

    # Subframe for search system
    self.search_frame = tk.Frame(list_frame)
    self.search_frame.grid(row=0, columnspan=2, sticky=tk.NSEW)

    # Search system
    self.search_label = tk.Label(
        self.search_frame, text="Search 🔎:", anchor=tk.W
        )
    self.search_label.grid(row=0, column=0, sticky=tk.NSEW)
    self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_str)
    self.search_entry.grid(row=0, column=1, sticky=tk.NSEW)
    self.search_frame.columnconfigure(1, weight=1)

    self.search_clear_bttn = tk.Button(
        self.search_frame, text="🧹", command=lambda: self.search_str.set("")
    )
    self.search_clear_bttn.grid(row=0, column=2, sticky=tk.NSEW)
    self.widgets_to_disable += [
        self.search_label,
        self.search_entry,
        self.search_clear_bttn,
    ]

    # Word list display
    self.query_box = tk.Listbox(
        list_frame,
        listvariable=self.query_list,
        height=10,
        selectmode=tk.SINGLE,
        exportselection=False,
    )
    self.query_box.bind(
        "<<ListboxSelect>>",
        lambda _: self.selection_updated(),
        )
    self.query_box.grid(row=1, column=0, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.query_box)

    self.query_box_scrollbar = tk.Scrollbar(
        list_frame, orient=tk.VERTICAL, command=self.query_box.yview
    )
    self.query_box["yscrollcommand"] = self.query_box_scrollbar.set
    self.query_box_scrollbar.grid(row=1, column=1, sticky=tk.N + tk.S + tk.E)
    # Scrollbar cannot be state disabled
    # self.widgets_to_disable.append(self.query_box_scrollbar)
    list_frame.rowconfigure(1, weight=1)

    # Button to add a word
    self.add_word_bttn = tk.Button(
        list_frame, text="➕ Add word", command=self.add_word
    )
    self.add_word_bttn.grid(row=2, columnspan=2, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.add_word_bttn)
    list_frame.columnconfigure(0, weight=1)


def __build_word_edit_pane(self: tk.Tk, word_edit_frame: tk.Frame):
    """Construct the selected word editing pane

    Args:
        self (tk.Tk): The root window.
        word_edit_frame (tk.Frame): The frame to build on."""

    # Subframe for word and usage display
    self.word_disp_frame = tk.Frame(word_edit_frame)
    self.word_disp_frame.grid(row=0, columnspan=2, sticky=tk.NSEW)
    word_edit_frame.columnconfigure(0, weight=1)
    word_edit_frame.columnconfigure(1, weight=1)

    # Display the currently selected word
    self.word_disp_label = tk.Label(self.word_disp_frame, textvariable=self.word_disp_str)
    self.word_disp_label.grid(row=0, column=0, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.word_disp_label)
    self.word_disp_frame.columnconfigure(0, weight=1)

    # Display how often that word is used
    self.usage_disp_label = tk.Label(
        self.word_disp_frame,
        textvariable=self.usage_disp_str,
        anchor=tk.E
        )
    self.usage_disp_label.grid(row=0, column=1, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.usage_disp_label)

    # Allow editing of the popdef for the word
    self.def_field = tk.Text(
        word_edit_frame,
        width=DEFFIELD_SIZE[0],
        height=DEFFIELD_SIZE[1],
        wrap=tk.WORD,
    )
    self.def_field.grid(row=1, columnspan=2, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.def_field)
    word_edit_frame.rowconfigure(1, weight=1)
    word_edit_frame.columnconfigure(0, weight=1)
    word_edit_frame.columnconfigure(1, weight=1)

    self.reset_def_bttn = tk.Button(
        word_edit_frame,
        text="🔃 Reset definition",
        command=self.selection_updated,
    )
    self.reset_def_bttn.grid(row=2, column=0, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.reset_def_bttn)

    self.save_def_bttn = tk.Button(
        word_edit_frame, text="💾 Save definition", command=self.update_definition
    )
    self.save_def_bttn.grid(row=2, column=1, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.save_def_bttn)

    self.autodef_bttn = tk.Button(
        word_edit_frame, text="📚 Auto-define", command=self.auto_define
    )
    self.autodef_bttn.grid(row=3, columnspan=2, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.autodef_bttn)

    self.del_bttn = tk.Button(
        word_edit_frame,
        text="🗑️ Delete word",
        command=self.delete_selected_word,
    )
    self.del_bttn.grid(row=4, columnspan=2, sticky=tk.NSEW)
    self.widgets_to_disable.append(self.del_bttn)


def build(self: tk.Tk):
    """Construct the GUI

    Args:
        self (tk.Tk): The root window to build on."""

    __build_menubar(self)

    # Left-hand pane, for list
    self.list_frame = tk.Frame(self)
    self.list_frame.grid(row=0, column=0, sticky=tk.NSEW)
    self.columnconfigure(0, weight=1)
    __build_list_pane(self, self.list_frame)

    # Right-hand pane, for single word edit functions
    self.word_edit_frame = tk.Frame(self)
    self.word_edit_frame.grid(row=0, column=1, sticky=tk.NSEW)
    self.word_edit_frame.bind_all("<Key>", lambda _: self.regulate_def_buttons)
    self.columnconfigure(1, weight=1)
    __build_word_edit_pane(self, self.word_edit_frame)

    # Expand those two panes vertically
    self.rowconfigure(0, weight=1)

    # Status display footer
    self.status_displaytext = tk.StringVar(self)
    self.status_label = tk.Label(
        self,
        textvariable=self.status_displaytext,
        anchor=tk.W,
        relief="sunken"
    )
    self.status_label.grid(row=1, column=0, columnspan=2, sticky=tk.EW)
