# FallenAces Plugin for Sublime Text

A Sublime Text plugin that enhances scripting for **Fallen Aces** development.  

Provides:

- Hover hints for functions, events, and tags
- Context-aware completions based on level metadata
- Syntax highlighting

## Requirements

- Sublime Text (https://www.sublimetext.com/)

## Installation

1. Clone this repo or download as ZIP.
2. Copy `fallen_aces_*` and `fallen-aces.*` files into your Sublime `Packages/User` directory.

## Usage
- Open chapter folder (the one with `chapterInfo.txt` in it) in Sublime Text.
- Save as Sublime Project (`Project > Save Project As ...`) in chapter folder. `*.sublime-project` file should be created.
- Open script file.
- Select syntax (`View > Syntax > Fallen Aces Script`)
- Start typing function names to see function completions.
- Hover on functions to see function description (*Note: current support is very limited*)
- Start typing event or tag names as arguments in corresponding functions to see arg completions. (*Note: current support is not fully completed*)
- Hover on event/tag identifiers to see text name.

## Trouble shooting
- Enable `fallen_aces_plugin_debug_enabled` setting in `*.sublime-project file`:
```
{
	"folders":
	[
		...
	],

	"settings": {
		"fallen_aces_plugin_debug_enabled": true
	}
}

```
- Open console (`'Ctrl' + '`'`)


