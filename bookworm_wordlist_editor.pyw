#!/usr/bin/env python3
"""BookWorm Deluxe Wordlist Editor

An application for editing the word list and popdefs in BookWorm Deluxe.

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

import os
from os import path as op
import shutil
import sys
import threading
import tkinter as tk
from tkinter import messagebox as mb
from tkinter import simpledialog as dialog
from tkinter import filedialog
import time
import webbrowser
import bookworm_utils as bw
import info

# File paths and related info
OP_PATH = op.dirname(__file__)  # The path of the script file's containing folder

BACKUP_FILEEXT = ".bak"  # Suffix for backup files

# Tkinter file dialog types filter for plain text files
TEXT_FILETYPE = [("Plain text", ".txt")]

# Allow system environment variable to override normal default for game path
ENV_GAME_PATH = os.environ.get("BOOKWORM_GAME_PATH")
if ENV_GAME_PATH:
    # The environment variable points to a nonexistent path
    if not op.exists(ENV_GAME_PATH):
        print("System tried to set game path default to", ENV_GAME_PATH, "but it does not exist.")
        GAME_PATH_DEFAULT = bw.GAME_PATH_DEFAULT

    # The environment variable points to a real path that is not a valid game path
    elif not bw.is_game_path_valid(ENV_GAME_PATH):
        # The default game path is valid
        if bw.is_game_path_valid(bw.GAME_PATH_DEFAULT):
            print("System tried to set game path default to", ENV_GAME_PATH, "but it is not valid while", bw.GAME_PATH_DEFAULT, "is.")
            GAME_PATH_DEFAULT = bw.GAME_PATH_DEFAULT

        # The default game path isn't any better than the one provided
        else:
            print("System set game path default to", ENV_GAME_PATH, "which is not a valid game path, but it's the best we know.")
            GAME_PATH_DEFAULT = ENV_GAME_PATH

    # The environment variable was set validly
    else:
        print("System set game path default to", ENV_GAME_PATH)
        GAME_PATH_DEFAULT = ENV_GAME_PATH

# The environment variable was not set
else:
    GAME_PATH_DEFAULT = bw.GAME_PATH_DEFAULT

# Miscellanious GUI settings
WINDOW_TITLE = info.PROGRAM_NAME
UNSAVED_WINDOW_TITLE = (
    "*" + WINDOW_TITLE
)  # Title of window when there are unsaved changes
RARE_COLS = ("#000", "#c00")  # Index with int(<is rare?>)
WORDFREQ_DISP_PREFIX = "Usage: "
NO_WORD = "(no word selected)"
DEFFIELD_SIZE = (15, 5)


class Editor(tk.Tk):
    """Main editor window"""

    def __init__(self):
        """Main editor window"""

        super().__init__()

        # The word list and definitions dictionary
        self.words = []
        self.defs = {}

        self.thread = None  # Any thread the GUI might spawn

        self.__busy = False  # Is the GUI currently busy (all widgets disabled)?

        self.__busy_text = ""  # Current operations message

        # Handle unsaved changes
        self.__unsaved_changes = False
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Make the GUI
        self.title(WINDOW_TITLE)
        self.iconphoto(True, tk.PhotoImage(file=info.ICON_PATH))
        self.build()

        # Lock built size as minimum
        self.update()
        self.minsize(self.winfo_width(), self.winfo_height())

        # Load files
        self.game_path = GAME_PATH_DEFAULT
        self.load_files(select=False, do_or_die=True)

        # Start the GUI loop
        self.mainloop()

    @property
    def unsaved_changes(self) -> bool:
        """If we currently have unsaved changes"""

        return self.__unsaved_changes

    @unsaved_changes.setter
    def unsaved_changes(self, new_value: bool):
        """If we have unsaved changes

        Args:
            new_value (bool): Setting if changes are currently unsaved"""

        assert isinstance(new_value, bool), "Value for unsaved changes must be bool"
        self.__unsaved_changes = new_value

        # Set the window title based on wether changes are saved or not
        self.title((WINDOW_TITLE, UNSAVED_WINDOW_TITLE)[int(new_value)])

        # Make sure the status footer is up-to-date with any new changes
        self.update_idle_status()

    def on_closing(self):
        """What to do if the user clicks to close this window"""

        if self.unsaved_changes:
            answer = mb.askyesnocancel(
                "Unsaved changes",
                "There are currently unsaved changes to the word list " +
                "and / or popdefs. Save before exiting?",
            )

            # The user cancelled the exit
            if answer is None:
                return

            # The user clicked yes
            if answer:
                self.save_files()

        # Close the window
        self.destroy()

    def build(self):
        """Construct GUI"""

        # Menubar
        self.menubar = tk.Menu(self)
        self["menu"] = self.menubar

        # File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=1)

        # Open
        self.bind("<Control-o>", lambda _: self.load_files(select=True))
        self.file_menu.add_command(
            label="📂 Open", underline=3, command=lambda: self.load_files(select=True)
        )

        # Reload
        self.bind("<Control-r>", lambda _: self.load_files(select=False))
        self.file_menu.add_command(
            label="🔃 Reload", underline=3, command=lambda: self.load_files(select=False)
        )

        # Save
        self.bind("<Control-s>", self.save_files)
        self.file_menu.add_command(label="💾 Save", underline=3, command=self.save_files)

        self.file_menu.add_separator()

        # Backup existing
        self.bind("<Control-b>", self.make_backup)
        self.file_menu.add_command(label="🕞 Backup existing", underline=3, command=self.make_backup)

        self.menubar.add_cascade(label="🗃️ File", menu=self.file_menu)

        # Edit menu
        self.edit_menu = tk.Menu(self.menubar, tearoff=1)
        self.edit_menu.add_command(
            label="➕ Add several words", command=self.mass_add_words
        )
        self.edit_menu.add_command(
            label="📚 Auto-define undefined rare words", command=self.mass_auto_define
        )

        self.edit_menu.add_separator()
        self.edit_menu.add_command(
            label="🗑️ Delete several words", command=self.mass_delete_words
        )
        self.edit_menu.add_command(
            label="📏 Delete words of invalid length", command=self.del_invalid_len_words
        )
        self.edit_menu.add_command(
            label="⛓️‍💥 Delete orphaned definitions", command=self.del_orphaned_defs
        )
        self.edit_menu.add_command(
            label="👬 Delete duplicate word listings", command=self.del_dupe_words
        )
        self.menubar.add_cascade(label="🖊️ Edit", menu=self.edit_menu)

        # Help menu
        self.help_menu = tk.Menu(self.menubar, tearoff=1)

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
        self.menubar.add_cascade(label="❔ Help", menu=self.help_menu)

        self.menubar_entries = ("🗃️ File", "🖊️ Edit", "❔ Help")  # Menus to disable when busy

        self.widgets_to_disable = []  # Widgets to disable when busy

        # Frame for list
        self.list_frame = tk.Frame(self)
        self.list_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Subframe for search system
        self.search_frame = tk.Frame(self.list_frame)
        self.search_frame.grid(row=0, columnspan=2, sticky=tk.NSEW)

        # Search system
        self.search_label = tk.Label(self.search_frame, text="Search 🔎:", anchor=tk.W)
        self.search_label.grid(row=0, column=0, sticky=tk.NSEW)

        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *args: self.update_query())
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search)
        self.search_entry.grid(row=0, column=1, sticky=tk.NSEW)
        self.search_frame.columnconfigure(1, weight=1)

        self.search_clear_bttn = tk.Button(
            self.search_frame, text="🧹", command=lambda: self.search.set("")
        )
        self.search_clear_bttn.grid(row=0, column=2, sticky=tk.NSEW)
        self.widgets_to_disable += [
            self.search_label,
            self.search_entry,
            self.search_clear_bttn,
        ]

        # Word list display
        self.query_list = tk.Variable(value=["foo", "bar", "bazz"])
        self.query_box = tk.Listbox(
            self.list_frame,
            listvariable=self.query_list,
            height=10,
            selectmode=tk.SINGLE,
            exportselection=False,
        )
        self.query_box.bind("<<ListboxSelect>>", self.selection_updated)
        self.query_box.grid(row=1, column=0, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.query_box)

        self.query_box_scrollbar = tk.Scrollbar(
            self.list_frame, orient=tk.VERTICAL, command=self.query_box.yview
        )
        self.query_box["yscrollcommand"] = self.query_box_scrollbar.set
        self.query_box_scrollbar.grid(row=1, column=1, sticky=tk.N + tk.S + tk.E)
        # self.widgets_to_disable.append(self.query_box_scrollbar)  # Scrollbar cannot be state disabled
        self.list_frame.rowconfigure(1, weight=1)

        # Button to add a word
        self.add_word_bttn = tk.Button(
            self.list_frame, text="➕ Add word", command=self.add_word
        )
        self.add_word_bttn.grid(row=2, columnspan=2, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.add_word_bttn)
        self.list_frame.columnconfigure(0, weight=1)

        # Right-hand pane, for single word edit functions
        self.worddef_frame = tk.Frame(self)
        self.worddef_frame.grid(row=0, column=1, sticky=tk.NSEW)
        self.worddef_frame.bind_all("<Key>", self.regulate_def_buttons)
        self.columnconfigure(1, weight=1)

        # Subframe for word and usage display
        self.worddisp_frame = tk.Frame(self.worddef_frame)
        self.worddisp_frame.grid(row=0, columnspan=2, sticky=tk.NSEW)
        self.worddef_frame.columnconfigure(0, weight=1)
        self.worddef_frame.columnconfigure(1, weight=1)

        # Display the currently selected word
        self.word_display = tk.Label(self.worddisp_frame, text=NO_WORD)
        self.word_display.grid(row=0, column=0, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.word_display)
        self.worddisp_frame.columnconfigure(0, weight=1)

        # Display how often that word is used
        self.usage_display = tk.Label(self.worddisp_frame, text="", anchor=tk.E)
        self.usage_display.grid(row=0, column=1, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.usage_display)

        # Allow editing of the popdef for the word
        self.def_field = tk.Text(
            self.worddef_frame,
            width=DEFFIELD_SIZE[0],
            height=DEFFIELD_SIZE[1],
            wrap=tk.WORD,
        )
        self.def_field.grid(row=1, columnspan=2, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.def_field)
        self.worddef_frame.rowconfigure(1, weight=1)
        self.worddef_frame.columnconfigure(0, weight=1)
        self.worddef_frame.columnconfigure(1, weight=1)

        self.reset_def_bttn = tk.Button(
            self.worddef_frame, text="🔃 Reset definition", command=self.selection_updated
        )
        self.reset_def_bttn.grid(row=2, column=0, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.reset_def_bttn)

        self.save_def_bttn = tk.Button(
            self.worddef_frame, text="💾 Save definition", command=self.update_definition
        )
        self.save_def_bttn.grid(row=2, column=1, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.save_def_bttn)

        self.autodef_bttn = tk.Button(
            self.worddef_frame, text="📚 Auto-define", command=self.auto_define
        )
        self.autodef_bttn.grid(row=3, columnspan=2, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.autodef_bttn)

        self.del_bttn = tk.Button(
            self.worddef_frame, text="🗑️ Delete word", command=self.delete_selected_word
        )
        self.del_bttn.grid(row=4, columnspan=2, sticky=tk.NSEW)
        self.widgets_to_disable.append(self.del_bttn)

        # Status display footer
        self.status_displaytext = tk.StringVar(self)
        self.status_label = tk.Label(
            self, textvariable=self.status_displaytext, anchor=tk.W, relief="sunken"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, sticky=tk.EW)

    def thread_process(self, method: callable, message: str = "Working..."):
        """Run a method in a thread, and grey out the GUI until it's finished.

        Args:
            method (callable): The method to run in a thread.
            message (str): The message to show over the greyed out GUI."""

        self.thread = threading.Thread(
            target=lambda: self.__busy_run(method, message), daemon=True
        )
        self.thread.start()

    def __busy_run(self, method: callable, message: str = "Working.."):
        """Run a method, and grey out the GUI until it's finished.

        Args:
            method (callable): The method to run.
            message (str): The message to show over the greyed out GUI."""

        self.busy_text = message
        self.busy = True
        method()
        self.busy = False

        # The currently selected word may have had changes made
        self.selection_updated()

    @property
    def idle_status(self) -> str:
        """The status text to display when no operations are running"""
        return f"Ready. {len(self.words):,} words. {len(self.defs):,} popdefs.{" (unsaved)" if self.unsaved_changes else ""}"

    @property
    def busy(self) -> bool:
        """Wether or not the program is busy"""
        return self.__busy

    @busy.setter
    def busy(self, new: bool):
        """Wether or not the program is busy"""
        # For other widget disablers to reference
        self.__busy = new

        if new:
            self.status_displaytext.set(self.busy_text)

        # Has its own check for current busy state, safe to run regardless
        self.update_idle_status()

        # Enable or disable all the widgets
        new_state = (tk.NORMAL, tk.DISABLED)[int(new)]
        for entry in self.menubar_entries:
            self.menubar.entryconfig(entry, state=new_state)
        for widget in self.widgets_to_disable:
            widget.config(state=new_state)

        # Rerun any unique widget disablers
        self.unique_disable_handlers()

    @property
    def busy_text(self):
        """Current operations message"""
        return self.__busy_text

    @busy_text.setter
    def busy_text(self, new: str):
        """Current operations message"""
        self.__busy_text = new
        # If we are currently busy, display the new message
        if self.busy:
            self.status_displaytext.set(new)

    def update_idle_status(self):
        """If we are currently idle, refresh the idle status message"""
        if not self.busy:
            self.status_displaytext.set(self.idle_status)

    def unique_disable_handlers(self):
        """Run all unique widget disabling handlers"""

        self.regulate_word_buttons()
        self.regulate_def_buttons()

    def regulate_word_buttons(self):
        """Enable or disable the word handling buttons based on if a word is
            selected"""

        # Do not enable or disable these widgets if the GUI is busy
        if self.busy:
            return

        # buttons should be disabled if no word is selected
        new_state = (tk.NORMAL, tk.DISABLED)[int(self.selected_word == NO_WORD)]

        for button in (self.autodef_bttn, self.del_bttn):
            button.config(state=new_state)

    def regulate_def_buttons(self, event=None):
        """Check if the definition has changed, and regulate the reset / save
            def buttons accordingly.

        Args:
            event (object): Unused, receives Tkinter callback event data.
                Defaults to None."""

        # Do not enable or disable these widgets if the GUI is busy
        if self.busy:
            return

        # Get the current entry
        def_entry = self.def_field.get("0.0", tk.END).strip()

        # There is no selected word
        if self.selected_word == NO_WORD:
            new_state = tk.DISABLED

        # We have an old definition for this word
        elif self.selected_word in self.defs:
            # The user deleted the old definition
            if not def_entry:
                new_state = tk.NORMAL

            # The old definition is the same as the new one
            elif self.defs[self.selected_word] == def_entry:
                new_state = tk.DISABLED

            # There is a new definition
            else:
                new_state = tk.NORMAL

        # We do not have an old definition, and there is a new one
        elif def_entry:
            new_state = tk.NORMAL

        # There was no old or new definition
        else:
            new_state = tk.DISABLED

        # Enable or disable the buttons appropriately
        for button in (self.reset_def_bttn, self.save_def_bttn):
            button.config(state=new_state)

    @property
    def wordlist_abs_path(self):
        """The absolute path of the wordlist file"""
        return op.join(self.game_path, bw.WORDLIST_FILE)

    @property
    def popdefs_abs_path(self):
        """The absolute path of the popdefs file"""
        return op.join(self.game_path, bw.POPDEFS_FILE)

    def load_files(self, select: bool = True, do_or_die: bool = False):
        """Load the wordlist and the popdefs (threaded)

        Args:
            select (bool): Wether or not we need to prompt the user to select a new path.
                Defaults to True.
            do_or_die(bool): Wether or not cancelling is not an option.
                Defaults to False, cancelling is an option."""

        self.thread_process(
            lambda: self._load_files(select, do_or_die), message="Loading..."
        )

    def _load_files(self, select: bool = True, do_or_die: bool = False):
        """Load the wordlist and the popdefs

        Args:
            select (bool): Wether or not we need to prompt the user to select a
                new path.
                Defaults to True.
            do_or_die (bool): Wether or not cancelling is not an option.
                Defaults to False, cancelling is an option."""

        # Ask the user for a directory if the current one is invalid, even if
        # the select argument is false.
        select = select or not bw.is_game_path_valid(self.game_path)

        # While we need to select something
        while select:
            while True:  # Keep asking for an input
                response = filedialog.askdirectory(
                    title="Game directory", initialdir=bw.deepest_valid_path(self.game_path)
                )

                # We got a response, so break the loop.
                if response:
                    break

                # The user cancelled, but we aren't supposed to force. Abort.
                if not do_or_die:
                    return

                # The only remaining possibility is that the user cancelled,
                # but we are do or die. They must choose a directory, or quit.
                if mb.askyesno(
                    "Cannot cancel",
                    "The program needs a valid directory to continue. Exit the program?",
                ):
                    self.destroy()
                    sys.exit()

            # If the game path is valid, we are no longer selecting
            select = not bw.is_game_path_valid(response)
            if select:
                mb.showerror(
                    "Invalid directory",
                    "Could not find the word list and pop definitions here.",
                )
            else:
                self.game_path = response  # We got a new valid directory

        # First, load the wordlist
        self.busy_text = f"Loading {bw.WORDLIST_FILE}..."
        with open(
            self.wordlist_abs_path, encoding=bw.WORDLIST_ENC
        ) as f:
            self.words = sorted(bw.unpack_wordlist(f.read().strip()))

        # Then, load the popdefs
        self.busy_text = f"Loading {bw.POPDEFS_FILE}..."
        with open(
            self.popdefs_abs_path, encoding=bw.POPDEFS_ENC
        ) as f:
            self.defs = dict(
                sorted(
                    bw.unpack_popdefs(f.read().strip()).items()
                    )
                )

        # Update the query list
        self.busy_text = "Updating display..."
        self.update_query()

        # The files were just (re)loaded, so there are no unsaved changes
        self.unsaved_changes = False

    def save_files(self, event=None, backup: bool = False):
        """Save the worldist and popdefs (threaded).

        Args:
            event (object): Unused, receives Tkinter callback event data.
                Defaults to None.
            backup (bool): Wether or not to copy the original files to a backup name.
                Defaults to False."""

        self.thread_process(lambda: self._save_files(backup))

    def _save_files(self, backup: bool = False):
        """Save the worldist and popdefs.

        Args:
            backup (bool): Wether or not to copy the original files to a backup name.
                Defaults to False."""

        # Backup system
        # Recommend a backup if the files are older than this program
        self.busy_text = "Checking need for backup..."
        backup = backup or (
            # Make sure we have files to back up before timestamp reading
            bw.is_game_path_valid(self.game_path) and

            # Files are older than this program
            min((
                op.getmtime(self.wordlist_abs_path),
                op.getmtime(self.popdefs_abs_path),
                )) < info.INITIAL_COMMIT_TIMESTAMP and

            # User confirmed a backup based on this
            mb.askyesno(
                "Backup recommended",
                "The existing game files are older than this program. Save a backup?"
                ))

        if backup:
            self.busy_text = "Creating backup..."
            self.make_backup()

        # First, save the wordlist
        self.busy_text = f"Saving {bw.WORDLIST_FILE}..."
        with open(
            self.wordlist_abs_path, "w", encoding=bw.WORDLIST_ENC
        ) as f:
            f.write(bw.pack_wordlist(sorted(self.words)))

        # Then, save the popdefs
        self.busy_text = f"Saving {bw.POPDEFS_FILE}..."
        with open(
            self.popdefs_abs_path, "w", encoding=bw.POPDEFS_ENC
        ) as f:
            f.write(bw.pack_popdefs(dict(sorted(self.defs.items()))))

        self.unsaved_changes = False  # All changes are now saved

    def make_backup(self):
        """Save a backup of the files, with a timestamp.

        Returns:
            success (bool): Wether or not we were able to backup."""

        # Catch for the files having been deleted while editing them
        if not bw.is_game_path_valid(self.game_path):
            mb.showerror(
                "Backup failed",
                "Could not back up the original files because they have disappeared.",
            )
            return False

        backup_suffix = f"_{int(time.time())}{BACKUP_FILEEXT}"
        shutil.copy(
            self.wordlist_abs_path,
            self.wordlist_abs_path + backup_suffix,
        )
        shutil.copy(
            self.popdefs_abs_path,
            self.popdefs_abs_path + backup_suffix,
        )

        # Notify the user that the backup was successful
        mb.showinfo("Backup completed", f"Copied files to current game path with suffix '{backup_suffix}'")
        return True

    def selection_updated(self, event=None):
        """A new word has been selected (or the equivalent of such), update
            everything.

        Args:
            event (object): Unused, receives Tkinter callback event data.
                Defaults to None."""

        # Load and display the current definition
        self.load_definition()

        # If no word is selected, clear the usage display
        # and just show NO_WORD in the main display
        if self.selected_word == NO_WORD:
            self.usage_display.config(text="")
            word_disp = self.selected_word

        # Otherwise, load and display usage statistics
        # and add quotes around the main display
        else:
            usage = bw.get_word_usage(self.selected_word)
            self.usage_display.config(
                text=WORDFREQ_DISP_PREFIX + str(usage),

                # Make the usage display colored based on a rarity threshold
                fg=RARE_COLS[int(usage < bw.RARE_THRESH)],
            )
            word_disp = f'"{self.selected_word}"'

        # Set the main display to the result regardless
        self.word_display.config(text=word_disp)

        # Enable or disable the word handling buttons based on the selection
        self.regulate_word_buttons()

    def update_query(self):
        """Update the list of search results"""

        # Do not allow any capitalization or non-letters in the search field
        self.search.set(
            "".join([char for char in self.search.get().lower() if char.isalpha()])
        )

        search = self.search.get()

        # Comprehensively filter the wordlist to only matching words
        if search:
            query = [word for word in self.words if search in word]

            # Sort search results primarily by how close the search query is to the beginning
            query.sort(key=lambda x: x.index(search))

        # The search was cleared
        else:
            query = self.words

        # Update the query list
        self.query_list.set(query)

        # There was a search entered, and it returned values, highlight the top result
        if search and query:
            self.selected_word = query[0]

        # The search was cleared or returned no search results
        else:
            self.selected_word = NO_WORD

    @property
    def selected_word(self):
        """The currently selected word.

        Returns:
            word (str): Either the curently selected word or NO_WORD."""

        if self.query_box.curselection():  # Something is selected
            # Return the word at the starting index of the selection
            # (only one word can be selected so the end doesn't matter)
            return self.query_box.get(self.query_box.curselection()[0])
        return NO_WORD

    @selected_word.setter
    def selected_word(self, word: str):
        """The currently selected word.
            If set to something not in the query, clears the query.
            If set to a word we don't have, quietly reverts to NO_WORD.

        Args:
            word (str): The word to try and select."""

        # For our logic purposes, NO_WORD should be treated as null.
        if word == NO_WORD:
            word = ""

        # Current search does not contain word
        if self.search.get() not in word:
            self.search.set("")  # WARNING: Causes one layer of recursion.

        # The word is in our current query, so select and view it
        if word and bw.binary_search(self.words, word) is not None:
            word_query_index = self.query_list.get().index(word)
            self.query_box.selection_clear(0, tk.END)
            self.query_box.selection_set(word_query_index)
            self.query_box.see(word_query_index)

        # Something not in the query list was given, or NO_WORD was given.
        # Clear the selection.
        else:
            self.query_box.selection_clear(0, tk.END)

        self.selection_updated()

    def load_definition(self):
        """Load the definition of the selected word if there is one"""

        # Clear any old displayed definition, regardless
        self.def_field.delete(0.0, tk.END)

        # If we have a definition for this word, display it
        if self.selected_word != NO_WORD and self.selected_word in self.defs:
            self.def_field.insert(0.0, self.defs[self.selected_word])

        # The definition has no unsaved changes.
        # Disable definition reset and save buttons.
        self.regulate_def_buttons()

    def update_definition(self):
        """Update the stored definition for a word"""

        # Filter definition to only spaces, and remove surrounding whitespace.
        def_entry = bw.WHITESPACE_PATTERN.sub(
            " ",
            self.def_field.get("0.0", tk.END).strip(),
            )

        # We have a definition to save
        if def_entry:
            self.defs[self.selected_word] = def_entry

        # We had a definition, and it has been deleted
        elif self.defs.get(self.selected_word) is not None:
            del self.defs[self.selected_word]

        # There are now unsaved changes
        self.unsaved_changes = True

        # In case the invalid character filtering changed what was entered
        self.load_definition()

        # The definition has no unsaved changes.
        # Disable definition reset and save buttons.
        self.regulate_def_buttons()

    def is_len_valid(self, word: str, notify: bool = False) -> bool:
        """Check if a word's length is valid.

        Args:
            word (str): The word to check.
            notify (bool): Wether or not to graphically notify the user of invalid length.
                Defaults to False.

        Returns:
            result (bool): Is the word of valud length?"""

        valid = bw.WORD_LENGTH_MIN <= len(word) <= bw.WORD_LENGTH_MAX

        if not valid and notify:
            # Dialog auto-selects the word "short" or "long" based on wether
            # the invalid length was a too long case or not.
            mb.showerror(
                "Word is too " +
                ("short", "long")[int(len(word) > bw.WORD_LENGTH_MAX)],

                f"Word must be between {bw.WORD_LENGTH_MIN:,} and {bw.WORD_LENGTH_MAX:,} letters long.",
            )

        return valid

    def add_word(self):
        """Create a new word entry"""

        new = dialog.askstring("New word", "Enter the word to add:")

        # Allow the user to cancel, and also enforce length delimiters.
        if not new or not self.is_len_valid(new, notify=True):
            return

        new = new.lower()

        # Ensure that the word is only letters
        if not new.isalpha():
            mb.showerror(
                "Invalid characters found",
                "Word must be only letters (no numbers or symbols).",
            )
            return

        # If the word really is new, add it.
        if not bw.binary_search(self.words, new):
            # Add the new word
            self.words.append(new)
            self.words.sort()

            # Update the query
            self.update_query()

            # There are now unsaved changes
            self.unsaved_changes = True

        # If it is not new, notify the user.
        else:
            mb.showinfo(
                "Already have word",
                f"The word '{new}' is already in the word list.",
            )

        # Highlight and scroll to the new word even if it wasn't actually new
        self.selected_word = new

    def __load_alpha_file(self):
        """Select a text file containing a human-readable list of words,
            read it, close it, and filter the result to alpha-only words.

        Returns:
            words (list): The list of alpha-only words from the file.
                Returns empty list if cancelled."""

        # Have the user select the file
        f = filedialog.askopenfile(
            title="Select human-readable list of words",
            filetypes=TEXT_FILETYPE,
        )

        # The user cancelled via the open file dialog
        if not f:
            return []

        # Read and close the file, splitting into words by whitespace
        listed_words = f.read().strip().lower().split()
        f.close()

        # There were no words
        if not listed_words:
            mb.showerror(
                "Invalid file",
                "Did not find any words in file.",
                )
            return []

        # Filter out duplicates
        self.busy_text = "Filtering out duplicates in file..."
        nodupe_words = set(listed_words)
        dupe_count = len(listed_words) - len(nodupe_words)
        if dupe_count:
            mb.showwarning(
                "Some duplicates in file",
                f"The file had {dupe_count:,} duplicate listings in itself.",
                )

        # filter file to only alpha words
        self.busy_text = "Filtering to alpha-only words..."
        alpha_words = [
            word for word in nodupe_words if word.isalpha()
        ]
        nonalpha_count = len(nodupe_words) - len(alpha_words)

        # There was no text besides non-alpha symbols
        if not alpha_words:
            mb.showerror(
                "Invalid file",
                "File did not contain any alpha-only words.",
                )
            return []

        # There were some non-alpha words
        if nonalpha_count:
            mb.showwarning(
                "Some invalid words",
                f"{nonalpha_count:,} words were rejected because they " +
                "contained non-alpha characters.",
            )

        return alpha_words

    def __mass_unsaved_changes(self, title: str, changes: str):
        """Call when mass changes have been made to the files.
            Offers to save them to disk.

        Args:
            title (str): The title of the dialog.
            changes (str): A human-readable description of the changes made."""

        self.unsaved_changes = True

        # Offer to save changes
        if mb.askyesno(
            title,
            changes + "\nSave changes to disk now?",
        ):
            self.save_files()

    def mass_add_words(self):
        """Add a whole file's worth of words (threaded)"""

        self.thread_process(self._mass_add_words)

    def _mass_add_words(self):
        """Add a whole file's worth of words"""

        alpha_words = self.__load_alpha_file()
        if not alpha_words:
            return

        # Filter to words we do not already have
        self.busy_text = "Filtering to only new words..."
        new_words = [
            word for word in alpha_words
            if bw.binary_search(self.words, word) is None
        ]
        already_have = len(alpha_words) - len(new_words)

        # There were no words that we didn't already have
        if not new_words:
            mb.showinfo(
                "Already have all words",
                f"All {len(alpha_words):,} alpha-only words are already " +
                "in the word list.",
            )
            return

        # We already have some of the words
        if already_have:
            mb.showinfo(
                "Already have some words",
                f"{already_have:,} words are already in the word list.",
            )

        # Filter to words of valid lengths
        self.busy_text = "Filtering out invalid length words..."
        new_lenvalid_words = [
            word for word in new_words if self.is_len_valid(word)
            ]
        len_invalid = len(new_words) - len(new_lenvalid_words)

        # There were no words of valid length
        if not new_lenvalid_words:
            mb.showerror(
                "Invalid word lengths",
                f"All {len(new_words):,} new words were rejected because " +
                f"they were not between {bw.WORD_LENGTH_MIN:,} and " +
                f"{bw.WORD_LENGTH_MAX:,} letters long.",
            )
            return

        # There were some words of invalid length
        if len_invalid:
            mb.showinfo(
                "Some invalid word lengths",
                f"{len_invalid:,} words were rejected because they were not " +
                f"between {bw.WORD_LENGTH_MIN:,} and {bw.WORD_LENGTH_MAX:,} " +
                "letters long.",
            )

        # Add the new words
        self.busy_text = "Combining lists..."
        self.words += new_lenvalid_words
        self.words.sort()

        # Update the query display
        self.update_query()

        # There are now major unsaved changes
        self.__mass_unsaved_changes(
            "Words added",
            f"Added {len(new_lenvalid_words):,} new words to the word list."
        )

    def mass_delete_words(self):
        """Delete a whole file's worth of words (threaded)"""

        self.thread_process(self._mass_delete_words)

    def _mass_delete_words(self):
        """Delete a whole file's worth of words"""

        # Get the list of words to delete
        del_words = self.__load_alpha_file()
        if not del_words:
            return

        # Filter down to words we actually have
        self.busy_text = "Finding words we do have..."
        old_words = [
            word for word in del_words
            if bw.binary_search(self.words, word) is not None
        ]
        dont_have = len(del_words) - len(old_words)

        # We don't have any of the words in the list
        if not old_words:
            mb.showinfo(
                "Don't have any of the words",
                f"None of the {len(del_words):,} words are in the word list.",
            )
            return

        # We only have some of the words in the list
        if dont_have:
            mb.showinfo(
                "Don't have some words",
                f"{dont_have:,} of the words are not in the wordlist.",
            )

        # Perform the deletion
        self.busy_text = "Deleting..."
        for word in old_words:
            self.__delete_word(word)

        # Words that were in the query may have been deleted, so update it.
        self.update_query()

        # There are now major unsaved changes
        self.__mass_unsaved_changes(
            "Words deleted",
            f"Removed {len(old_words):,} words from the word list.",
        )

    def delete_selected_word(self, event=None):
        """Delete the currently selected word

        Args:
            event (object): Unused, receives Tkinter callback event data.
                Defaults to None."""

        # No word is selected, so nothing to delete
        if self.selected_word == NO_WORD:
            return

        # Actually do the deleting
        self.__delete_word(self.selected_word)

        # Refresh the query list
        self.update_query()

        # There are now unsaved changes
        self.unsaved_changes = True

    def __delete_word(self, word: str, quiet=True):
        """Delete a word from our wordlist and popdefs

        Args:
            word (str): The word to delete.
            quiet (bool): If the word doesn't exist, this silences an error.
                Defaults to True, silence the error."""

        # Delete the word
        if bw.binary_search(self.words, word) is not None:
            self.words.remove(word)
        elif not quiet:
            mb.showerror(
                "Bad delete attempt",
                f"Attempted to delete '{word}' but it was not in the wordlist."
                )

        # Delete any popdef
        if self.defs.get(word) is not None:
            del self.defs[word]

    def del_invalid_len_words(self):
        """Remove all words of invalid length from the wordlist (threaded)"""

        self.thread_process(self._del_invalid_len_words)

    def _del_invalid_len_words(self):
        """Remove all words of invalid length from the wordlist"""

        # Comprehensively filter to words of invalid length
        invalid = [word for word in self.words if not self.is_len_valid(word)]

        # If all words were of valid length, notify the user
        if not invalid:
            mb.showinfo(
                "No invalid length words",
                f"All words are already between {bw.WORD_LENGTH_MIN:,} " +
                f"and {bw.WORD_LENGTH_MAX:,} letters long.",
            )
            return

        # Perform the deletion
        for word in invalid:
            self.__delete_word(word)

        # Update the query display
        self.update_query()

        # There are now mass unsaved changes
        self.__mass_unsaved_changes(
            "Invalid length words deleted",
            f"Found and deleted {len(invalid):,} words of invalid length " +
            "from the word list."
        )

    def del_orphaned_defs(self):
        """Find and delete any orphaned definitions (threaded)"""

        self.thread_process(self._del_orphaned_defs)

    def _del_orphaned_defs(self):
        """Find and delete any orphaned definitions"""

        self.busy_text = "Finding orphaned definitions..."
        orphaned = [
            word for word in self.defs if bw.binary_search(self.words, word) is None
        ]

        # No orphaned definitions found
        if not orphaned:
            mb.showinfo(
                "No orphaned definitions",
                "All recorded definitions have a word they are paired with.",
            )
            return

        # Delete the orphaned definitions
        self.busy_text = "Deleting orphans..."
        for o in orphaned:
            del self.defs[o]

        # There are now mass unsaved changes
        self.__mass_unsaved_changes(
            "Orphaned definitions deleted",
            f"Found and deleted {len(orphaned):,} orphaned definitions.",
        )

    def del_dupe_words(self):
        """Delete any duplicate word listings (threaded)"""

        self.thread_process(self._del_dupe_words)

    def _del_dupe_words(self):
        """Delete any duplicate word listings"""

        self.busy_text = "Searching for duplicates..."
        unduped = set(self.words)  # Sets don't have duplicate entries
        dupe_count = len(self.words) - len(unduped)

        # No duplicates
        if not dupe_count:
            mb.showinfo(
                "No duplicates found",
                "All words are only listed once.",
                )
            return

        # There were duplicates, so now convert and sort the set
        self.busy_text = "Ordering unduplicated set..."
        self.words = list(unduped)
        self.words.sort()

        # There are now mass unsaved changes.
        self.__mass_unsaved_changes(
            "Duplicates deleted",
            f"Found and removed {dupe_count:,} duplicate listings",
        )

    def auto_define(self):
        """Attempt to automatically define the currently selected word"""

        if self.selected_word == NO_WORD:
            return

        result, success = bw.build_auto_def(self.selected_word)
        if not success:
            mb.showerror("Could not autodefine", result)
            return

        # Write out the auto-definition, but do not save
        self.def_field.delete(0.0, tk.END)
        self.def_field.insert(0.0, result)

        # Enable or disable the definition handler buttons accordingly
        self.regulate_def_buttons()

    def mass_auto_define(self):
        """Find all words below the usage threshold,
            and try to define them (threaded)"""

        self.thread_process(self._mass_auto_define, message="Working...")

    def _mass_auto_define(self):
        """Find all words below the usage threshold, and try to define them"""

        if not bw.HAVE_WORDNET:
            mb.showerror(
                "No dictionary",
                "We need to download the NLTK wordnet English dictionary " +
                "for auto-defining. Please connect to the internet, then " +
                "restart the application.",
            )
            return

        # Find all words below the usage threshold and without a definition
        self.busy_text = "Finding undefined rare words..."
        defined_words = tuple(self.defs)
        words_to_define = [
            word for word in self.words
            if bw.get_word_usage(word) < bw.RARE_THRESH
            and bw.binary_search(defined_words, word) is None
        ]
        total = len(words_to_define)

        # Nothing to do?
        if not total:
            mb.showinfo(
                "No undefined rare words",
                "All words with a usage metric below the threshold already " +
                "have a popdef.",
            )
            return

        # Attempt to define all the words
        self.busy_text = f"Auto-defining {total:,} words..."
        fails = 0
        for word in words_to_define:
            result, success = bw.build_auto_def(word)
            if success:
                self.defs[word] = result
            else:
                fails += 1

        if fails == total:
            mb.showerror(
                "No definitions found",
                f"Failed to define any of the {total:,} undefined " +
                "rare words found.",
            )
            return

        # If there were successes, sort the updated popdefs alphabetically
        self.busy_text = "Sorting popdefs..."
        self.defs = dict(sorted(self.defs.items()))

        if fails:
            mb.showwarning(
                "Some definitions not found",
                f"Failed to define {fails:,} of the {total:,} undefined " +
                "rare words found.",
            )

        # There are now unsaved changes
        self.__mass_unsaved_changes(
            "Operation complete",
            f"Auto-defined {total - fails:,} words.",
        )


# Create an editor window
if __name__ == "__main__":
    Editor()
