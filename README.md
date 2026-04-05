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
- **Phantom Hints**: Inline visual hints for numeric identifiers (tags and events), showing their names directly in the editor next to the ID.
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
Plugin works only wiht `.txt` files that use **Fallen Aces Script** syntax.

To select syntax manually open a script file (`.txt`) and set the syntax to **Fallen Aces Script** via the status bar or **View > Syntax > Fallen Aces Script**.

To automatically apply **Fallen Aces Script** syntax to every `.txt` file in Scripts folder, open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) and run **Fallen Aces: Toggle Auto Syntax Application** command. This command will also update your project-level settings (`*.sublime-project`):
```json
{
    "settings": {
        "fallen_aces_auto_syntax_enabled": true
    }
}
```

To disable this feature, run the same command again, or change the setting manually in `*sublime-project` file.

### 3. Debugging
If you encounter issues, you can enable debug logging by using the **Fallen Aces: Toggle Debug Logging** command or by adding this to your `*.sublime-project` file:

```json
{
    "settings": {
        "fallen_aces_plugin_debug_enabled": true
    }
}
```
Logs will appear in the Sublime Text console (``Ctrl + ` ``).

### 4. Settings & Commands
The plugin provides several commands accessible via the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`) to toggle project-level settings. These commands automatically update your `*.sublime-project` file:

- **Fallen Aces: Toggle Phantom Hints**: Enable/disable inline visual hints for tags and events.
- **Fallen Aces: Toggle Auto Syntax Application**: Enable/disable automatic syntax detection for `.txt` files in `scripts` folders.
- **Fallen Aces: Toggle Debug Logging**: Enable/disable debug logging in the Sublime Text console.

## Requirements
- **Sublime Text** ([https://www.sublimetext.com/](https://www.sublimetext.com/))
- Python 3.3+ (Built-in to Sublime Text)

## Testing
The project includes a comprehensive test suite. To run tests locally:
```bash
python -m unittest discover tests
```
