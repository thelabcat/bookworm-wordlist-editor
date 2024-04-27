# BookWorm Deluxe wordlist (and popdefs) editor

![Screenshot](https://i.imgur.com/lbd3wFy.png "The main app window")

This program edits the wordlist and popup definitions for the game [BookWorm Deluxe by PopCap Games](https://oldgamesdownload.com/bookworm-deluxe/) released in 2006. I created this program after augmenting the wordlist more manually using [this free list of English words by dwyl](https://github.com/dwyl/english-words), but then discovering that it contained some errors, along with real words that I felt deserved a popdef.

## Dependencies:
This program relies on the following non-native Python libraries, which can be installed using Pip:
- [PyDictionary](https://pypi.org/project/PyDictionary/)
- [wordfreq](https://pypi.org/project/wordfreq/)

You can find executables with bundled Python and the dependencies in the Releases page of this repository.

## Usage:
To run from source, install Python 3.x, and then the dependencies, then use Python to run the .pyw program.

### Program operation:
- When the program opens, it will default to opening the BookWorm Deluxe folder in the expected system location per your platform. If on Linux or MacOS, it will assume the default wine prefix. If it does not find the wordlist.txt and popdefs.txt files in this default location or the default location doesn't exist, it will ask you to choose the BookWorm Deluxe folder manually. After it loads, you should see a list of words in the left pane.
- Select a word to see its usage frequency according to wordfreq, and its current popdef (blank for no popdef). If the usage frequency is below an arbitrary value where I think it might need a popdef, it will show in red. Otherwise, it will show in black. While a word is selected you can:
    - Edit the popdef and save it. Note that if you select a different word before saving the definition, it will reset.
    - Reset the popdef to what it was the last time you saved it.
    - Auto-create a popdef using PyDictionary (requires an internet connection).
    - Delete the word from the wordlist.
- You can search for a word with the search box, using the X button to clear the search query.
- You can add a new word to the wordlist with the New button. Once added, it will become selected.
- The File menu provides the following operations:
    - Open (Ctrl + O): Open a different word list and popdefs file pair.
    - Reload: Reload the current word list and popdefs file pair, reversing all your changes.
    - Save (Ctrl + S): Save your changes.
- The Edit menu provides the following operations:
    - Delete orphaned definitions: Removes definitions from the popdefs that do not have a word in the wordlist.
    - Delete words of invalid length: Removes words that BookWorm Deluxe will not allow as moves because of their length.
    - Add several words: Select a text file of new words and add them all.
    - Delete several words: Select a text file of words and delete them all.

## Information on antivirus false positives for PyInstaller executables

Recently, I discovered that multiple antivirus services are consistently flagging any and all Windows executables packaged with PyInstaller. This is a mistake: While malware could certainly be written in Python and subsequently packaged with PyInstaller into an exe, the exe would be malicious because of the packaged Python code, not because of PyInstaller. I've reported the problem to the antivirus services that I found false positive reporting forms for, but only the specific app version was whitelisted, if anything at all, in most cases. I tested BookWorm Deluxe Wordlist Editor v1.5.0 win x64 on April 27 in VirusTotal: It showed no malicious behavior from the application inside sandbox tests, and provided the following list of flags from security vendors. If you receive a different report than this, or you know of a permanent solution, please let me know, as this has been an ongoing problem.


<table>
    <tr>
        <th>Antivirus service</th>
        <th>Report for this PyInstaller EXE</th>
    </tr>
    <tr>
        <td>Bkav Pro</td>
        <td>W64.AIDetectMalware</td>
    </tr>
    <tr>
        <td>Elastic</td>
        <td>Malicious (moderate Confidence)</td>
    </tr>
    <tr>
        <td>Jiangmin</td>
        <td>TrojanSpy.Agent.afwu</td>
    </tr>
    <tr>
        <td>Malwarebytes</td>
        <td>Malware.AI.3767809634</td>
    </tr>
    <tr>
        <td>SecureAge</td>
        <td>Malicious</td>
    </tr>
    <tr>
        <td>Skyhigh (SWG)</td>
        <td>BehavesLike.Win64.Agent.tc</td>
    </tr>
</table>

Hope this helps! S.D.G.
