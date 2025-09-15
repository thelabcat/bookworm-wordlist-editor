# !/usr/bin/env python3
"""BookWorm Utilities

Tools for loading, editing, and saving the wordlist and popdefs of
BookWorm Deluxe.


The rules for unpacking the dictionary are simple:

    1. Read the number at the start of the line, and copy that many characters
    from the beginning of the previous word. (If there is no number, copy as
    many characters as you did last time.)

    2. Append the following letters to the word.

As for the popdefs format, each line is: "WORD\t(part of speech abbreviation)
definiton; another definition"

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

S.D.G.
"""

import bisect
import getpass
import os
import os.path as op
from pathlib import Path
import platform
import re
import warnings
import nltk
from nltk.corpus import wordnet
from wordfreq import zipf_frequency

# Language and charset information
ALPHABET = "abcdefghijklmnopqrstuvwxyz"
NUMERIC = "1234567890"

# RegEx pattern to match one or more of any whitespace character
WHITESPACE_PATTERN = re.compile(r"\s+")

# Make sure we have the NLTK wordnet for our English dictionary
# Note: Without internet, nltk.download will quietly fail and return False.
# With internet, it will return True even if we already had wordnet.
nltk.download("wordnet")
try:
    # Word part-of-speech's that NLTK wordnet may return, and their
    # abbreviations to use for in-game definitions.
    WORD_POS = {
        wordnet.NOUN: "n.",
        wordnet.VERB: "v.",
        wordnet.ADJ: "adj.",
        wordnet.ADJ_SAT: "adj.",
        wordnet.ADV: "adv.",
        # "Interjection": "int.",
        # "Preposition": "prep.",
        # "Conjugation": "conj."
    }
    HAVE_WORDNET = True

# Referencing word part-of-speech's in wordnet when we don't have wordnet
# raises a LookupError.
except LookupError:
    warnings.warn("NLTK wordnet load failed with LookupError.")
    print("Auto definition will not be available.")
    WORD_POS = None
    HAVE_WORDNET = False

LANG = "en"  # Language to use when checking word rarity

# Words with usage less than this should probably get definitions
RARE_THRESH = 3.5

# BookWorm Deluxe's internal word length delimiters
WORD_LENGTH_MIN = 3
WORD_LENGTH_MAX = 12

# File paths and related info
SYS_USER = getpass.getuser()

# Default game path inside C drive
GAME_PATH_C = Path("Program Files", "PopCap Games", "BookWorm Deluxe")

# Default game path inside a *NIX all-users directory (to default Wine prefix)
GAME_PATH_NIX_USERS = Path(SYS_USER, ".wine", "drive_c").joinpath(GAME_PATH_C)

# Default game path based on the OS
GAME_PATH_OS_DEFAULT = {
    "Linux": Path("/home").joinpath(GAME_PATH_NIX_USERS),
    "Darwin": Path("/Users").joinpath(GAME_PATH_NIX_USERS),
    "Windows": Path("C:").joinpath(GAME_PATH_C),
}[platform.system()]

# Tkinter file dialog types filter for plain text files
TEXT_FILETYPE = [("Plain text", ".txt")]

# Names of the two game files we can edit
WORDLIST_FILE = "wordlist.txt"
POPDEFS_FILE = "popdefs.txt"


def is_game_path_valid(path: str) -> bool:
    """Check if the wordlist and popdefs files exist at the given path

    Args:
        path (str): A complete path to a folder, allegedly the game's.

    Returns:
        valid (bool): If we found the two files."""

    return op.exists(op.join(path, WORDLIST_FILE)) and op.exists(
        op.join(path, POPDEFS_FILE)
    )


# Allow system environment variable to override normal default for game path
ENV_GAME_PATH = os.environ.get("BOOKWORM_GAME_PATH")
if ENV_GAME_PATH:
    ENV_GAME_PATH_MSG = f"System set the game path default to {ENV_GAME_PATH}"

    # The environment variable points to a nonexistent path
    if not op.exists(ENV_GAME_PATH):
        print(ENV_GAME_PATH_MSG, "but it does not exist.")
        GAME_PATH_DEFAULT = GAME_PATH_OS_DEFAULT

    # The environment variable points to a real path, but not a valid game path
    elif not is_game_path_valid(ENV_GAME_PATH):
        # The default game path is valid
        if is_game_path_valid(GAME_PATH_OS_DEFAULT):
            print(
                ENV_GAME_PATH_MSG,
                f"but it is not valid while {GAME_PATH_OS_DEFAULT} is.",
                )
            GAME_PATH_DEFAULT = GAME_PATH_OS_DEFAULT

        # The default game path isn't any better than the one provided
        else:
            print(
                ENV_GAME_PATH_MSG +
                "which is not a valid game path, but it's the best we know."
                )
            GAME_PATH_DEFAULT = ENV_GAME_PATH

    # The environment variable was set validly
    else:
        print(ENV_GAME_PATH_MSG)
        GAME_PATH_DEFAULT = ENV_GAME_PATH

# The environment variable was not set
else:
    GAME_PATH_DEFAULT = GAME_PATH_OS_DEFAULT

# Encoding to use when opening the wordlist and popdefs files
WORDLIST_ENC = "utf-8"
POPDEFS_ENC = "iso 8859-15"


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
        i = 0  # Ensure the variable exists.
        for i, char in enumerate(listing):
            if char not in NUMERIC:
                break  # i is now the index of the first letter in the listing

        # Set copystr to any digits at the beginning of the listing
        copystr = listing[:i]

        if copystr:  # If there is a new copy count, don't reuse the last one
            copy = int(copystr)

        # Copy from the last word, and add the letters from the listing?
        if words:
            words.append(words[-1][:copy] + listing[i:])

        # Do not copy from the last word, but trim off a zero copy count?
        elif not copy:
            words.append(listing[i:])

        else:
            raise ValueError(
                "Copy count is {copy} at the first word: Nothing to copy from."
            )

    return words


def pack_wordlist(words: list[str]) -> str:
    """Pack to the game's wordlist syntax

    Args:
        words (list[str]): A list of words

    Returns:
        wordlist (str): The contents of a new wordlist.txt"""

    # Each packed word listing in the new file
    listings = []

    # The number of letters copied to the word before the current one
    oldcopy = 0

    for i, new_word in enumerate(words):
        # The first word cannot possibly copy anything: Should be listed whole
        if i == 0:
            listings.append(new_word)
            old_word = new_word
            continue

        # Compare the new word with the old one, one letter at a time,
        # only going to the end of the shortest of the two words
        copy = 0  # Ensure the variable exists.
        for copy, letters in enumerate(zip(old_word, new_word)):
            # Compare the two letters at the same position from each word
            if letters[0] != letters[1]:
                # copy is now set to the index of the first letter that the
                # new word does not have in common with the old one
                break

        # Only include the copy count in the listing if it has changed,
        # and only include the differing letters of the new word.
        listings.append(str(copy) * (copy != oldcopy) + new_word[copy:])
        oldcopy = copy
        old_word = new_word

    return "\n".join(listings).strip()


def unpack_popdefs(popdefs: str) -> dict[str, str]:
    """Unpack the game's popdefs syntax to a dictionary

    Args:
        popdefs (str): The contents of popdefs.txt

    Returns:
        definitions (dict[str, str]): The parsed popup definitions."""

    # Split all non-blank lines at a tab, into the word and its definition.
    # The popdefs list capitalizes words, so lowercase them.
    return {
        line.split("\t")[0].lower(): line.split("\t")[1]
        for line in popdefs.strip().splitlines()
        if line
    }


def pack_popdefs(defs: dict[str, str]) -> str:
    """Pack a dictionary into the game's popdefs syntax

    Args:
        defs (dict[str, str]): Dictionary of word: meaning pairs.

    Returns:
        popdefs (str): The contents of a new popdefs.txt"""

    return "\n".join(
        [
            word.upper() + "\t" + definition
            for word, definition in defs.items()
        ]
    )


def build_auto_def(word: str) -> str | None:
    """Construct a definition line for a word automatically

    Args:
        word (str): The word to define

    Returns:
        result (str): Either a definition for the game to use,
            or an error message upon faliure.
        success (bool): Wether or not we succeeded."""

    if not HAVE_WORDNET:
        return (
            "We need to download NLTK wordnet for this. "
            + "Please connect to the internet, then restart the application.",
            False,
        )

    try:
        synsets = wordnet.synsets(word)
    except LookupError:
        return "LookupError raised. " +\
            "The NLTK wordnet package is missing.", False

    if not synsets:
        return f"No definition found for '{word}'.", False

    # Group definitions together by word part-of-speech
    pos_groups = {}
    for ss in synsets:
        if (pos := ss.pos()) not in pos_groups:
            pos_groups[pos] = [ss.definition()]
        else:
            pos_groups[pos].append(ss.definition())

    return "; ".join(  # type groups are split by semicolon
        f"({WORD_POS[pos]}) "  # Each type group starts with the type
        +
        # Definitions within a group are also split by semicolon
        # Each definition should also be capitalized
        "; ".join((d.capitalize() for d in definitions))
        # Iterate through type groups with the definitions in them
        for pos, definitions in pos_groups.items()
        # The last definition needs a period.
    ) + ".", True  # Report success


def get_word_usage(word: str) -> float:
    """Get how often a word is used.

    Args:
        word (str): The word to check.

    Returns:
        usage (float): A number ranging from 0 to 8.
            0 means we had no usage listed.
            1 is the minimum registered usage."""

    return zipf_frequency(word, LANG)


def binary_search(elements, value) -> int | None:
    """A binary search implementation.
        By Bartosz Zaczyński on <https://realpython.com/>

    Args:
        elements (iter): The sorted iterable to search through
        value (object): The value to get the index of

    Returns:
        result (int|None): The index, or NoneType if not found
    """

    index = bisect.bisect_left(elements, value)
    if index < len(elements) and elements[index] == value:
        return index

    # Lookup failed
    return None


def deepest_valid_path(path: str | Path) -> Path:
    """Find the deepest part of the given path that is valid

    Args:
        path (str | Path): The path to test.

    Returns:
        valid (Path): The closest we could really get to the specified path."""

    path = Path(path).absolute()
    while not path.exists():
        path = path.parent

    return path
