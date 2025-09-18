#!/usr/bin/env python3
"""BookWorm Deluxe Wordlist Editor configuration I/O

Loads and saves the configuration for the aforementioned.

S.D.G."""

import os
import os.path as op
from pathlib import Path
import yaml
import bookworm_utils as bw

# The text encoding of the config file
CONFIG_ENC = "utf-8"


# The location of the config file
CONFIG_FILE = Path("~", ".bookworm_wordlist_editor", "config.yaml").expanduser()

# Default values for the config
CONFIG_DEFAULTS = {
    "gamePath": str(bw.GAME_PATH_OS_DEFAULT)
    }


def choose_best_game_path(suggestion: Path | str) -> Path:
    """Decide which is better: The suggested path, or the default

    Args:
        suggestion (Path | str): The path to try and use.

    Returns:
        best (Path): Our decision."""

    suggestion = Path(suggestion)

    # Allow system environment variable to override normal default for game path
    msg_part = f"Config set the game path default to {suggestion}"

    # The environment variable points to a nonexistent path
    if not suggestion.exists():
        print(msg_part, "but it does not exist.")
        return bw.GAME_PATH_OS_DEFAULT

    # The environment variable points to a real path, but not a valid game path
    if not bw.is_game_path_valid(suggestion):
        # The default game path is valid
        if bw.is_game_path_valid(bw.GAME_PATH_OS_DEFAULT):
            print(
                msg_part,
                f"but it is not valid while {bw.GAME_PATH_OS_DEFAULT} is.",
                )
            return bw.GAME_PATH_OS_DEFAULT

        # The default game path isn't any better than the one provided
        print(
            msg_part +
            "which is not a valid game path, but it's the best we know."
            )
        return suggestion

    # The environment variable was set validly
    print(msg_part)
    return suggestion


def load_config():
    """Load the config for the editor, or return blank new config"""
    if not CONFIG_FILE.exists():
        return CONFIG_DEFAULTS

    with open(CONFIG_FILE, encoding=CONFIG_ENC) as f:
        config = yaml.safe_load(f.read())

    # Avoid loading the game path as a Path object
    # Also, choose the best between it and the default
    config["gamePath"] = str(choose_best_game_path(config["gamePath"]))

    return config


def save_config(config):
    """Save the config for the editor"""

    # Ensure the config folder exists
    os.makedirs(op.dirname(CONFIG_FILE), exist_ok=True)

    # Actually write the configuration file
    with open(CONFIG_FILE, "w", encoding=CONFIG_ENC) as f:
        f.write(yaml.dump(config))
