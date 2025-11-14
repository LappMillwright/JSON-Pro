#!/usr/bin/env python3
"""
JSON Pro - Professional JSON Editor for macOS
Features: Multi-tab editing, tree view, format, validate, minify
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import re

# Settings file for persistent last folder
SETTINGS_FILE = os.path.expanduser("~/.json_editor_pro.json")

def load_settings():
    """Load settings from file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_settings(settings):
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
    except:
        pass

class JSONTreeView:
    """Tree view panel for JSON structure navigation"""

    def __init__(self, parent, on_refresh=None):
        self.parent = parent
        self.container = tk.Frame(parent, bg='#2b2b2b')
        self.on_refresh = on_refresh

        # Header
        header = tk.Frame(self.container, bg='#2b2b2b')
        header.pack(fill='x', padx=5, pady=(5, 2))

        tk.Label(header, text="JSON Structure", bg='#2b2b2b', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left')

        # Refresh button
        refresh_btn = tk.Label(header, text="⟳", bg='#404040', fg='white',
                              padx=8, pady=2, cursor='hand2', relief='raised', bd=1,
                              font=('Arial', 14))
        refresh_btn.pack(side='right')
        refresh_btn.bind("<Button-1>", lambda e: self.on_refresh() if self.on_refresh else None)

        # Hover effects for refresh button
        def on_refresh_enter(e):
            refresh_btn.config(bg='#505050')
        def on_refresh_leave(e):
            refresh_btn.config(bg='#404040')
        refresh_btn.bind("<Enter>", on_refresh_enter)
        refresh_btn.bind("<Leave>", on_refresh_leave)

        # Tree view
        tree_frame = tk.Frame(self.container, bg='#404040', bd=1)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_frame, show='tree')

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Style
        style = ttk.Style()
        style.configure("Treeview",
                       background="#1e1e1e",
                       foreground="#d4d4d4",
                       fieldbackground="#1e1e1e",
                       borderwidth=0,
                       font=('Menlo', 12))

        # Configure tags for keys and values
        self.tree.tag_configure('key', font=('Menlo', 12, 'bold'))  # Bold for folder keys
        self.tree.tag_configure('key_bold', font=('Menlo', 12, 'bold'))  # Bold for key part
        self.tree.tag_configure('value_blue', font=('Menlo', 12), foreground='#569cd6')  # Blue for top-level values
        self.tree.tag_configure('value_green', font=('Menlo', 12), foreground='#4ec9b0')  # Dark green for nested values

        # Bind click event for navigation
        self.tree.bind('<Button-1>', self.on_tree_click)

        # Store callback for navigation
        self.on_key_click = None

    def set_on_key_click(self, callback):
        """Set callback for when a key is clicked"""
        self.on_key_click = callback

    def on_tree_click(self, event):
        """Handle click on tree item"""
        item = self.tree.identify('item', event.x, event.y)
        if item:
            # Get the stored path from the item's values
            values = self.tree.item(item, 'values')
            if values and len(values) > 0:
                json_path = values[0]
                if json_path and self.on_key_click:
                    self.on_key_click(json_path)

    def populate(self, json_data):
        """Populate tree view with JSON data"""
        # Clear existing tree
        self.tree.delete(*self.tree.get_children())

        if json_data is None:
            return

        # Add root
        root = self.tree.insert("", "end", text="JSON Document", open=True, values=("",))
        self._add_node(root, json_data, level=0, path="")

    def _add_node(self, parent, data, level=0, path=""):
        """Recursively add JSON nodes to tree"""
        if isinstance(data, dict):
            for key, value in data.items():
                # Build the path for this key
                new_path = f"{path}.{key}" if path else key

                if isinstance(value, (dict, list)):
                    # Folder keys - keep bold
                    node = self.tree.insert(parent, "end", text=f"📁 {key}", open=False, tags=('key',), values=(new_path,))
                    self._add_node(node, value, level=level+1, path=new_path)
                else:
                    # Key:value pairs - format as "key : value"
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."

                    # Use different colors based on nesting level
                    if level == 0:
                        # Top level values in blue
                        tag = 'value_blue'
                    else:
                        # Nested values in dark green
                        tag = 'value_green'

                    # Format: "key" in default + " : " + value
                    # Since we can't mix fonts, we'll use spacing to visually separate
                    self.tree.insert(parent, "end", text=f"{key}  :  {value_str}", tags=(tag,), values=(new_path,))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                # Build the path for this array index
                new_path = f"{path}[{i}]"

                if isinstance(item, (dict, list)):
                    node = self.tree.insert(parent, "end", text=f"📁 [{i}]", open=False, tags=('key',), values=(new_path,))
                    self._add_node(node, item, level=level+1, path=new_path)
                else:
                    value_str = str(item)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."

                    # Array items use same color scheme as regular values
                    if level == 0:
                        tag = 'value_blue'
                    else:
                        tag = 'value_green'

                    self.tree.insert(parent, "end", text=f"[{i}]  :  {value_str}", tags=(tag,), values=(new_path,))


class JSONTab:
    """Individual JSON editing tab"""

    def __init__(self, parent, tab_id, on_content_changed=None):
        self.parent = parent
        self.tab_id = tab_id
        self.on_content_changed = on_content_changed
        self.file_path = None
        self.modified = False

        # Create main container
        self.container = tk.Frame(parent, bg='#2b2b2b')

        # File info bar
        info_bar = tk.Frame(self.container, bg='#2b2b2b')
        info_bar.pack(fill='x', padx=5, pady=(5, 2))

        self.file_label = tk.Label(info_bar, text="Untitled", bg='#2b2b2b',
                                   fg='#808080', font=('Arial', 9))
        self.file_label.pack(side='left')

        self.position_label = tk.Label(info_bar, text="Line 1, Col 1",
                                       bg='#2b2b2b', fg='#808080', font=('Arial', 9))
        self.position_label.pack(side='right')

        # Text editor with frame
        editor_frame = tk.Frame(self.container, bg='#2b2b2b', bd=1)
        editor_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.text = tk.Text(editor_frame,
                           bg='#1e1e1e',
                           fg='#d4d4d4',
                           insertbackground='white',
                           font=('Menlo', 13),
                           wrap='none',
                           bd=0,
                           highlightthickness=0)

        # Scrollbars
        vsb = ttk.Scrollbar(editor_frame, orient="vertical", command=self.text.yview)
        hsb = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.text.xview)

        self.text.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        editor_frame.grid_rowconfigure(0, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)

        self.text.config(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Bind events
        self.text.bind('<KeyRelease>', self.update_position)
        self.text.bind('<ButtonRelease>', self.update_position)
        self.text.bind('<<Modified>>', self.on_text_modified)
        self.text.bind("<Command-s>", lambda e: self.on_save_request())

        # Setup syntax highlighting
        self.setup_syntax_highlighting()

    def setup_syntax_highlighting(self):
        """Setup JSON syntax highlighting"""
        # Configure tags
        self.text.tag_config('key', foreground='#9cdcfe')        # Light blue for keys
        self.text.tag_config('string', foreground='#ce9178')     # Orange for strings
        self.text.tag_config('number', foreground='#b5cea8')     # Light green for numbers
        self.text.tag_config('boolean', foreground='#569cd6')    # Blue for true/false
        self.text.tag_config('null', foreground='#569cd6')       # Blue for null
        self.text.tag_config('bracket', foreground='#ffd700')    # Gold for brackets

        self.text.bind('<KeyRelease>', self.highlight_syntax)

    def highlight_syntax(self, event=None):
        """Apply JSON syntax highlighting"""
        # Simple JSON highlighting
        content = self.text.get('1.0', tk.END)

        # Remove all tags
        for tag in ['key', 'string', 'number', 'boolean', 'null', 'bracket']:
            self.text.tag_remove(tag, '1.0', tk.END)

        # Highlight strings (keys and values)
        start_idx = '1.0'
        while True:
            pos = self.text.search('"', start_idx, tk.END)
            if not pos:
                break
            end_pos = self.text.search('"', f"{pos}+1c", tk.END)
            if not end_pos:
                break

            # Check if it's a key (followed by :)
            char_after = self.text.get(f"{end_pos}+1c", f"{end_pos}+2c")
            if char_after.strip().startswith(':'):
                self.text.tag_add('key', pos, f"{end_pos}+1c")
            else:
                self.text.tag_add('string', pos, f"{end_pos}+1c")

            start_idx = f"{end_pos}+1c"

        # Highlight numbers
        for match in re.finditer(r'\b\d+\.?\d*\b', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('number', start, end)

        # Highlight booleans and null
        for word, tag in [('true', 'boolean'), ('false', 'boolean'), ('null', 'null')]:
            start_idx = '1.0'
            while True:
                pos = self.text.search(r'\b' + word + r'\b', start_idx, tk.END, regexp=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(word)}c"
                self.text.tag_add(tag, pos, end_pos)
                start_idx = end_pos

        # Highlight brackets
        for char in ['{', '}', '[', ']']:
            start_idx = '1.0'
            while True:
                pos = self.text.search(char, start_idx, tk.END)
                if not pos:
                    break
                self.text.tag_add('bracket', pos, f"{pos}+1c")
                start_idx = f"{pos}+1c"

    def update_position(self, event=None):
        """Update cursor position display"""
        position = self.text.index(tk.INSERT)
        line, col = position.split('.')
        self.position_label.config(text=f"Line {line}, Col {int(col)+1}")

    def on_text_modified(self, event=None):
        """Called when text is modified"""
        if self.text.edit_modified():
            self.modified = True
            if self.on_content_changed:
                self.on_content_changed(self.tab_id)
            self.text.edit_modified(False)

    def on_save_request(self):
        """Called when save is requested"""
        # This will be connected to the main app's save function
        pass

    def get_content(self):
        """Get the JSON text content"""
        return self.text.get("1.0", tk.END).strip()

    def set_content(self, content):
        """Set the JSON text content"""
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.highlight_syntax()
        self.modified = False

    def set_file_path(self, path):
        """Set the file path for this tab"""
        self.file_path = path
        if path:
            filename = os.path.basename(path)
            self.file_label.config(text=filename, fg='#50fa7b')
        else:
            self.file_label.config(text="Untitled", fg='#808080')

    def find_and_highlight_key(self, json_path):
        """Find a key in the JSON text using its path, scroll to it, and highlight it"""
        # Remove any existing highlights
        self.text.tag_remove('highlight', '1.0', tk.END)

        # Configure highlight tag
        self.text.tag_config('highlight', background='#ffd700', foreground='#000000')

        if not json_path:
            return

        try:
            # Parse the JSON to get the structure
            content = self.get_content()
            if not content:
                return

            data = json.loads(content)

            # Navigate to the value using the path
            path_parts = self._parse_path(json_path)
            if not path_parts:
                return

            # Find the key position by parsing the text and tracking paths
            position = self._find_key_position_by_path(content, json_path)

            if position:
                start_pos, end_pos = position

                # Highlight the key
                self.text.tag_add('highlight', start_pos, end_pos)

                # Scroll to make it visible
                self.text.see(start_pos)
                self.text.mark_set(tk.INSERT, start_pos)

                # Update position indicator
                self.update_position()

                # Remove highlight after 3 seconds
                self.text.after(3000, lambda: self.text.tag_remove('highlight', '1.0', tk.END))

        except Exception as e:
            # If path-based search fails, fall back to simple search
            print(f"Path-based search failed: {e}")
            import traceback
            traceback.print_exc()

    def _parse_path(self, path):
        """Parse a JSON path like 'user.address.city' or 'items[0].name' into parts"""
        if not path:
            return []

        parts = []
        current = ""
        i = 0
        while i < len(path):
            if path[i] == '.':
                if current:
                    parts.append(current)
                    current = ""
                i += 1
            elif path[i] == '[':
                if current:
                    parts.append(current)
                    current = ""
                # Find the closing bracket
                j = i + 1
                while j < len(path) and path[j] != ']':
                    j += 1
                # Extract the index
                index = int(path[i+1:j])
                parts.append(index)
                i = j + 1
            else:
                current += path[i]
                i += 1

        if current:
            parts.append(current)

        return parts

    def _find_key_position_by_path(self, content, target_path):
        """Find the text position of a key by parsing JSON and tracking paths"""
        # Parse the path
        path_parts = self._parse_path(target_path)
        if not path_parts:
            return None

        target_key = path_parts[-1]

        # If it's an array index, handle differently
        if isinstance(target_key, int):
            return None  # For now, skip array indices

        # Track all key positions and their paths
        key_positions = []

        # Parse JSON manually to track positions
        lines = content.split('\n')

        for line_idx, line in enumerate(lines):
            line_num = line_idx + 1

            # Look for key patterns: "key":
            # Use regex to find all quoted strings followed by colon
            for match in re.finditer(r'"([^"]+)"\s*:', line):
                key_name = match.group(1)
                key_start_in_line = match.start()

                # If the key matches our target
                if key_name == target_key:
                    # Store this position with the key
                    key_positions.append({
                        'key': key_name,
                        'line': line_num,
                        'col': key_start_in_line
                    })

        # Now we need to figure out which occurrence matches our path
        # We'll do this by parsing the JSON structure
        occurrence_index = self._find_path_occurrence(content, target_path)

        if occurrence_index is not None and occurrence_index < len(key_positions):
            pos_info = key_positions[occurrence_index]

            # Convert to Tkinter text widget position
            start_pos = f"{pos_info['line']}.{pos_info['col']}"
            # Calculate end position (key with quotes)
            end_pos = f"{pos_info['line']}.{pos_info['col'] + len(target_key) + 2}"  # +2 for quotes

            return (start_pos, end_pos)

        return None

    def _find_path_occurrence(self, content, target_path):
        """Find which occurrence of a key name corresponds to the target path"""
        try:
            data = json.loads(content)
            path_parts = self._parse_path(target_path)

            if not path_parts:
                return 0

            target_key = path_parts[-1]
            if isinstance(target_key, int):
                return 0

            # Count how many times we see this key name before reaching our target
            count = [0]  # Use list to make it mutable in nested function
            found_index = [None]

            def traverse(obj, current_path):
                if found_index[0] is not None:
                    return

                if isinstance(obj, dict):
                    for key, value in obj.items():
                        # Build current path
                        new_path = current_path + [key]

                        # If this key matches our target key name
                        if key == target_key:
                            # Check if this is our target path
                            if new_path == path_parts:
                                found_index[0] = count[0]
                                return
                            else:
                                # This is a different occurrence
                                count[0] += 1

                        # Recurse into nested structures
                        if isinstance(value, (dict, list)):
                            traverse(value, new_path)

                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        new_path = current_path + [i]
                        if isinstance(item, (dict, list)):
                            traverse(item, new_path)

            traverse(data, [])
            return found_index[0] if found_index[0] is not None else 0

        except Exception as e:
            print(f"Error in _find_path_occurrence: {e}")
            import traceback
            traceback.print_exc()
            return 0


class JSONEditorPro:
    """Main JSON Editor Application"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JSON Pro")

        # Start with a default size
        self.root.geometry("1000x700")

        # Maximize window
        self.root.after(100, self.maximize_window)

        # Variables
        self.tabs = {}
        self.tab_counter = 0
        self.tree_panel_visible = True

        # Load settings
        self.settings = load_settings()
        self.last_folder = self.settings.get('last_folder', os.path.expanduser("~"))

        # Create UI
        self.create_widgets()

        # Bind shortcuts
        self.root.bind("<Command-o>", lambda e: self.open_file())
        self.root.bind("<Command-s>", lambda e: self.save_file())
        self.root.bind("<Command-n>", lambda e: self.create_new_tab())
        self.root.bind("<Command-t>", lambda e: self.create_new_tab())
        self.root.bind("<Command-f>", lambda e: self.format_json())
        self.root.bind("<Command-m>", lambda e: self.minify_json())
        self.root.bind("<Command-k>", lambda e: self.validate_json())
        self.root.bind("<Command-r>", lambda e: self.refresh_tree())

    def maximize_window(self):
        """Maximize window to fill screen"""
        if sys.platform == 'darwin':
            try:
                self.root.state('zoomed')
            except:
                pass
        else:
            self.root.state('zoomed')

        self.root.configure(bg='#2b2b2b')

    def create_widgets(self):
        """Create the main UI"""

        # Top toolbar
        toolbar = tk.Frame(self.root, bg='#3c3c3c', height=40)
        toolbar.pack(fill='x', padx=0, pady=0)

        def create_button(parent, text, command, side='left'):
            btn = tk.Label(parent, text=text, bg='#404040', fg='white',
                          padx=12, pady=6, cursor='hand2', relief='raised', bd=1)
            btn.pack(side=side, padx=2, pady=5)
            btn.bind("<Button-1>", lambda e: command())

            def on_enter(e):
                btn.config(bg='#505050')
            def on_leave(e):
                btn.config(bg='#404040')

            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            return btn

        # Left side buttons
        create_button(toolbar, "+ NEW", self.create_new_tab)
        create_button(toolbar, "OPEN", self.open_file)
        create_button(toolbar, "SAVE", self.save_file)
        create_button(toolbar, "FORMAT", self.format_json)
        create_button(toolbar, "MINIFY", self.minify_json)
        create_button(toolbar, "VALIDATE", self.validate_json)

        # Toggle tree view button
        self.tree_toggle_btn = create_button(toolbar, "TREE ▼", self.toggle_tree_panel)

        # Status label
        self.status_label = tk.Label(toolbar, text="", bg='#3c3c3c',
                                    fg='#808080', font=('Arial', 10))
        self.status_label.pack(side='right', padx=10)

        # Main container with paned window
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL,
                                         sashwidth=8, sashrelief=tk.RAISED,
                                         bg='#404040', borderwidth=0)
        self.main_paned.pack(fill='both', expand=True, padx=5, pady=5)

        # Left panel - Tree view
        self.tree_view = JSONTreeView(self.root, on_refresh=self.refresh_tree)
        self.tree_view.set_on_key_click(self.on_key_clicked)

        # Right panel - Tabs
        right_panel = tk.Frame(self.root, bg='#2b2b2b')

        # Create notebook for tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Custom.TNotebook',
                       background='#2b2b2b',
                       borderwidth=0)
        style.configure('Custom.TNotebook.Tab',
                       background='#404040',
                       foreground='#d4d4d4',
                       padding=[15, 8],
                       font=('Arial', 10))
        style.map('Custom.TNotebook.Tab',
                 background=[('selected', '#2b2b2b'), ('!selected', '#404040')],
                 foreground=[('selected', '#89b4fa'), ('!selected', '#d4d4d4')])

        self.notebook = ttk.Notebook(right_panel, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)

        # Bind tab change event
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        self.notebook.bind('<Button-3>', self.on_tab_right_click)

        # Add panels to paned window
        self.main_paned.add(self.tree_view.container, minsize=200)
        self.main_paned.add(right_panel, minsize=400)

        # Set initial sash position
        self.root.update_idletasks()
        self.main_paned.sash_place(0, 250, 1)

        # Create first tab
        self.create_new_tab()

    def toggle_tree_panel(self):
        """Toggle tree panel visibility"""
        if self.tree_panel_visible:
            self.main_paned.forget(self.tree_view.container)
            self.tree_toggle_btn.config(text="TREE ▶")
            self.tree_panel_visible = False
        else:
            self.main_paned.add(self.tree_view.container, before=self.main_paned.panes()[0])
            self.main_paned.sash_place(0, 250, 1)
            self.tree_toggle_btn.config(text="TREE ▼")
            self.tree_panel_visible = True

    def create_new_tab(self):
        """Create a new editing tab"""
        self.tab_counter += 1
        tab_id = self.tab_counter
        tab_name = f"Untitled {tab_id}"

        tab = JSONTab(self.notebook, tab_id, on_content_changed=self.on_tab_modified)

        self.tabs[tab_id] = {
            'tab': tab,
            'name': tab_name
        }

        self.notebook.add(tab.container, text=tab_name)
        self.notebook.select(tab.container)
        tab.text.focus_set()

    def get_current_tab(self):
        """Get the currently active tab"""
        current = self.notebook.select()
        if not current:
            return None

        for tab_id, tab_data in self.tabs.items():
            if str(tab_data['tab'].container) == current:
                return tab_data['tab']
        return None

    def on_tab_modified(self, tab_id):
        """Called when a tab is modified"""
        if tab_id in self.tabs:
            tab_data = self.tabs[tab_id]
            tab = tab_data['tab']
            name = tab_data['name']
            if tab.modified and not name.startswith('*'):
                self.notebook.tab(tab.container, text=f"*{name}")

    def on_tab_changed(self, event=None):
        """Called when tab changes"""
        current_tab = self.get_current_tab()
        if current_tab:
            # Update tree view with current JSON
            try:
                content = current_tab.get_content()
                if content:
                    data = json.loads(content)
                    self.tree_view.populate(data)
                else:
                    self.tree_view.populate(None)
            except:
                self.tree_view.populate(None)

    def on_tab_right_click(self, event):
        """Handle right-click on tab"""
        clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
        if clicked_tab == "":
            return

        tab_index = int(clicked_tab)
        tab_id = None
        for tid, tdata in self.tabs.items():
            if self.notebook.index(tdata['tab'].container) == tab_index:
                tab_id = tid
                break

        if not tab_id:
            return

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Rename", command=lambda: self.rename_tab(tab_id))
        if len(self.tabs) > 1:
            menu.add_separator()
            menu.add_command(label="Close", command=lambda: self.close_tab(tab_id))
        menu.post(event.x_root, event.y_root)

    def rename_tab(self, tab_id):
        """Rename a tab"""
        # Similar to SQL Jaguar implementation
        pass

    def close_tab(self, tab_id):
        """Close a tab"""
        if tab_id not in self.tabs:
            return

        tab_data = self.tabs[tab_id]
        tab = tab_data['tab']

        if tab.modified:
            response = messagebox.askyesno(
                "Close Tab",
                f"Close '{tab_data['name']}'?\n\nUnsaved changes will be lost."
            )
            if not response:
                return

        self.notebook.forget(tab.container)
        tab.container.destroy()
        del self.tabs[tab_id]

    def open_file(self):
        """Open a JSON file"""
        filename = filedialog.askopenfilename(
            title="Open JSON File",
            initialdir=self.last_folder,
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if filename:
            # Save the folder for next time
            self.last_folder = os.path.dirname(filename)
            self.settings['last_folder'] = self.last_folder
            save_settings(self.settings)

            try:
                with open(filename, 'r') as f:
                    content = f.read()

                # Validate JSON
                json.loads(content)

                # Create new tab or use current empty tab
                current_tab = self.get_current_tab()
                if current_tab and not current_tab.get_content() and not current_tab.file_path:
                    tab = current_tab
                else:
                    self.create_new_tab()
                    tab = self.get_current_tab()

                # Load content
                tab.set_content(content)
                tab.set_file_path(filename)
                tab.modified = False

                # Update tab name
                for tab_id, tab_data in self.tabs.items():
                    if tab_data['tab'] == tab:
                        tab_data['name'] = os.path.basename(filename)
                        self.notebook.tab(tab.container, text=os.path.basename(filename))
                        break

                # Update tree view
                self.on_tab_changed()

                self.status_label.config(text=f"Opened: {os.path.basename(filename)}", fg='#50fa7b')
                self.root.after(3000, lambda: self.status_label.config(text=""))

            except json.JSONDecodeError as e:
                messagebox.showerror("Invalid JSON", f"Error parsing JSON:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error opening file:\n{str(e)}")

    def save_file(self):
        """Save current JSON file"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        # If no file path, do save as
        if not current_tab.file_path:
            self.save_file_as()
            return

        try:
            content = current_tab.get_content()

            # Validate JSON before saving
            json.loads(content)

            with open(current_tab.file_path, 'w') as f:
                f.write(content)

            # Save the folder for next time
            self.last_folder = os.path.dirname(current_tab.file_path)
            self.settings['last_folder'] = self.last_folder
            save_settings(self.settings)

            current_tab.modified = False

            # Update tab name (remove *)
            for tab_id, tab_data in self.tabs.items():
                if tab_data['tab'] == current_tab:
                    self.notebook.tab(current_tab.container, text=tab_data['name'])
                    break

            self.status_label.config(text="Saved", fg='#50fa7b')
            self.root.after(2000, lambda: self.status_label.config(text=""))

        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Cannot save invalid JSON:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def save_file_as(self):
        """Save as new file"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialdir=self.last_folder,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            current_tab.set_file_path(filename)
            self.save_file()

    def format_json(self):
        """Format (pretty print) JSON"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        try:
            content = current_tab.get_content()
            data = json.loads(content)
            formatted = json.dumps(data, indent=2, ensure_ascii=False)

            current_tab.set_content(formatted)
            self.on_tab_changed()

            self.status_label.config(text="Formatted", fg='#50fa7b')
            self.root.after(2000, lambda: self.status_label.config(text=""))

        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Cannot format invalid JSON:\n{str(e)}")

    def minify_json(self):
        """Minify JSON (remove whitespace)"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        try:
            content = current_tab.get_content()
            data = json.loads(content)
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

            current_tab.set_content(minified)
            self.on_tab_changed()

            self.status_label.config(text="Minified", fg='#50fa7b')
            self.root.after(2000, lambda: self.status_label.config(text=""))

        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Cannot minify invalid JSON:\n{str(e)}")

    def validate_json(self):
        """Validate JSON syntax"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        try:
            content = current_tab.get_content()
            json.loads(content)

            self.status_label.config(text="✓ Valid JSON", fg='#50fa7b')
            self.root.after(3000, lambda: self.status_label.config(text=""))

        except json.JSONDecodeError as e:
            error_msg = str(e)
            messagebox.showerror("Invalid JSON", f"JSON validation failed:\n\n{error_msg}")
            self.status_label.config(text="✗ Invalid JSON", fg='#ff5555')

    def refresh_tree(self):
        """Refresh the JSON tree view from current tab content"""
        current_tab = self.get_current_tab()
        if not current_tab:
            return

        try:
            content = current_tab.get_content()
            if content:
                data = json.loads(content)
                self.tree_view.populate(data)
                self.status_label.config(text="Tree refreshed", fg='#50fa7b')
                self.root.after(2000, lambda: self.status_label.config(text=""))
            else:
                self.tree_view.populate(None)
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Cannot refresh tree with invalid JSON:\n{str(e)}")
            self.status_label.config(text="✗ Invalid JSON", fg='#ff5555')

    def on_key_clicked(self, json_path):
        """Handle click on a key in the tree view"""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.find_and_highlight_key(json_path)

    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """Handle window closing"""
        # Check for unsaved changes
        unsaved = []
        for tab_id, tab_data in self.tabs.items():
            if tab_data['tab'].modified:
                unsaved.append(tab_data['name'])

        if unsaved:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Save changes before closing?\n\nUnsaved tabs: {', '.join(unsaved)}"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes - save all
                for tab_id, tab_data in self.tabs.items():
                    if tab_data['tab'].modified:
                        # Would need to implement save all
                        pass

        self.root.destroy()


def main():
    app = JSONEditorPro()
    app.run()


if __name__ == "__main__":
    main()
