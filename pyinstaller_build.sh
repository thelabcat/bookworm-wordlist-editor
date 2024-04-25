echo "Updating the English word frequency list"
curl https://raw.githubusercontent.com/rspeer/wordfreq/master/wordfreq/data/large_en.msgpack.gz -o large_en.msgpack.gz
echo "Building exe"
pyinstaller -F --icon=bookworm_wordlist_editor.ico --add-data bookworm_wordlist_editor.png:. --add-data large_en.msgpack.gz:wordfreq/data/ bookworm_wordlist_editor.pyw
echo "Cleaning up exe build residue"
rm -rf build
rm bookworm_wordlist_editor.spec
