# JSON Pro

A professional JSON editor for macOS with multi-tab support, tree view navigation, and powerful formatting tools. Built with Python and Tkinter, featuring a modern dark theme interface and native macOS app bundle integration.

## Features

- **Multi-Tab Editing** - Work with multiple JSON files simultaneously in tabs
- **Tree View Navigator** - Browse JSON structure in an expandable tree view
- **Syntax Highlighting** - Color-coded JSON for better readability
- **Format/Pretty Print** - Auto-format JSON with proper indentation
- **Minify** - Compress JSON by removing whitespace
- **Validate** - Check JSON syntax with detailed error messages
- **Dark Theme UI** - Modern, eye-friendly interface with custom color scheme
- **Native macOS App** - Proper .app bundle with dock integration
- **Keyboard Shortcuts** - Fast workflow with command shortcuts

## Installation

1. Create virtual environment:
   ```bash
   python3 -m venv venv314
   source venv314/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install pyobjc-framework-Cocoa
   ```

3. Run the app:
   ```bash
   python3 json_editor_pro.py
   ```

Or simply double-click **JSON Pro.app** to launch.

## Requirements

- macOS 10.15+
- Python 3.14
- Tkinter (included with Python)

## Keyboard Shortcuts

- **Cmd-N** - New tab
- **Cmd-O** - Open JSON file
- **Cmd-S** - Save file
- **Cmd-F** - Format (pretty print)
- **Cmd-M** - Minify JSON
- **Cmd-K** - Validate JSON

## Usage

1. **Open Files** - Click "OPEN" or use Cmd-O to open JSON files
2. **Edit JSON** - Type directly in the editor with syntax highlighting
3. **Format** - Click "FORMAT" or Cmd-F to pretty print your JSON
4. **Validate** - Click "VALIDATE" or Cmd-K to check syntax
5. **Save** - Click "SAVE" or Cmd-S to save changes
6. **Tree View** - Toggle with "TREE" button to navigate JSON structure

## Project Structure

```
json Pro/
├── JSON Pro.app/            # macOS application bundle
├── json_editor_pro.py       # Main application
├── create_json_icon.py      # Icon generation script
├── JSONPro.iconset/         # Application icon resources
├── JSONPro.icns             # macOS icon file
├── json.png                 # Source icon image (1024x1024)
└── README.md                # This file
```

## Features in Detail

### Multi-Tab Interface
Open multiple JSON files in separate tabs. Each tab maintains its own:
- File path
- Edit history
- Unsaved changes indicator

### Tree View Navigation
The collapsible tree view shows your JSON structure:
- Objects and arrays are shown as expandable folders
- Keys and values are displayed inline
- Long values are truncated with "..."

### Syntax Highlighting
Color-coded elements:
- **Keys** - Light blue
- **String values** - Orange
- **Numbers** - Light green
- **Booleans/null** - Blue
- **Brackets** - Gold

### Format & Minify
- **Format**: Converts JSON to readable format with 2-space indentation
- **Minify**: Removes all whitespace for compact storage or transmission

### Validation
Real-time syntax validation with detailed error messages showing:
- Line number of error
- Character position
- Description of what went wrong

