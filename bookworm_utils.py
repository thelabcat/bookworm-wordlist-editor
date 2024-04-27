#!/usr/bin/env python3
"""BookWorm Utilities

Tools for loading, editing, and saving the wordlist of BookWorm Deluxe

S.D.G.
"""

import glob
import getpass
import platform
from PyDictionary import PyDictionary as dic
from wordfreq import zipf_frequency

#Language and charset information
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
NUMERIC = "1234567890"
WORD_TYPES = { #Word types that PyDictionary may return, and their abbreviations
    "Noun":"n.",
    "Verb":"v.",
    "Adjective":"adj.",
    "Adverb":"adv.",
    "Interjection":"int.",
    "Preposition":"prep.",
    "Conjugation":"conj."
        }
LANG = "en" #Language to use when checking word rarity
RARE_THRESH = 3.5 #Words with usage less than this should probably get definitions

#BookWorm Deluxe's internal word length delimiters'
WORD_LENGTH_MIN = 3
WORD_LENGTH_MAX = 12

#File paths and related info
SYS_USER = getpass.getuser()
GAME_PATH_DEFAULT={"Linux" : f"/home/{SYS_USER}/.wine/drive_c/Program Files/PopCap Games/BookWorm Deluxe/",
                   "Darwin" : f"/Users/{SYS_USER}/.wine/drive_c/Program Files/PopCap Games/BookWorm Deluxe/",
                   "Windows" : "C:\\Program Files\\PopCap Games\\BookWorm Deluxe\\"
                   }[platform.system()] #Get the default game path based on the OS
WORDLIST_FILE = "wordlist.txt"
POPDEFS_FILE = "popdefs.txt"

#Encoding to use when opening the wordlist and popdefs files
WORDLIST_ENC = "utf-8"
POPDEFS_ENC = "iso 8859-15"

def unpack_wordlist(wordlist):
    """Given a wordlist as text, unpack into a list of words"""
    words = []
    copy = 0 #Number of characters to copy from previous word
    for listing in wordlist.strip().splitlines():
        #Skip any blank listings
        if not listing:
            continue

        #Parse any numbers at the beginning of the listing as the copy count
        for i, char in enumerate(listing):
            if char not in NUMERIC:
                break #i is now the index of the first letter in the listing

        copyread = listing[:i] #set copyread to a string of any numbers at the beginning of the listing

        if copyread: #If there a new copy count, don't reuse the last one
            copy = int(copyread)

        if words: #Copy from the last word, and add the letters from the listing
            words.append(words[-1][:copy] + listing[i:])

        elif not copy: #Do not copy from the last word, but trim off a zero copy count
            words.append(listing[i:])

        else:
            raise ValueError("Copy count is {copy} at the first word but there are no words yet.")

    return words

def pack_wordlist(words):
    """Given a list of words, pack into a wordlist as text"""
    listings = []
    oldcopy = 0 #The previous number of letters copied from the word(s) before the current word
    for i, new_word in enumerate(words):
        if i == 0: #The first word cannot possibly copy anything, and should be listed whole
            listings.append(new_word)
            old_word = new_word
            continue

        #Compare the new word with the old one, one letter at a time,
        #only going to the end of the shortest of the two words
        for copy, letters in enumerate(zip(old_word, new_word)):
            if letters[0] != letters[1]: #Compare the two letters at the same position from each word
                #copy is now set to the index of the first letter the new word does not have in common with the old one
                break

        #Only include the copy count in the listing if it is different from the old copy count
        #Only include the differing letters of the new word
        listings.append(str(copy) * (copy != oldcopy) + new_word[copy:])
        oldcopy = copy
        old_word = new_word

    return "\n".join(listings).strip()

def unpack_popdefs(popdefs):
    """Given popdefs as text, unpack into a dict of definitions"""
    #Split all non-blank lines at a tab, into the lowercase word and its definition
    return {l.split("\t")[0].lower() : l.split("\t")[1] for l in popdefs.strip().splitlines() if l}

def pack_popdefs(defs):
    """Given a dict of definitions, pack into popdefs as text"""
    return "\n".join([word.upper() + "\t" + definition for word, definition in defs.items()])

def build_auto_def(word):
    """Construct a definition line using PyDictionary, given a word"""
    #Try to get a definition
    def_raw = dic.meaning(word, disable_errors = True)
    if not def_raw:
        print("No definition found for", word)
        return None

    for typ in tuple(def_raw.keys()): #For each word type listed...
        for meaning in def_raw[typ][:]: #For each definition listed in that word type...
            if meaning[0] == "(": #Remove special context defintions
                def_raw[typ].remove(meaning)
        if not def_raw[typ]: #Remove emptied word type definition lists
            del def_raw[typ]

    #If all definitions were for special context, report faliure
    if not def_raw:
        print("No appropriate definition found for", word)
        return None

    #Format the first PyDictionary definition for each word type as a BookWorm Deluxe definition string
    return "; ".join(["(" + WORD_TYPES[typ] + ") " + defs[0].capitalize() for typ, defs in def_raw.items()])

def is_game_path_valid(path):
    """Check if the wordlist and popdefs files exist at the given path"""
    dircheck = glob.glob(path + "*")
    return (path + WORDLIST_FILE in dircheck and path + POPDEFS_FILE in dircheck)

def get_word_usage(word):
    """Given a word, return its average usage"""
    return zipf_frequency(word, LANG)
