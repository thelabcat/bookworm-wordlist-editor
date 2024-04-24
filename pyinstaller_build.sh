pyinstaller -F --icon=bookworm_wordlist_editor.ico --add-data bookworm_wordlist_editor.png:. bookworm_wordlist_editor.pyw
rm -rf build
rm bookworm_wordlist_editor.spec
