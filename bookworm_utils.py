# !/usr/bin/env python3
"""BookWorm Utilities

Tools for loading, editing, and saving the wordlist of BookWorm Deluxe


The rules for unpacking the dictionary are simple:

    1. Read the number at the start of the line, and copy that many characters
    from the beginning of the previous word. (If there is no number, copy as
    many characters as you did last time.)

    2. Append the following letters to the word.

As for the popdefs format, each line is: "WORD\t(part of speech abbreviation)
definiton; another definition"

This file is part of BookWorm Deluxe Wordlist Editor.

BookWorm Deluxe Wordlist Editor is free software: you can redistribute it
and/or modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

BookWorm Deluxe Wordlist Editor is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
License for more details.

You should have received a copy of the GNU General Public License along with
BookWorm Deluxe Wordlist Editor. If not, see <https://www.gnu.org/licenses/>.

S.D.G.
"""

import bisect
import glob
import getpass
import platform
import warnings
import nltk
from nltk.corpus import wordnet
from wordfreq import zipf_frequency

# Language and charset information
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
NUMERIC = "1234567890"
try:
    WORD_TYPES = {  # Word types that NLTK wordnet may return, and their abbreviations
        wordnet.NOUN: "n.",
        wordnet.VERB: "v.",
        wordnet.ADJ: "adj.",
        wordnet.ADV: "adv.",
        # "Interjection": "int.",
        # "Preposition": "prep.",
        # "Conjugation": "conj."
            }
    HAVE_WORDNET = True

except LookupError:
    warnings.warn("NLTK corpus wordnet load failed with LookupError.")
    print("Auto definition will not be available.")
    WORD_TYPES = None
    HAVE_WORDNET = False

LANG = "en"  # Language to use when checking word rarity
RARE_THRESH = 3.5  # Words with usage less than this should probably get definitions

# BookWorm Deluxe's internal word length delimiters'
WORD_LENGTH_MIN = 3
WORD_LENGTH_MAX = 12

# File paths and related info
SYS_USER = getpass.getuser()

# Get the default game path based on the OS
GAME_PATH_DEFAULT = {
    "Linux": f"/home/{SYS_USER}/.wine/drive_c/Program Files/PopCap Games/BookWorm Deluxe/",
    "Darwin": f"/Users/{SYS_USER}/.wine/drive_c/Program Files/PopCap Games/BookWorm Deluxe/",
    "Windows": "C:\\Program Files\\PopCap Games\\BookWorm Deluxe\\"
    }[platform.system()]

WORDLIST_FILE = "wordlist.txt"
POPDEFS_FILE = "popdefs.txt"

# Encoding to use when opening the wordlist and popdefs files
WORDLIST_ENC = "utf-8"
POPDEFS_ENC = "iso 8859-15"

# Make sure we have the NLTK corpus wordnet for our English dictionary
nltk.download("wordnet")


def unpack_wordlist(wordlist: str) -> list:
    """Unpack the game's wordlist syntax

    Args:
        wordlist (str): The contents of wordlist.txt

    Returns:
        words (list): The parsed word list"""

    words = []
    copy = 0  # Number of characters to copy from previous word
    for listing in wordlist.strip().splitlines():
        # Skip any blank listings
        if not listing:
            continue

        # Parse any numbers at the beginning of the listing as the copy count
        for i, char in enumerate(listing):
            if char not in NUMERIC:
                break  # i is now the index of the first letter in the listing

        copystr = listing[:i]  # set copystr to a string of any numbers at the beginning of the listing

        if copystr:  # If there a new copy count, don't reuse the last one
            copy = int(copystr)

        if words:  # Copy from the last word, and add the letters from the listing
            words.append(words[-1][:copy] + listing[i:])

        elif not copy:  # Do not copy from the last word, but trim off a zero copy count
            words.append(listing[i:])

        else:
            raise ValueError("Copy count is {copy} at the first word but there are no words yet.")

    return words


def pack_wordlist(words: list[str]) -> str:
    """Pack to the game's wordlist syntax

    Args:
        words (list[str]): A list of words

    Returns:
        wordlist (str): The contents of a new wordlist.txt"""

    listings = []
    oldcopy = 0  # The previous number of letters copied from the word(s) before the current word
    for i, new_word in enumerate(words):
        if i == 0:  # The first word cannot possibly copy anything, and should be listed whole
            listings.append(new_word)
            old_word = new_word
            continue

        # Compare the new word with the old one, one letter at a time,
        # only going to the end of the shortest of the two words
        for copy, letters in enumerate(zip(old_word, new_word)):
            if letters[0] != letters[1]:  # Compare the two letters at the same position from each word
                # copy is now set to the index of the first letter the new word does not have in common with the old one
                break

        # Only include the copy count in the listing if it is different from the old copy count
        # Only include the differing letters of the new word
        listings.append(str(copy) * (copy != oldcopy) + new_word[copy:])
        oldcopy = copy
        old_word = new_word

    return "\n".join(listings).strip()


def unpack_popdefs(popdefs: str) -> dict[str, str]:
    """Unpack the game's popdefs syntax to a dictionary

    Args:
        popdefs (str): The contents of popdefs.txt

    Returns:
        definitions (dict[str, str]): The parsed popup definitions"""

    # Split all non-blank lines at a tab, into the lowercase word and its definition
    return {l.split("\t")[0].lower() : l.split("\t")[1] for l in popdefs.strip().splitlines() if l}


def pack_popdefs(defs: dict[str, str]) -> str:
    """Pack a dictionary into the game's popdefs syntax

    Args:
        defs (dict[str, str]): Dictionary of word: meaning pairs.

    Returns:
        popdefs (str): The contents of a new popdefs.txt"""

    return "\n".join([word.upper() + "\t" + definition for word, definition in defs.items()])


def build_auto_def(word: str) -> str | None:
    """Construct a definition line for a word automatically

    Args:
        word (str): The word to define

    Returns:
        result (str): Either a definition for the game to use,
            or an error message upon faliure.
        success (bool): Wether or not we succeeded."""

    if not HAVE_WORDNET:
        return "We need to download NLTK wordnet for this. " +\
            "Please connect to the internet, then restart the application.", \
            False

    try:
        synsets = wordnet.synsets(word)
    except LookupError:
        return "LookupError raised. " +\
            "The NLTK wordnet package is missing.", \
            False

    if not synsets:
        return f"No definition found for '{word}'", False

    # Group definitions together by word type
    pos_groups = {}
    for ss in synsets:
        if (pos := ss.pos()) not in pos_groups:
            pos_groups[pos] = [ss.definition()]
        else:
            pos_groups[pos].append(ss.definition())

    return "; ".join(  # type groups are split by semicolon
        f"({WORD_TYPES[pos]}) " +  # Each type group starts with the type

        # Definitions within a group are also split by semicolon
        # Each definition should also be capitalized
        "; ".join((d.capitalize() for d in definitions))

        # Iterate through type groups with the definitions in them
        for pos, definitions in pos_groups.items()
        # The last definition needs a period.
        ) + ".", \
        True  # Report success


def is_game_path_valid(path: str) -> bool:
    """Check if the wordlist and popdefs files exist at the given path

    Args:
        path (str): A complete path to a folder, allegedly the game's.

    Returns:
        valid (bool): If we found the two files."""

    dircheck = glob.glob(path + "*")
    return (path + WORDLIST_FILE in dircheck and path + POPDEFS_FILE in dircheck)


def get_word_usage(word: str) -> float:
    """Get how often a word is used.

    Args:
        word (str): The word to check.

    Returns:
        usage (float): A number ranging from 0 to 8.
            0 means we had no usage listed.
            1 is the minimum registered usage."""

    return zipf_frequency(word, LANG)


def binary_search(elements, value):
    """A binary search implementation from W3Schools

    Args:
        elements (iter): The sorted iterable to search through
        value (object): The value to get the index of

    Returns:
        result (int|None): The index, or NoneType if not found
    """

    index = bisect.bisect_left(elements, value)
    if index < len(elements) and elements[index] == value:
        return index
