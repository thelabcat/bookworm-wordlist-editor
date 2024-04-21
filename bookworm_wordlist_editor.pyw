#!/usr/bin/env python3
#Bookworm Deluxe wordlist editor
#S.D.G.

from tkinter import *
from tkinter import messagebox as mb
from tkinter import simpledialog as dialog
from tkinter import filedialog
import glob
import os
from PyDictionary import PyDictionary as dic
from wordfreq import zipf_frequency
import shutil
import getpass
import platform
import sys
import time #For debug

NO_WORD="(no word selected)"
DEFFIELD_SIZE=(15, 5)

ALPHABET = "abcdefghijklmnopqrstuvwxyz"
LANG="en" #Language to use when checking word rarity
NUMERIC="1234567890"
WORD_TYPES={"Noun":"n.", "Verb":"v.", "Adjective":"adj.", "Adverb":"adv.", "Interjection":"int.", "Preposition":"prep.", "Conjugation":"conj."}
RARE_THRESH=3.5 #Words with usage less than this get definitions
RARE_COLS=("#000", "#c00") #Index with int(<is rare?>)
USER=getpass.getuser()
GAME_PATH_DEFAULT={"Linux":"/home/%s/.wine/drive_c/Program Files/PopCap Games/BookWorm Deluxe/" % USER,
                   "Darwin":"/Users/%s/.wine/drive_c/Program Files/PopCap Games/BookWorm Deluxe/" % USER,
                   "Windows":"C:\\Program Files\\PopCap Games\\BookWorm Deluxe\\"
                   }[platform.system()] #Get the default game path based on the OS
WORDLIST_FILE="wordlist.txt"
POPDEFS_FILE="popdefs.txt"
POPDEFS_ENC="iso 8859-15" #Encoding to use when writing the popdefs.txt file
BACKUP_SUFFIX=".bak"
WORDFREQ_DISP_PREFIX="Usage: "

"""
The rules for unpacking the dictionary are simple:

    1. Read the number at the start of the line, and copy that many characters from the beginning of the previous word. (If there is no number, copy as many characters as you did last time.)

    2. Append the following letters to the word.
"""
#Popdefs format: WORD\t(word form) definiton; another definition

class Editor(Tk):
    def __init__(self):
        """Main editor window"""
        super(type(self), self).__init__()
        self.title("Bookworm Wordlist Editor")
        self.build()
        self.game_path=GAME_PATH_DEFAULT
        self.load_files(select=False, do_or_die=True)
        self.mainloop()
        
    def build(self):
        """Construct GUI"""

        self.bind("<Control-s>", self.save_files)

        #Menubar
        self.menubar=Menu(self)
        self["menu"]=self.menubar

        #File menu
        self.file_menu=Menu(self.menubar, tearoff=1)
        self.file_menu.add_command(label="Open", command=lambda: self.load_files(select=True))
        self.file_menu.add_command(label="Reload", command=lambda: self.load_files(select=False))
        self.file_menu.add_command(label="Save", command=self.save_files)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        #Edit menu
        self.edit_menu = Menu(self.menubar, tearoff = 1)
        self.edit_menu.add_command(label = "Delete orphaned definitions", command = self.del_orphaned_defs)
        self.edit_menu.add_command(label = "Add several words", command = self.mass_add_words)
        self.edit_menu.add_command(label = "Delete several words", command = self.mass_delete_words)
        self.menubar.add_cascade(label="Edit", menu=self.edit_menu)

        #Frame for list
        self.list_frame=Frame(self)
        self.list_frame.grid(row=0, column=0, sticky=N+S+E+W)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        #Subframe for search system
        self.search_frame=Frame(self.list_frame)
        self.search_frame.grid(row=0, columnspan=2, sticky=N+S+E+W)

        #Search system
        Label(self.search_frame, text="Search:").grid(row=0, column=0, sticky=N+S+W)
        self.search=StringVar()
        self.search.trace_add("write", self.update_query)
        self.search_entry=Entry(self.search_frame, textvariable=self.search)
        self.search_entry.grid(row=0, column=1, sticky=N+S+E+W)
        self.search_frame.columnconfigure(1, weight=1)
        Button(self.search_frame, text="X", command=lambda: self.search_entry.delete(0, END)).grid(row=0, column=2, sticky=N+S+E)
        
        self.query_list=Variable(value=["foo", "bar", "bazz"])
        self.query_box=Listbox(self.list_frame, listvariable=self.query_list, height=10, selectmode=SINGLE, exportselection=False)
        self.query_box.bind('<<ListboxSelect>>', self.selection_updated)
        self.query_box.grid(row=1, column=0, sticky=N+S+E+W)
        
        self.query_box_scrollbar=Scrollbar(self.list_frame, orient=VERTICAL, command=self.query_box.yview)
        self.query_box['yscrollcommand'] = self.query_box_scrollbar.set
        self.query_box_scrollbar.grid(row=1, column=1, sticky=N+S+E)
        self.list_frame.rowconfigure(1, weight=1)
        self.list_frame.columnconfigure(0, weight=1)

        Button(self.list_frame, text="New", command=self.new_word).grid(row=2, columnspan=2, sticky=N+S+E+W)

        #Frame for word and definition
        self.worddef_frame=Frame(self)
        self.worddef_frame.grid(row=0, column=1, sticky=N+S+E+W)
        self.columnconfigure(1, weight=1)
        
        #Subframe for word and usage display
        self.worddisp_frame=Frame(self.worddef_frame)
        self.worddisp_frame.grid(row=0, columnspan=2, sticky=E+W)
        self.worddef_frame.columnconfigure(0, weight=1)
        self.worddef_frame.columnconfigure(1, weight=1)
        
        self.word_display=Label(self.worddisp_frame, text=NO_WORD)
        self.word_display.grid(row=0, column=0, sticky=E+W)
        self.worddisp_frame.columnconfigure(0, weight=1)

        self.usage_display=Label(self.worddisp_frame, text="")
        self.usage_display.grid(row=0, column=1, sticky=E)
        
        self.def_field=Text(self.worddef_frame, width=DEFFIELD_SIZE[0], height=DEFFIELD_SIZE[1], wrap=WORD)
        #self.def_field.bind("<FocusOut>", self.update_definition)
        self.def_field.grid(row=1, columnspan=2, sticky=N+S+E+W)
        self.worddef_frame.rowconfigure(1, weight=1)
        self.worddef_frame.columnconfigure(0, weight=1)
        self.worddef_frame.columnconfigure(1, weight=1)

        self.reload_bttn=Button(self.worddef_frame, text="Reset definition", command=self.selection_updated)
        self.reload_bttn.grid(row=2, column=0, sticky=N+S+E+W)
        
        self.save_bttn=Button(self.worddef_frame, text="Save definition", command=self.update_definition)
        self.save_bttn.grid(row=2, column=1, sticky=N+S+E+W)

        self.autodef_bttn=Button(self.worddef_frame, text="Auto-define", command=self.auto_define)
        self.autodef_bttn.grid(row=3, columnspan=2, sticky=N+S+E+W)
        
        self.del_bttn=Button(self.worddef_frame, text="Delete word", command=self.del_word)
        self.del_bttn.grid(row=4, columnspan=2, sticky=N+S+E+W)

    def mass_add_words(self):
        """Add a whole file's worth of words"""
        f = filedialog.askopenfile(title = "Select human-readable list of words", filetypes = [("Plain text", "*.txt")])
        if not f: #The user cancelled
            return
        text = f.read().strip()
        f.close()

        alpha_text = "".join([c for c in text if c.lower() in ALPHABET or c.isspace()]) #Filter text to alphabet and whitespace
        if not alpha_text:
            mb.showerror("Invalid file", "File did not contain any alphabetic text.")
            return

        add_words = [word.strip().lower() for word in alpha_text.split()] #Get all words, delimited by whitespace, in lowercase
        if not add_words:
            mb.showerror("Invalid file", "Did not find any words in file.")
            return

        new_words = [word for word in add_words if word not in self.words] #Filter words to ones we don't have yet
        already_have = len(add_words) - len(new_words)
        if not new_words:
            mb.showinfo("Already have all words", "All %i words are already in the word list." % len(add_words))
            return

        if already_have:
            mb.showinfo("Already have some words", "%i of these words are already in the wordlist." % already_have)

        self.words += new_words
        self.words.sort()
        if mb.askyesno("Words added", "Added %i new words to the word list. Save changes to disk now?" % len(new_words)):
            self.save_files()

    def mass_delete_words(self):
        """Delete a whole file's worth of words"""
        f = filedialog.askopenfile(title = "Select human-readable list of words", filetypes = [("Plain text", "*.txt")])
        if not f: #The user cancelled
            return
        text = f.read().strip()
        f.close()

        alpha_text = "".join([c for c in text if c.lower() in ALPHABET or c.isspace()]) #Filter text to alphabet and whitespace
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
            mb.showinfo("Don't have any of the words", "None of the %i words were in the word list." % len(del_words))
            return

        if dont_have:
            mb.showinfo("Don't have some words", "%i of these words are not in the wordlist." % dont_have)

        for word in old_words:
            self.words.remove(word)
        if mb.askyesno("Words deleted", "Removed %i words from the word list. Save changes to disk now?" % len(old_words)):
            self.save_files()

    def unpack_wordlist(self, wordlist):
        """Given a wordlist as text, unpack into a list of words"""
        words=[]
        copy=0
        for listing in wordlist.splitlines():
            copyread=""
            for i in range(len(listing)):
                if listing[i] not in NUMERIC:
                    break #i is now the index of the first letter in the listing
                copyread+=listing[i]

            if copyread: #If there a new copycount, don't reuse the last one
                copy=int(copyread)

            if words: #Copy from the last word, or not
                words.append(words[-1][:copy]+listing[i:])
                
            elif not copy: #Do not copy from the last word, but trim off the zero copy count
                words.append(listing[i:])

            else:
                raise ValueError("Copy count is %i but there are no words yet." % copy)
            
        return words

    def pack_wordlist(self, words):
        """Given a list of words, pack into a wordlist as text"""
        listings=[]
        oldcopy=0
        for i in range(len(words)):
            if i==0:
                listings.append(words[i])
                continue
            for copy in range(min((len(words[i-1]), len(words[i])))):
                if words[i-1][copy] != words[i][copy]:
                    break #copy is now set to the index of the first letter the new word does not have in common with the old one
            
            listings.append(str(copy)*(copy!=oldcopy)+words[i][copy:])
            oldcopy=copy
            
        return "\n".join(listings).strip()

    def selection_updated(self, *args):
        """A new word has been selected, update everything"""
        self.word_display.config(text=self.get_selected_word())
        if self.get_selected_word()==NO_WORD:
            self.usage_display.config(text="")
            return
        usage=zipf_frequency(self.get_selected_word(), LANG)
        self.usage_display.config(text=WORDFREQ_DISP_PREFIX+str(usage), fg=RARE_COLS[int(usage<RARE_THRESH)])
        self.load_definition()

    def load_definition(self):
        """Load the definition of the selected word if there is one"""
        self.def_field.delete(0.0, END)
        if self.get_selected_word() in self.defs.keys():
            self.def_field.insert(0.0, self.defs[self.get_selected_word()])

    def update_definition(self, *args):
        """Update the stored definition for a word"""
        def_entry=self.def_field.get("0.0",END).strip()
        if def_entry: #There is a definition entry
            self.defs[self.get_selected_word()]=def_entry
        elif self.get_selected_word() in self.defs.keys():
            del self.defs[self.get_selected_word()]

    def new_word(self, *args):
        """Create a new word entry"""
        new=dialog.askstring("New word", "Enter the new word to add:")
        if not new:
            return
        new=new.lower()
        if new not in self.words:
            self.words.append(new)
            self.words.sort()
            self.update_query()
        if new in self.query_list.get():
            self.query_box.activate(self.query_list.get().index(new)) #If the new word is now in the query, select it

    def update_query(self, *args):
        """Update the list of search results"""
        self.search.set(self.search.get().lower())
        query = [word for word in self.words if self.search.get() in word] #Comprehensively filter the wordlist to only matching words
        query.sort(key = lambda x: x.index(self.search.get())) #Sort search results by how close the search query is to the beginning
        self.query_list.set(query)
        self.selection_updated()

    def build_def(self, word):
        """Construct a definition line given a word"""
        def_raw=dic.meaning(word, disable_errors=True)
        if not def_raw:
            print("No definition found for", word)
            return None
        
        for typ in tuple(def_raw.keys()):
            for meaning in def_raw[typ][:]:
                if meaning[0]=="(": #Remove special context defintions
                    def_raw[typ].remove(meaning)
            if not def_raw[typ]: #Remove emptied word type definitions
                del def_raw[typ]
                
        if not def_raw:
            print("No appropriate definition found for", word)
            return None
        
        return "; ".join(["("+WORD_TYPES[key]+") "+def_raw[key][0].capitalize() for key in def_raw.keys()])

    def auto_define(self, *args):
        """Pull a definition from the web and show it"""
        word = self.get_selected_word()
        if word == NO_WORD:
            return
        
        definition = self.build_def(word)
        if not definition:
            mb.showerror("Could not autodefine", "No useful definition returned from PyDictionary for %s." % word)
            return
        
        self.def_field.delete(0.0, END)
        self.def_field.insert(0.0, definition)

    def get_selected_word(self):
        """Get the currently selected word"""
        if self.query_box.curselection():
            return self.query_box.get(self.query_box.curselection()[0])
        return NO_WORD

    def del_word(self, *args):
        """Delete the currently selected word"""
        if self.get_selected_word() == NO_WORD:
            return
        self.words.remove(self.get_selected_word())
        if self.get_selected_word() in self.defs.keys():
            del self.defs[self.get_selected_word()]
        self.update_query()
        self.selection_updated()

    def is_game_path_valid(self, path):
        """Check if the wordlist and popdefs files exists in the game path"""
        dircheck = glob.glob(path + "*")
        return (path+WORDLIST_FILE in dircheck and path + POPDEFS_FILE in dircheck)

    def load_files(self, *args, select = True, do_or_die = False):
        """Load the wordlist and the popdefs"""
        select = select or not self.is_game_path_valid(self.game_path) #Ask the user for a directory if the current one is invalid, even if the select argument is false
        while select:
            while True: #Possible to force the user to select something and not cancel
                response = filedialog.askdirectory(title = "Game directory", initialdir = self.game_path)
                if response:
                    break #We got a response, so break the loop
                elif not do_or_die:
                    return #We did not get a response, but we aren't supposed to force. Assumes the game is not installed to root directory.
                if mb.askyesno("Cannot cancel", "The program needs a valid directory to continue. Exit the program?"): #Do or die
                    self.destroy()
                    sys.exit()
                
            select = not self.is_game_path_valid(response + os.sep) #If the game path is valid, we are no longer selecting
            if select:
                mb.showerror("Invalid directory", "Could not find the word list and pop definitions here.")
            else:
                self.game_path = response + os.sep #We got a new valid directory
        
        #First, the wordlist
        f=open(self.game_path+WORDLIST_FILE)
        wordlist=f.read()
        f.close()
        self.words=self.unpack_wordlist(wordlist)
        self.update_query()

        #Then, the popdefs
        f=open(self.game_path+POPDEFS_FILE, encoding=POPDEFS_ENC)
        data=f.read().strip().splitlines()
        f.close()

        self.defs = {l.split("\t")[0].lower() : l.split("\t")[1] for l in data}

    def del_orphaned_defs(self):
        """Find and delete any orphaned definitions"""
        orphaned = [word for word in self.defs.keys() if word not in self.words]
        if not orphaned:
            mb.showinfo("No orphaned definitions", "All recorded definitions have a word they are paired with.")
            return
        for o in orphaned:
            del self.defs[o]
        if mb.askyesno("Orphaned definitions deleted", "Found and deleted %i orphaned definitions. Save now?" % len(orphaned)):
            self.save_files()

    def save_files(self, *args, backup=False):
        """Save the worldist and popdefs"""
        #Backup system
        if backup:
            try:
                shutil.copy(self.game_path+WORDLIST_FILE, GAME_PATH+WORDLIST_FILE+BACKUP_SUFFIX)
                shutil.copy(self.game_path+POPDEFS_FILE, GAME_PATH+POPDEFS_FILE+BACKUP_SUFFIX)
            except FileNotFoundError:
                mb.showerror("Backup failed", "Could not back up the original files because they have disappeared.")

        #First, the wordlist
        f=open(self.game_path+WORDLIST_FILE, "w")
        f.write(self.pack_wordlist(self.words))
        f.close()

        #Then, the popdefs
        f=open(self.game_path+POPDEFS_FILE, "w", encoding=POPDEFS_ENC)
        for word in self.defs.keys():
            f.write(word.upper()+"\t"+self.defs[word]+"\n")
        f.close()

Editor()
