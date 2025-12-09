# Sublime Text Plugin for Fallen Aces scripting 

## Features

- **Syntax Highlighting** for Fallen Aces script files (`.txt`)
- **Context-aware completions** based on level metadata
- **Hover hints** for functions, events and tags


## Installation

1. Open your Sublime Text `Packages` directory (**Preferences > Browse Packages...**).
2. Create a folder named `FallenAces`.
3. Copy the following files into that folder:
   - `fallen_aces.py`
   - `fallen-aces-data.json`
   - `fallen-aces.sublime-syntax`
   - `fallen-aces.tmPreferences`

## Usage

### 1. Project Setup
1. Open your chapter folder (the one containing `chapterInfo.txt`) in Sublime Text.
2. Save it as a project: **Project > Save Project As...** inside the chapter folder.
3. The plugin will automatically find and parse the `world_file_name` specified in your `chapterInfo.txt`.

### 2. Syntax Selection
- Open a script file.
- Set the syntax to **Fallen Aces Script** (via the status bar or **View > Syntax**).

### 3. Debugging
If you encounter issues, you can enable debug logging in your `*.sublime-project` file:

```json
{
    "settings": {
        "fallen_aces_plugin_debug_enabled": true
    }
}
```
Logs will appear in the Sublime Text console (``Ctrl + ` ``).

## Requirements
- Sublime Text (https://www.sublimetext.com/)
