# Sublime Text Plugin for Fallen Aces Scripting

A plugin for Fallen Aces script files. It provides completions and hover hints by parsing level metadata.

## Features

- **Syntax Highlighting**: Dedicated highlighting for Fallen Aces script files.
- **Context-aware Completions**: Autocompletions for:
  - Built-in Fallen Aces editor functions.
  - Level-specific **Events** and **Tags**.
- **Hover Hints**: Documentation and metadata on hover for:
  - Function signatures, descriptions, and usage examples.
  - Event and Tag resolutions showing their names directly in the tooltip.
- **Snippet Support**: Built-in shortcuts for common code snippets.

## Installation

### Upgrading from Previous Versions
If you previously installed this plugin by copying files directly into your `Packages/User` folder, you **must** remove them to avoid conflicts:
1. Go to **Preferences > Browse Packages...**
2. Open the `User` folder.
3. Delete any old `fallen_aces.py` or `fallen-aces-*` files.

### Manual Installation
1. Open your Sublime Text `Packages` directory (**Preferences > Browse Packages...**).
2. Create a folder named `FallenAces`.
3. Copy the entire contents of this repository into that folder, ensuring the following structure is maintained:
   ```text
   FallenAces/
   ├── fa_core/
   ├── fa_parser/
   ├── fa_utils/
   ├── fallen_aces.py
   ├── fallen-aces-data.json
   ├── fallen-aces.sublime-syntax
   └── fallen-aces.tmPreferences
   ```

## Usage

### 1. Project Setup
For the plugin to resolve level-specific tags and events:
1. Open your chapter folder (the one containing `chapterInfo.txt`) in Sublime Text.
2. Save it as a project: **Project > Save Project As...** inside the chapter folder.
3. The plugin will automatically find and parse the `world_file_name` specified in your `chapterInfo.txt` and keep data in sync as you save changes.

### 2. Syntax Selection
- Open a script file (`.txt`).
- Set the syntax to **Fallen Aces Script** (via the status bar or **View > Syntax > Fallen Aces Script**).

### 3. Automatic Syntax Application
You can enable automatic syntax detection for `.txt` files located inside `scripts` folders by adding this to your `*.sublime-project` file:

```json
{
    "settings": {
        "fallen_aces_auto_syntax_enabled": true
    }
}
```

### 4. Debugging
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
- **Sublime Text** ([https://www.sublimetext.com/](https://www.sublimetext.com/))
- Python 3.3+ (Built-in to Sublime Text)

## Testing
The project includes a comprehensive test suite. To run tests locally:
```bash
python -m unittest discover tests
```
