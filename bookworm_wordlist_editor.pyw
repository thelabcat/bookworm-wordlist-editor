#!/usr/bin/env python3
"""BookWorm Deluxe Wordlist Editor

A graphical application for editing the word list and popdefs in BookWorm Deluxe.

S.D.G."""

from tkinter import *
from tkinter import messagebox as mb
from tkinter import simpledialog as dialog
from tkinter import filedialog
import os
import shutil
import sys
import threading
import bookworm_utils as bw

#File paths and related info
OP_PATH = __file__[:__file__.rfind(os.sep)] #The path of the script file
ICON_PATH = OP_PATH + os.sep + "bookworm_wordlist_editor.png"

BACKUP_SUFFIX = ".bak" #Suffix for backup files

#Miscellanious GUI settings
WINDOW_TITLE = "BookWorm Deluxe Wordlist Editor"
UNSAVED_WINDOW_TITLE = "*" + WINDOW_TITLE #Title of window when there are unsaved changes
RARE_COLS = ("#000", "#c00") #Index with int(<is rare?>)
WORDFREQ_DISP_PREFIX = "Usage: "
NO_WORD = "(no word selected)"
DEFFIELD_SIZE = (15, 5)

"""
The rules for unpacking the dictionary are simple:

    1. Read the number at the start of the line, and copy that many characters from the beginning of the previous word. (If there is no number, copy as many characters as you did last time.)

    2. Append the following letters to the word.
"""
#Popdefs format: WORD\t(word form) definiton; another definition

class Editor(Tk):
    """Main editor window"""
    def __init__(self):
        """Start the Tkinter app"""
        super().__init__()

        #The word list and definitions dictionary
        self.words = []
        self.defs = {}

        #Whatever word is selected
        self.selected_word = NO_WORD

        self.thread = None #Any thread the GUI might spawn

        self.busy_status = False #Is the GUI currently busy (all widgets disabled)?

        #Handle unsaved changes
        self.__unsaved_changes = False
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.title(WINDOW_TITLE) #Set the window title
        self.iconphoto(True, PhotoImage(file = ICON_PATH)) #Set the window icon
        self.build()

        #Load files
        self.game_path = bw.GAME_PATH_DEFAULT
        self.load_files(select = False, do_or_die = True)

        #Start the GUI loop
        self.mainloop()

    @property
    def unsaved_changes(self):
        """Check if we currently have unsaved changes"""
        return self.__unsaved_changes

    @unsaved_changes.setter
    def unsaved_changes(self, new_value):
        """Set if we have unsaved changes"""
        if not isinstance(new_value, bool):
            raise TypeError("Value for unsaved changes must be bool")
        self.__unsaved_changes = new_value

        #Set the window title based on wether changes are saved or not
        self.title((WINDOW_TITLE, UNSAVED_WINDOW_TITLE)[int(new_value)])

    def on_closing(self):
        """What to do if the user clicks to close this window"""
        if self.unsaved_changes:
            answer = mb.askyesnocancel("Unsaved changes", "There are currently unsaved changes to the word list and / or popdefs. Save before exiting?")

            #The user cancelled the exit
            if answer is None:
                return

            #The user clicked yes
            if answer:
                self.save_files()

        #Close the window
        self.destroy()

    def build(self):
        """Construct GUI"""

        self.bind("<Control-s>", self.save_files)

        #Menubar
        self.menubar = Menu(self)
        self["menu"] = self.menubar

        #File menu
        self.file_menu = Menu(self.menubar, tearoff=1)
        self.file_menu.add_command(label = "Open", command = lambda: self.load_files(select = True))
        self.file_menu.add_command(label = "Reload", command = lambda: self.load_files(select = False))
        self.file_menu.add_command(label = "Save", command = self.save_files)
        self.menubar.add_cascade(label = "File", menu = self.file_menu)

        #Edit menu
        self.edit_menu = Menu(self.menubar, tearoff = 1)
        self.edit_menu.add_command(label = "Delete orphaned definitions", command = self.del_orphaned_defs)
        self.edit_menu.add_command(label = "Delete words of invalid length", command = self.del_invalid_len_words)
        self.edit_menu.add_command(label = "Add several words", command = self.mass_add_words)
        self.edit_menu.add_command(label = "Delete several words", command = self.mass_delete_words)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu)

        #Test menu
        self.test_menu = Menu(self.menubar, tearoff = 1)
        self.test_menu.add_command(label = "Disable GUI", command = lambda: self.gui_busy_set(True))
        self.test_menu.add_command(label = "Enable GUI", command = lambda: self.gui_busy_set(False))
        # self.menubar.add_cascade(label = "Tests", menu = self.test_menu) #Uncomment this to enable the test menu

        self.menubar_entries = ("File", "Edit") #Menus to disable when busy

        self.widgets_to_disable = [] #Widgets to disable when busy

        #Frame for list
        self.list_frame = Frame(self)
        self.list_frame.grid(row = 0, column = 0, sticky = NSEW)
        self.rowconfigure(0, weight = 1)
        self.columnconfigure(0, weight = 1)

        #Subframe for search system
        self.search_frame=Frame(self.list_frame)
        self.search_frame.grid(row = 0, columnspan = 2, sticky = NSEW)

        #Search system
        self.search_label = Label(self.search_frame, text = "Search:")
        self.search_label.grid(row = 0, column = 0, sticky = N + S + W)
        self.search = StringVar()
        self.search.trace_add("write", self.update_query)
        self.search_entry = Entry(self.search_frame, textvariable = self.search)
        self.search_entry.grid(row = 0, column = 1, sticky = NSEW)
        self.search_frame.columnconfigure(1, weight = 1)
        self.search_clear_bttn = Button(self.search_frame, text = "X", command = lambda: self.search.set(""))
        self.search_clear_bttn.grid(row = 0, column = 2, sticky = N + S + E)
        self.widgets_to_disable += [self.search_label, self.search_entry, self.search_clear_bttn]

        self.query_list=Variable(value = ["foo", "bar", "bazz"])
        self.query_box=Listbox(self.list_frame, listvariable = self.query_list, height = 10, selectmode = SINGLE, exportselection = False)
        self.query_box.bind('<<ListboxSelect>>', self.selection_updated)
        self.query_box.grid(row = 1, column = 0, sticky = NSEW)
        self.widgets_to_disable.append(self.query_box)

        self.query_box_scrollbar = Scrollbar(self.list_frame, orient = VERTICAL, command = self.query_box.yview)
        self.query_box['yscrollcommand'] = self.query_box_scrollbar.set
        self.query_box_scrollbar.grid(row = 1, column = 1, sticky = N + S + E)
        # self.widgets_to_disable.append(self.query_box_scrollbar) #Scrollbar cannot be state disabled
        self.list_frame.rowconfigure(1, weight = 1)
        self.list_frame.columnconfigure(0, weight = 1)

        self.add_word_bttn = Button(self.list_frame, text = "Add word", command = self.add_word)
        self.add_word_bttn.grid(row = 2, columnspan = 2, sticky = NSEW)
        self.widgets_to_disable.append(self.add_word_bttn)

        #Frame for word and definition
        self.worddef_frame = Frame(self)
        self.worddef_frame.grid(row = 0, column = 1, sticky = NSEW)
        self.worddef_frame.bind_all("<Key>", self.regulate_def_buttons)
        self.columnconfigure(1, weight = 1)

        #Subframe for word and usage display
        self.worddisp_frame = Frame(self.worddef_frame)
        self.worddisp_frame.grid(row = 0, columnspan = 2, sticky = E + W)
        self.worddef_frame.columnconfigure(0, weight = 1)
        self.worddef_frame.columnconfigure(1, weight = 1)

        self.word_display = Label(self.worddisp_frame, text = NO_WORD)
        self.word_display.grid(row = 0, column = 0, sticky = E + W)
        self.widgets_to_disable.append(self.word_display)
        self.worddisp_frame.columnconfigure(0, weight = 1)

        self.usage_display = Label(self.worddisp_frame, text = "")
        self.usage_display.grid(row = 0, column = 1, sticky = E)
        self.widgets_to_disable.append(self.usage_display)

        self.def_field = Text(self.worddef_frame, width = DEFFIELD_SIZE[0], height = DEFFIELD_SIZE[1], wrap = WORD)
        self.def_field.grid(row = 1, columnspan = 2, sticky = NSEW)
        self.widgets_to_disable.append(self.def_field)
        self.worddef_frame.rowconfigure(1, weight = 1)
        self.worddef_frame.columnconfigure(0, weight = 1)
        self.worddef_frame.columnconfigure(1, weight = 1)

        self.reset_def_bttn = Button(self.worddef_frame, text = "Reset definition", command = self.selection_updated)
        self.reset_def_bttn.grid(row = 2, column = 0, sticky = NSEW)
        self.widgets_to_disable.append(self.reset_def_bttn)

        self.save_def_bttn = Button(self.worddef_frame, text = "Save definition", command = self.update_definition)
        self.save_def_bttn.grid(row = 2, column = 1, sticky = NSEW)
        self.widgets_to_disable.append(self.save_def_bttn)

        self.autodef_bttn = Button(self.worddef_frame, text = "Auto-define", command = self.auto_define)
        self.autodef_bttn.grid(row = 3, columnspan = 2, sticky = NSEW)
        self.widgets_to_disable.append(self.autodef_bttn)

        self.del_bttn = Button(self.worddef_frame, text = "Delete word", command = self.del_word)
        self.del_bttn.grid(row = 4, columnspan = 2, sticky = NSEW)
        self.widgets_to_disable.append(self.del_bttn)

        #Busy text that goes over everything
        self.busy_text = StringVar(self)
        self.busy_label = Label(self, textvariable = self.busy_text)
        self.busy_label.grid(row = 0, column = 0, columnspan = 2)

    def thread_process(self, method, message = "Working..."):
        """Run a method in a thread and set the GUI to busy while we do it"""
        self.thread = threading.Thread(target = lambda: self.busy_run(method, message), daemon = True)
        self.thread.start()

    def busy_run(self, method, message = "Working.."):
        """Set the GUI to busy, run a method, then set the GUI to normal again"""
        self.gui_busy_set(True, message = message)
        method()
        self.gui_busy_set(False)

    def gui_busy_set(self, busy_status, message = "Working..."):
        """Set the GUI to busy or not busy"""
        if busy_status:
            self.busy_text.set(message)
            self.busy_label.lift()
        else:
            self.busy_text.set("")
            self.busy_label.lower()

        new_state = (NORMAL, DISABLED)[int(busy_status)]
        for entry in self.menubar_entries:
            self.menubar.entryconfig(entry, state = new_state)
        for widget in self.widgets_to_disable:
            widget.config(state = new_state)

        #For other widget disablers to reference
        self.busy_status = busy_status

        #Rerun any unique widget disablers
        self.unique_disable_handlers()

    def unique_disable_handlers(self):
        """Run all unique widget disabling handlers"""
        self.regulate_word_buttons()
        self.regulate_def_buttons()

    def regulate_word_buttons(self):
        """Enable or disable the word handling buttons based on if a word is selected"""
        #Do not enable or disable these widgets if the GUI is busy
        if self.busy_status:
            return

        #buttons should be disabled if no word is selected
        new_state = (NORMAL, DISABLED)[int(self.selected_word == NO_WORD)]

        for button in (self.autodef_bttn, self.del_bttn):
            button.config(state = new_state)

    def regulate_def_buttons(self, *args):
        """Check if the definition has changed, and dis/en-able the reset and save buttons accordingly"""
        #Do not enable or disable these widgets if the GUI is busy
        if self.busy_status:
            return

        def_entry = self.def_field.get("0.0", END).strip() #Get the current entry

        #There is no selected word
        if self.selected_word == NO_WORD:
            new_state = DISABLED

        #We have an old definition for this word
        elif self.selected_word in self.defs.keys():
            #The user deleted the old definition
            if not def_entry:
                new_state = NORMAL

            #The old definition is the same as the new one
            elif self.defs[self.selected_word] == def_entry:
                new_state = DISABLED

            #There is a new definition
            else:
                new_state = NORMAL

        #We do not have an old definition, and there is a new one
        elif def_entry:
            new_state = NORMAL

        #There was no old or new definition
        else:
            new_state = DISABLED

        for button in (self.reset_def_bttn, self.save_def_bttn):
            button.config(state = new_state)

    def load_files(self, select = True, do_or_die = False):
        """Load the wordlist and the popdefs (threaded)"""
        self.thread_process(lambda: self.__load_files(select, do_or_die), message = "Loading...")

    def __load_files(self, select = True, do_or_die = False):
        """Load the wordlist and the popdefs"""
        #Ask the user for a directory if the current one is invalid, even if the select argument is false
        select = select or not bw.is_game_path_valid(self.game_path)

        #While we need to select something
        while select:
            while True: #Keep asking for an input
                response = filedialog.askdirectory(title = "Game directory", initialdir = self.game_path)
                if response:
                    break #We got a response, so break the loop

                if not do_or_die:
                    return #We did not get a response, but we aren't supposed to force. Assumes the game is not installed to root directory.

                if mb.askyesno("Cannot cancel", "The program needs a valid directory to continue. Exit the program?"): #Do or die
                    self.destroy()
                    sys.exit()

            select = not bw.is_game_path_valid(response + os.sep) #If the game path is valid, we are no longer selecting
            if select:
                mb.showerror("Invalid directory", "Could not find the word list and pop definitions here.")
            else:
                self.game_path = response + os.sep #We got a new valid directory

        #First, load the wordlist
        with open(self.game_path + bw.WORDLIST_FILE, encoding = bw.WORDLIST_ENC) as f:
            self.words = bw.unpack_wordlist(f.read().strip())

        #Then, load the popdefs
        with open(self.game_path + bw.POPDEFS_FILE, encoding = bw.POPDEFS_ENC) as f:
            self.defs = bw.unpack_popdefs(f.read().strip())

        #Update the query list
        self.update_query()

        #The files were just (re)loaded, so there are no unsaved changes
        self.unsaved_changes = False

    def save_files(self, *args, backup=False):
        """Save the worldist and popdefs"""
        #*args is there to receive unnecessary event data as this is a callback method

        #Backup system
        if backup:
            try:
                shutil.copy(self.game_path + bw.WORDLIST_FILE, self.game_path + bw.WORDLIST_FILE + BACKUP_SUFFIX)
                shutil.copy(self.game_path + bw.POPDEFS_FILE, self.game_path + bw.POPDEFS_FILE + BACKUP_SUFFIX)
            except FileNotFoundError:
                mb.showerror("Backup failed", "Could not back up the original files because they have disappeared.")

        #First, save the wordlist
        with open(self.game_path + bw.WORDLIST_FILE, "w", encoding = bw.WORDLIST_ENC) as f:
            f.write(bw.pack_wordlist(self.words))

        #Then, save the popdefs
        with open(self.game_path + bw.POPDEFS_FILE, "w", encoding = bw.POPDEFS_ENC) as f:
            f.write(bw.pack_popdefs(self.defs))

        self.unsaved_changes = False #All changes are now saved

    def selection_updated(self, *args):
        """A new word has been selected, update everything"""
        #*args is there to receive unnecessary event data as this is a callback method

        #Update what word is selected
        self.selected_word = self.get_selected_word()

        self.word_display.config(text = self.selected_word) #Display the current word
        self.load_definition() #Load and display the current definition

        #If no word is selected, clear the usage statistic display
        if self.selected_word == NO_WORD:
            self.usage_display.config(text = "")

        #Otherwise, try to load and display usage statistics
        else:
            try:
                usage = bw.get_word_usage(self.selected_word)
                self.usage_display.config(text = WORDFREQ_DISP_PREFIX + str(usage), fg = RARE_COLS[int(usage < bw.RARE_THRESH)])
            except LookupError:
                print("Usage lookup faliure. See issue #5.")

        #Enable or disable the word handling buttons based on the selection
        self.regulate_word_buttons()

    def update_query(self, *args):
        """Update the list of search results"""
        #*args is there to receive unnecessary event data as this is a callback method

        #Do not allow any capitalization or non-letters in the search field
        self.search.set("".join([char for char in self.search.get().lower() if char in bw.ALPHABET]))

        search = self.search.get()

        #Comprehensively filter the wordlist to only matching words
        if search:
            query = [word for word in self.words if search in word]
            #Sort search results by how close the search query is to the beginning
            query.sort(key = lambda x: x.index(search))

        #The search was cleared
        else:
            query = self.words

        #Update the query list
        self.query_list.set(query)

        #There was a search entered, and it returned values, highlight the top result
        if search and query:
            self.set_selected_word(query[0])

        #The search was cleared or returned no search results
        else:
            self.set_selected_word(None)

    def get_selected_word(self):
        """Get the currently selected word"""
        if self.query_box.curselection(): #Something is selected
            #Return the word at the starting index of the selection
            #(only one word can be selected so the end doesn't matter)
            return self.query_box.get(self.query_box.curselection()[0])
        return NO_WORD

    def set_selected_word(self, word):
        """Change what word is selected, if the word is in the query"""
        #The word is in our current query, so select and view it
        if word and word in self.query_list.get():
            word_query_index = self.query_list.get().index(word)
            self.query_box.selection_clear(0, END)
            self.query_box.selection_set(word_query_index)
            self.query_box.see(word_query_index)

        #Something not in the query list was given, clear the selection
        else:
            self.query_box.selection_clear(0, END)

        self.selection_updated()

    def load_definition(self):
        """Load the definition of the selected word if there is one"""

        #Clear any old displayed definition, regardless
        self.def_field.delete(0.0, END)

        #If we have a definition for this word, display it
        if self.selected_word != NO_WORD and self.selected_word in self.defs.keys():
            self.def_field.insert(0.0, self.defs[self.selected_word])

        #Disable definition reset and save buttons now that a definition was (re)loaded
        self.regulate_def_buttons()

    def update_definition(self):
        """Update the stored definition for a word"""
        def_entry = self.def_field.get("0.0", END).strip()

        #We have a definition to save
        if def_entry:
            self.defs[self.selected_word] = def_entry

        #We had a definition, and it has been deleted
        elif self.selected_word in self.defs.keys():
            del self.defs[self.selected_word]

        #There are now unsaved changes
        self.unsaved_changes = True

        #In case any whitespace was stripped off of the start or end, reload the definition
        self.load_definition()

        #Disable definition reset and save buttons now that the definition was saved
        self.regulate_def_buttons()

    def is_len_valid(self, word, notify = False):
        """Check if a word's length is valid. Notify triggers a GUI popup if length is invalid"""
        if notify and not bw.WORD_LENGTH_MIN <= len(word) <= bw.WORD_LENGTH_MAX:
            #Dialog auto-selects the word "short" or "long" based on wether the invalid length was a too long case or not
            mb.showerror("Word is too " + ("short", "long")[int(len(word) > bw.WORD_LENGTH_MAX)], f"Word must be between {bw.WORD_LENGTH_MIN} and {bw.WORD_LENGTH_MAX} letters long.")

        return bw.WORD_LENGTH_MIN <= len(word) <= bw.WORD_LENGTH_MAX

    def add_word(self):
        """Create a new word entry"""
        new = dialog.askstring("New word", "Enter the new word to add:")

        #Allow the user to cancel, and also ensure the word is of allowed length
        if not new or not self.is_len_valid(new, notify = True):
            return
        new = new.lower()

        #Ensure that the word is only letters
        for char in new:
            if char not in bw.ALPHABET:
                mb.showerror("Invalid character found", "Word must be only letters (no numbers or symbols).")
                return

        #If the word really is new, add it
        if new not in self.words:
            #Add the new word
            self.words.append(new)
            self.words.sort()

            #Update the query
            self.update_query()

            #There are now unsaved changes
            self.unsaved_changes = True

        else:
            mb.showinfo("Already have word", f"The word {new} is already in the word list.")

        #Highlight and scroll to the new word even if it wasn't actually new, so long as it is in our current search results
        self.set_selected_word(new)

    def mass_add_words(self):
        """Add a whole file's list of words (threaded)"""
        self.thread_process(self.__mass_add_words)

    def __mass_add_words(self):
        """Add a whole file's worth of words"""

        #Open and read a file with a human-readable list of new words
        with filedialog.askopenfile(title = "Select human-readable list of words", filetypes = [("Plain text", "*.txt")]) as f:
            #The user cancelled via the open file dialog
            if not f:
                return

            #Read the file
            text = f.read().strip()

        #filter file to only letters and spaces
        alpha_text = "".join([c for c in text if c.lower() in bw.ALPHABET or c.isspace()])

        #There was no text besides non-alpha symbols
        if not alpha_text:
            mb.showerror("Invalid file", "File did not contain any alphabetic text.")
            return

        #Get all words, delimited by whitespace, in lowercase
        add_words = [word.strip().lower() for word in alpha_text.split()]

        #There were no words
        if not add_words:
            mb.showerror("Invalid file", "Did not find any words in file.")
            return

        #Filter to words we do not already have
        new_words = [word for word in add_words if word not in self.words] #Filter words to ones we don't have yet
        already_have = len(add_words) - len(new_words)

        #There were no words that we didn't already have'
        if not new_words:
            mb.showinfo("Already have all words", f"All {len(add_words)} words are already in the word list.")
            return

        #We already have some of the words
        if already_have:
            mb.showinfo("Already have some words", f"{already_have} words are already in the word list.")

        #Filter to words of valid lengths
        new_lenvalid_words = [word for word in new_words if self.is_len_valid(word)]
        len_invalid = len(new_words) - len(new_lenvalid_words)

        #There were no words of valid length
        if not new_lenvalid_words:
            mb.showerror("Invalid word lengths", f"All {len(new_words)} new words were rejected because they were not between {bw.WORD_LENGTH_MIN} and {bw.WORD_LENGTH_MAX} letters long.")
            return

        #There were some words of invalid length
        if len_invalid:
            mb.showinfo("Some invalid word lengths", f"{len_invalid} words were rejected because they were not between {bw.WORD_LENGTH_MIN} and {bw.WORD_LENGTH_MAX} letters long.")

        #Add the new words
        self.words += new_lenvalid_words
        self.words.sort()

        #Update the query display
        self.update_query()

        #There are now unsaved changes
        self.unsaved_changes = True

        if mb.askyesno("Words added", f"Added {new_lenvalid_words} new words to the word list. Save changes to disk now?"):
            self.save_files()

    def mass_delete_words(self):
        """Delete a whole file's worth of words (threaded)"""
        self.thread_process(self.__mass_delete_words)

    def __mass_delete_words(self):
        """Delete a whole file's worth of words"""
        f = filedialog.askopenfile(title = "Select human-readable list of words", filetypes = [("Plain text", "*.txt")])
        if not f: #The user cancelled
            return
        text = f.read().strip()
        f.close()

        alpha_text = "".join([c for c in text if c.lower() in bw.ALPHABET or c.isspace()]) #Filter text to alphabet and whitespace
        if not alpha_text:
            mb.showerror("Invalid file", "File did not contain any alphabetic text.")
            return

        del_words = [word.strip().lower() for word in alpha_text.split()] #Get all words, delimited by whitespace, in lowercase
        if not del_words:
            mb.showerror("Invalid file", "Did not find any words in file.")
            return

        old_words = [word for word in del_words if word in self.words] #Filter words to ones we do have
        dont_have = len(del_words) - len(old_words)
        if not old_words:
            mb.showinfo("Don't have any of the words", f"None of the {len(del_words)} words are in the word list.")
            return

        if dont_have:
            mb.showinfo("Don't have some words", f"{dont_have} of the words are not in the wordlist.")

        for word in old_words:
            self.words.remove(word)

        #Update the query display
        self.update_query()

        #There are now unsaved changes
        self.unsaved_changes = True

        if mb.askyesno("Words deleted", f"Removed {len(old_words)} words from the word list. Save changes to disk now?"):
            self.save_files()

    def del_word(self, *args):
        """Delete the currently selected word"""
        #No word is selected, so nothing to delete
        if self.selected_word == NO_WORD:
            return

        #Remove the word from our words list
        self.words.remove(self.selected_word)

        #If we have a definition saved for this word, delete it
        if self.selected_word in self.defs.keys():
            del self.defs[self.selected_word]

        #Refresh the query list
        self.update_query()

        #There are now unsaved changes
        self.unsaved_changes = True

    def del_invalid_len_words(self):
        """Remove all words of invalid length from the wordlist (threaded)"""
        self.thread_process(self.__del_invalid_len_words)

    def __del_invalid_len_words(self):
        """Remove all words of invalid length from the wordlist"""
        invalid = [word for word in self.words if not self.is_len_valid(word)]
        if not invalid:
            mb.showinfo("No invalid length words", f"All words are already between {bw.WORD_LENGTH_MIN} and {bw.WORD_LENGTH_MAX} letters long.")
            return

        for word in invalid:
            self.words.remove(word)

        #Update the query display
        self.update_query()

        #There are now unsaved changes
        self.unsaved_changes = True

        if mb.askyesno("Invalid length words deleted", f"Found and deleted {len(invalid)} words of invalid length from the word list. Save changes to disk now?"):
            self.save_files()

    def del_orphaned_defs(self):
        """Find and delete any orphaned definitions (threaded)"""
        self.thread_process(self.__del_orphaned_defs)

    def __del_orphaned_defs(self):
        """Find and delete any orphaned definitions"""
        orphaned = [word for word in self.defs.keys() if word not in self.words]

        #No orphaned definitions found
        if not orphaned:
            mb.showinfo("No orphaned definitions", "All recorded definitions have a word they are paired with.")
            return

        #Delete the orphaned definitions
        for o in orphaned:
            del self.defs[o]

        #There are now unsaved changes
        self.unsaved_changes = True

        #Offer to save changes
        if mb.askyesno("Orphaned definitions deleted", f"Found and deleted {len(orphaned)} orphaned definitions. Save now?"):
            self.save_files()

    def auto_define(self):
        """Pull a definition from the web and show it"""
        word = self.selected_word
        if word == NO_WORD:
            return

        definition = bw.build_auto_def(word)
        if not definition:
            mb.showerror("Could not autodefine", f"No useful definition returned from PyDictionary for {word}")
            return

        #Write out the auto-definition, but do not save
        self.def_field.delete(0.0, END)
        self.def_field.insert(0.0, definition)

        #Enable or disable the definition handler buttons accordingly
        self.regulate_def_buttons()

#Create an editor window
if __name__ == "__main__":
    Editor()
