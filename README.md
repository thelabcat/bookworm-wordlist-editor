# Bookworm Deluxe wordlist (and popdefs) editor

This program edits the wordlist and popup definitions for the game [Bookworm Deluxe by PopCap Games](https://oldgamesdownload.com/bookworm-deluxe/) released in 2006. I created this program after augmenting the wordlist more manually using [this free list of English words by dwyl](https://github.com/dwyl/english-words), but then discovering that it contained some errors, along with real words that I felt deserved a popdef.

## Dependencies:
This program relies on the following non-native Python libraries, which can be installed using Pip:
- [PyDictionary](https://pypi.org/project/PyDictionary/)
- [wordfreq](https://pypi.org/project/wordfreq/)

## Usage:
To run from source, install Python 3.x, and then the dependencies, then use Python to run the .pyw program.
You can find executables with bundled Python and the dependencies in the Releases page of this repository.

1. When the program opens, it will default to opening the Bookworm Deluxe folder in the expected system location per your platform. If on Linux or MacOS, it will assume the default wine prefix. If it does not find the wordlist.txt and popdefs.txt files in this default location or the default location doesn't exist, it will ask you to choose the Bookworm Deluxe folder manually. The program will freeze momentarily as it unpacks the word and popdef lists. You should then see a list of words in the left pane.
2. Select a word to see its usage frequency according to wordfreq, and its current popdef (blank for no popdef). If the usage frequency is below an arbitrary value where I think it might need a popdef, it will show in red. Otherwise, it will show in black. While a word is selected you can:
    - Edit the popdef and save it. Note that if you select a different word before saving the definition, it will reset.
    - Reset the popdef to what it was the last time you saved it.
    - Auto-create a popdef using PyDictionary (requires an internet connection).
    - Delete the word from the wordlist.
3. You can search for a word with the search box, using the X button to clear the search query.
4. You can add a new word to the wordlist with the New button. Once added, it will become selected.
5. You must save all your changes before closing the program using File -> Save or the Ctrl+S hotkey.
6. You can revert all changes using File -> Reload.
7. You can open a different wordlist.txt and popdefs.txt pair using File -> Open or the Ctrl+O hotkey.

Hope this helps! S.D.G.
