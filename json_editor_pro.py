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

class JSONTreeView:
    """Tree view panel for JSON structure navigation"""

    def __init__(self, parent):
        self.parent = parent
        self.container = tk.Frame(parent, bg='#2b2b2b')

        # Header
        header = tk.Frame(self.container, bg='#2b2b2b')
        header.pack(fill='x', padx=5, pady=(5, 2))

        tk.Label(header, text="JSON Structure", bg='#2b2b2b', fg='white',
                font=('Arial', 10, 'bold')).pack(side='left')

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
                       font=('Monaco', 11))

    def populate(self, json_data):
        """Populate tree view with JSON data"""
        # Clear existing tree
        self.tree.delete(*self.tree.get_children())

        if json_data is None:
            return

        # Add root
        root = self.tree.insert("", "end", text="JSON Document", open=True)
        self._add_node(root, json_data)

    def _add_node(self, parent, data):
        """Recursively add JSON nodes to tree"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    node = self.tree.insert(parent, "end", text=f"📁 {key}", open=False)
                    self._add_node(node, value)
                else:
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."
                    self.tree.insert(parent, "end", text=f"{key}: {value_str}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    node = self.tree.insert(parent, "end", text=f"📁 [{i}]", open=False)
                    self._add_node(node, item)
                else:
                    value_str = str(item)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."
                    self.tree.insert(parent, "end", text=f"[{i}]: {value_str}")


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
                           font=('Monaco', 12),
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
        import re
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
        self.tree_view = JSONTreeView(self.root)

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
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if filename:
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
