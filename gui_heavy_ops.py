#!/ur/bin/env python3
"""BookWorm WordList Editor GUI heavy operations

Functions to be run via the main window's tread_process() method.

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
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox as mb
import bookworm_utils as bw
import info


def __load_alpha_file(self: tk.Tk):
    """Select a text file containing a human-readable list of words,
        read it, close it, and filter the result to alpha-only words.

    Args:
        self (tk.Tk): The main GUI.

    Returns:
        words (list): The list of alpha-only words from the file.
            Returns empty list if cancelled."""

    # Have the user select the file
    f = filedialog.askopenfile(
        title="Select human-readable list of words",
        filetypes=bw.TEXT_FILETYPE,
    )

    # The user cancelled via the open file dialog
    if not f:
        return []

    # Read and close the file, splitting into words by whitespace
    self.busy_text = "Reading file..."
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


def load_files(self: tk.Tk, select: bool = True, do_or_die: bool = False):
    """Load the wordlist and the popdefs

    Args:
        self (tk.Tk): The main GUI.
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


def save_files(self: tk.Tk, backup: bool = False):
    """Attempt to save the worldist and popdefs.
        Reference self.unsaved_changes to know the result.

    Args:
        self (tk.Tk): The main GUI.
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

    # First, encode the wordlist
    self.busy_text = f"Encoding {bw.WORDLIST_FILE}..."

    # Ensure that the wordlist encodes properly
    # Technically, this should never fail because a word should always be alpha
    try:
        encoded_wordlist = bw.pack_wordlist(sorted(self.words))\
            .encode(bw.WORDLIST_ENC)
    except UnicodeEncodeError:
        # Failure to encode stops us from even trying to open the file
        mb.showerror(
            "File encoding error",
            "One or more word entries contain characters that couldn't" +
            f"be encoded in {bw.WORDLIST_ENC}."
            )
        return

    # Then, encode the popdefs
    self.busy_text = f"Encoding {bw.POPDEFS_FILE}..."

    # Ensure that the popdefs encodes properly
    try:
        encoded_popdefs = bw.pack_popdefs(dict(sorted(self.defs.items())))\
            .encode(bw.POPDEFS_ENC)
    except UnicodeEncodeError:
        # Failure to encode stops us from even trying to open the file
        mb.showerror(
            "File encoding error",
            "One or more definition entries contain characters that couldn't" +
            f"be encoded in {bw.POPDEFS_ENC}."
            )
        return

    self.busy_text = "Writing to disk..."
    with open(self.wordlist_abs_path, "wb") as f:
        f.write(encoded_wordlist)
    with open(self.popdefs_abs_path, "wb") as f:
        f.write(encoded_popdefs)

    self.unsaved_changes = False  # All changes are now saved


def mass_add_words(self: tk.Tk):
    """Add a whole file's worth of words

    Args:
        self (tk.Tk): The main GUI."""

    alpha_words = __load_alpha_file(self)
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
    self.mass_unsaved_changes(
        "Words added",
        f"Added {len(new_lenvalid_words):,} new words to the word list."
    )


def mass_delete_words(self: tk.Tk):
    """Delete a whole file's worth of words

    Args:
        self (tk.Tk): The main GUI."""

    # Get the list of words to delete
    del_words = __load_alpha_file(self)
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
        self._delete_word(word)

    # Words that were in the query may have been deleted, so update it.
    self.update_query()

    # There are now major unsaved changes
    self.mass_unsaved_changes(
        "Words deleted",
        f"Removed {len(old_words):,} words from the word list.",
    )


def del_invalid_len_words(self: tk.Tk):
    """Remove all words of invalid length from the wordlist

    Args:
        self (tk.Tk): The main GUI."""

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
        self._delete_word(word)

    # Update the query display
    self.update_query()

    # There are now mass unsaved changes
    self.mass_unsaved_changes(
        "Invalid length words deleted",
        f"Found and deleted {len(invalid):,} words of invalid length " +
        "from the word list."
    )


def del_orphaned_defs(self: tk.Tk):
    """Find and delete any orphaned definitions

    Args:
        self (tk.Tk): The main GUI."""

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
    self.mass_unsaved_changes(
        "Orphaned definitions deleted",
        f"Found and deleted {len(orphaned):,} orphaned definitions.",
    )


def del_dupe_words(self: tk.Tk):
    """Delete any duplicate word listings

    Args:
        self (tk.Tk): The main GUI."""

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
    self.mass_unsaved_changes(
        "Duplicates deleted",
        f"Found and removed {dupe_count:,} duplicate listings",
    )


def mass_auto_define(self: tk.Tk):
    """Find all words below the usage threshold, and try to define them

    Args:
        self (tk.Tk): The main GUI."""

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
    self.mass_unsaved_changes(
        "Operation complete",
        f"Auto-defined {total - fails:,} words.",
    )
