import os
import re
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

# This is a simple GUI that allows you to browse a directory and then search
# for files by part of the name. Parts are delimited by non-alphanumeric
# characters and lowercased. To deal with the proliferation of parts differing
# only by a numeric suffix, these are truncated.
#
# The autocomplete textbox selects parts that start with the text you enter.
# If you prefix that text with a space, it searchs for parts containing that
# text. In other words, it changes from "part*" to "*part*".
#
# Selecting the part shows all files that contain it. Double-clicking on a
# file open it. Right-clicking on it opens a menu. The first two options
# are self-explanatory. The last fills the parts list based on the selected
# file, letting you search laterally.
#
# To run it conveniently under Windows, create a shortcut to this file. It
# needs to launch python, passing the full path to this file as a parameter.

directory = ""


def show_help():
    messagebox.showinfo(
        "Help",
        "Enter start of part to autocomplete. Prefix with space for wildcard search. Double-click on file for menu.",
    )


class FileInfo:
    def __init__(self, key, path, name, extension, size):
        self.key = key
        self.path = path
        self.name = name
        self.extension = extension
        self.size = size

    def __hash__(self):
        return hash((self.key))

    def __eq__(self, other):
        return (self.key) == (other.key)


def get_file_size(filepath):
    # Normalize filepath to the current operating system's path separator
    filepath = os.path.normpath(filepath)

    try:
        # Get the file size using os.path.getsize()
        size = os.path.getsize(filepath)
        return size
    except:
        # If an error occurs, return 0
        return 0


class AutocompleteEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.var = tk.StringVar()
        self.configure(textvariable=self.var)
        self.var.trace_add("write", self.on_change)
        self.bind("<Tab>", self.autocomplete)

    def on_change(self, *args):
        current_text = self.var.get().lower()
        temp_list = []
        if current_text and current_text[0].isspace():
            # If there's leading whitespace, search `*text*`.
            current_text = current_text.lstrip()
            for part in file_dict:
                if current_text in part:
                    temp_list.append(part)
        else:
            # Otherwise, search `text*`.
            for part in file_dict:
                if part.startswith(current_text):
                    temp_list.append(part)
        temp_list.sort()
        listbox_parts.delete(0, "end")
        for part in temp_list:
            listbox_parts.insert(tk.END, part)
        if listbox_parts.size() > 0:
            listbox_parts.selection_set(0)
            listbox_parts.see(0)
            listbox_parts.event_generate("<<ListboxSelect>>")

    def autocomplete(self, event=None):
        if listbox_parts.size() > 0:
            listbox_parts.selection_set(0)
            listbox_parts.see(0)
            listbox_parts.event_generate("<<ListboxSelect>>")
        return "break"

    def clear_text(self):
        self.var.set("")


def get_files_with_selected_part(event=None):
    set_headings()
    if listbox_parts.curselection():
        selected_part = listbox_parts.get(listbox_parts.curselection())
        if tree.get_children():
            tree.delete(*tree.get_children())
        for file in file_dict[selected_part]:
            tree.insert(
                "",
                "end",
                text=file.key,
                values=(file.path, file.extension, format(file.size, ",")),
            )


def get_selected_file(event=None):
    items = tree.selection()
    if not items:
        return None
    item_text = tree.item(items[0])["text"]
    if len(item_text) == 0:
        return None
    selected_file = os.path.join(directory, item_text)
    return selected_file


def open_selected_file(event=None):
    selected_file = get_selected_file(event)
    if selected_file:
        os.startfile(selected_file)


def open_selected_directory(event=None):
    selected_file = get_selected_file(event)
    if selected_file:
        selected_directory = os.path.dirname(selected_file)
        os.startfile(selected_directory)


def open_laterally(event=None):
    selected_file = get_selected_file(event)
    if selected_file:
        return None
        # Split up file and fill parts list.


def show_tree_menu(event):
    # Select the item that was clicked on
    item = tree.identify_row(event.y)

    # If an item was clicked on, show the context menu
    if item:
        path = tree.item(item)["text"]
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)
        tree_menu.entryconfig(0, label=f"Open File: {filename}")
        tree_menu.entryconfig(1, label=f"Open Directory: {dirname}")
        tree.selection_set(item)
        tree_menu.post(event.x_root, event.y_root)


file_dict = {}


def browse_directory():
    global directory
    directory = filedialog.askdirectory()
    if directory:
        file_dict.clear()
        for current_root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.relpath(os.path.join(current_root, file), directory)
                parts = re.split(r"[^a-zA-Z0-9\u0080-\uFFFF]", file_path)
                file_info = FileInfo(
                    file_path.lower(),
                    file_path,
                    os.path.split(file_path)[-1],
                    os.path.splitext(file_path)[1][1:].upper(),
                    get_file_size(os.path.join(directory, file_path)),
                )
                for part in parts:
                    p = re.sub(r"\d*$", "", part.lower())
                    if len(p) != 0:
                        if p not in file_dict:
                            file_dict[p] = set()
                        file_dict[p].add(file_info)

        for key in file_dict:
            file_dict[key] = sorted(file_dict[key], key=lambda x: x.key)

        listbox_parts.delete(0, "end")
        for part in sorted(file_dict.keys()):
            listbox_parts.insert(tk.END, part)
        entry_autocomplete.clear_text()
        entry_autocomplete.focus()


root = tk.Tk()
custom_font = ("TkDefaultFont", 16, "normal")
root.title("File Part Matcher")
root.state("zoomed")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(1, weight=1)

root.bind("<F1>", lambda event: show_help())

frame_left = tk.Frame(root)
frame_left.grid(row=1, column=0, sticky="nsew")
frame_left.columnconfigure(0, weight=1)
frame_left.rowconfigure(0, weight=0)

entry_autocomplete = AutocompleteEntry(root, width=40, font=custom_font)
entry_autocomplete.grid(row=0, column=0, sticky="ew")

browse_button = tk.Button(frame_left, text="Browse", command=browse_directory)
browse_button.pack(side=tk.TOP, padx=10)

listbox_parts = tk.Listbox(frame_left, width=40, font=custom_font)
listbox_parts.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

scrollbar_parts = tk.Scrollbar(frame_left, command=listbox_parts.yview)
scrollbar_parts.pack(side=tk.LEFT, fill=tk.Y)
listbox_parts.config(yscrollcommand=scrollbar_parts.set)

frame_right = tk.Frame(root)
frame_right.grid(row=1, column=1, sticky="nsew")
frame_right.configure(bg="#ffff00")

style = ttk.Style()
style.theme_use("clam")
style.configure("Custom.Treeview", font=custom_font, rowheight=30)
style.configure("Custom.Treeview.Heading", background="gray", foreground="white")
style.map("Custom.Treeview.Heading", background=[("active", "#005ca3")])
tree = ttk.Treeview(
    frame_right, columns=("name", "type", "size"), style="Custom.Treeview"
)


def set_headings():
    tree.heading("name", text="Name", command=lambda c=0: sortby(tree, c))
    tree.heading("type", text="Type", command=lambda c=1: sortby(tree, c))
    tree.heading("size", text="Size", command=lambda c=2: sortby(tree, c))


screen_width = root.winfo_screenwidth()
tree.heading("#0", text="File Path")
set_headings()
tree.column("#0", width=0, stretch=False)
tree.column(
    "name", minwidth=int(screen_width / 2.5), width=int(screen_width / 2), anchor="w"
)
tree.column("type", width=160, anchor="w")
tree.column("size", width=160, anchor="e")
tree.grid(row=0, column=1, sticky="nsew")


def sortby(tree, column_number):
    column_id = tree.column(column_number, option="id")
    column_text = tree.heading(column_id, option="text")
    last_char = column_text[-1]
    if last_char == "▲":
        descending = True
        column_text = column_text[:-1]
    elif last_char == "▼":
        descending = False
        column_text = column_text[:-1]
    else:
        descending = True

    set_headings()
    tree.heading(
        column_id,
        text=column_text + ("▼" if descending else "▲"),
        command=lambda c=column_number: sortby(tree, c),
    )

    if column_text == "Size":
        data = [
            (float(tree.set(child, column_number).replace(",", "")), child)
            for child in tree.get_children("")
        ]
    else:
        data = [
            (tree.set(child, column_number), child) for child in tree.get_children("")
        ]

    # Sort the items in place
    data.sort(reverse=descending)
    for index, item in enumerate(data):
        tree.move(item[1], "", index)


# Create the scrollbar widget and link it to the treeview widget
vsb = ttk.Scrollbar(frame_right, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=vsb.set)
vsb.grid(row=0, column=2, sticky="ns")

# Configure the size of the rows and columns
frame_right.rowconfigure(0, weight=1)
frame_right.columnconfigure(1, weight=1)

listbox_parts.bind("<<ListboxSelect>>", get_files_with_selected_part)
tree.bind(
    "<Double-Button-1>",
    lambda event: open_selected_file(event) if tree.identify_row(event.y) else None,
)

tree_menu = tk.Menu(root, tearoff=0)
tree_menu.add_command(label="Open File", command=open_selected_file)
tree_menu.add_command(label="Open Directory", command=open_selected_directory)
tree_menu.add_command(label="Explore Laterally", command=open_laterally)
tree.bind("<Button-3>", show_tree_menu)

root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)

browse_button.focus()

root.mainloop()
