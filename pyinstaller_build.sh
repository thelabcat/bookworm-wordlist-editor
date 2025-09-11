# Copyright 2025 Wilbur Jaywright d.b.a. Marswide BGL.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

echo "Preparing venv"
python -m venv .venv

echo "Activating venv"
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # cygwin is POSIX compatibility layer and Linux environment emulation for Windows
    source .venv/bin/activate

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "WARNING: MacOS detected. Have not fully tested on MacOS."
    source .venv/bin/activate

elif [[ "$OSTYPE" == "msys" ]]; then
    # Lightweight shell and GNU utilities compiled for Windows (part of MinGW)
    # Used by Git Bash
    venv\Scripts\activate
elif [[ "$OSTYPE" == "freebsd"* ]]; then
    echo "WARNING: FreeBSD detected but not supported."
else
    echo "Could not detect operating system. Guessing UNIX."
    source .venv/bin/activate
fi

echo "Installing requirements"
pip install -r requirements.txt
pip install -U setuptools pyinstaller

echo "Updating the English word frequency list"
curl https://raw.githubusercontent.com/rspeer/wordfreq/master/wordfreq/data/large_en.msgpack.gz -o large_en.msgpack.gz

echo "Building exe"
pyinstaller -F --icon=bookworm_wordlist_editor.ico --add-data bookworm_wordlist_editor.png:. --add-data large_en.msgpack.gz:wordfreq/data/ bookworm_wordlist_editor.pyw 2>&1 | tee pyinstaller_build_log.txt

echo "Cleaning up exe build residue"
rm -rf build
rm bookworm_wordlist_editor.spec

echo "Deactivating venv"
deactivate
