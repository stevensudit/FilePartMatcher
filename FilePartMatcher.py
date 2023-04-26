import os
import re
import time
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from collections import namedtuple

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
# file opens it. Right-clicking on it opens a menu. The first two options
# are self-explanatory. The last fills the parts list based on the selected
# file, letting you search laterally. In lateral search mode, the part list
# contains only the ones relevant to the file that you had selected and the
# autocomplete textbox has a leading ">" to indicate that it's scoped to this
# partial list. Clearing the textbox restores regular mode.
#
# To run it conveniently under Windows, create a shortcut to this file. It
# needs to launch python, passing the full path to this file as a parameter.

# Top-level directory being searched.
directory = ""

# Maps parts to the FileInfo's that contain them.
file_dict = {}

# Holds currently-displayed parts list.
part_list = []

# Counter used for title display
title_counter = 0

# Named tuple to hold file info for each row in the tree.
FileInfo = namedtuple("FileInfo", ["key", "path", "name", "extension", "size"])


# Shows help messagebox.
def show_help():
    messagebox.showinfo(
        "Help",
        "Enter start of part to autocomplete. Prefix with space for wildcard search. Double-click on file for launch. Right-click for menu.",
    )


# Control for auto-complete.
class AutocompleteEntry(tk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.var = tk.StringVar()
        self.configure(textvariable=self.var)
        self.var.trace_add("write", self.on_change)

    # Updates part list display based on current text.
    def on_change(self, *args):
        current_text = self.var.get().lower()
        temp_list = []
        if current_text and current_text[0].isspace():
            # If there's leading whitespace, search `*text*`.
            current_text = current_text.lstrip()
            for part in file_dict:
                if current_text in part:
                    temp_list.append(part)
        elif current_text and current_text[0] == ">":
            # If we're in lateral search mode, search within partial list.
            current_text = current_text[1:]
            for part in part_list:
                if part.startswith(current_text):
                    temp_list.append(part)
        else:
            # Otherwise, search `text*`.
            for part in file_dict:
                if part.startswith(current_text):
                    temp_list.append(part)

        # Display list and cascade changes.
        temp_list.sort()
        listbox_parts.delete(0, "end")
        for part in temp_list:
            listbox_parts.insert(tk.END, part)
        if listbox_parts.size() > 0:
            listbox_parts.selection_set(0)
            listbox_parts.see(0)
            listbox_parts.event_generate("<<ListboxSelect>>")

    def set_text(self, text=""):
        self.var.set(text)


# Updates tree with files that contain selected part.
def show_files_with_selected_part(event=None):
    if not listbox_parts.curselection():
        return

    # Reset headings to remove sorting indicators and timer.
    update_title()
    set_headings()

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


# Helper to extract selected file from tree.
def get_selected_file(event=None):
    items = tree.selection()
    if not items:
        return None
    item_text = tree.item(items[0])["text"]
    if len(item_text) == 0:
        return None
    selected_file = os.path.join(directory, item_text)
    return selected_file


# Opens selected file.
def open_selected_file(event=None):
    selected_file = get_selected_file(event)
    if selected_file:
        os.startfile(selected_file)


# Opens selected file's directory.
def open_selected_directory(event=None):
    selected_file = get_selected_file(event)
    if selected_file:
        selected_directory = os.path.dirname(selected_file)
        os.startfile(selected_directory)


# Opens lateral search on the parts from the selected file.
def open_laterally(event=None):
    global part_list
    selected_file = get_selected_file(event)
    selected_file = os.path.relpath(selected_file, directory)
    if selected_file:
        part_list = list(set(get_parts(selected_file)))
        show_part_list(True)


# Pop up context menu on right-click in tree. Doubles as a properties box to
# see attributes that aren't visible without resizing columns.
def show_context_menu(event):
    item = tree.identify_row(event.y)
    if not item:
        return
    path = tree.item(item)["text"]
    filename = os.path.basename(path)
    dirname = os.path.dirname(path)
    tree_menu.entryconfig(0, label=f"Open File: {filename}")
    tree_menu.entryconfig(1, label=f"Open Directory: {dirname}")
    tree.selection_set(item)
    tree_menu.post(event.x_root, event.y_root)


non_alphanumeric_regex = re.compile(r"[^a-zA-Z0-9\u0080-\uFFFF]")
trailing_numbers_regex = re.compile(r"\d*$")


# Breaks file path into parts, normalizing them for searching.
# Dedupes but does not sort.
def get_parts(file_path):
    # Split on anything that's not alphanumeric, but leave high Unicode alone.
    parts = re.split(non_alphanumeric_regex, file_path)
    # Remove trailing numbers and (subsequent) empty parts.
    parts = [trailing_numbers_regex.sub("", part.lower()) for part in parts]
    parts = [part for part in parts if len(part) != 0]
    return parts


# Fill part list with sub-list. Pass True to start a lateral search.
def show_part_list(start_exploring=False):
    listbox_parts.delete(0, "end")
    for part in part_list:
        listbox_parts.insert(tk.END, part)
    if start_exploring:
        entry_autocomplete.set_text(">")
    else:
        entry_autocomplete.set_text()
    entry_autocomplete.focus()


# Update title, potentially resetting or incrementing counter.
def update_title(increment=0, msg=""):
    global title_counter
    if not increment:
        title_counter = 0
    else:
        title_counter += increment

    if title_counter == 0:
        root.title(f"File Part Matcher: {directory} {msg}")
        return

    if title_counter % 100 == 0:
        root.title(f"File Part Matcher: {directory}, {title_counter} {msg}")
        if title_counter % 1000 == 0:
            root.update()


# Find files and sizes recursively.
def find_files(directory):
    file_list = []
    for entry in os.scandir(directory):
        if entry.is_symlink():
            continue
        if entry.is_file():
            update_title(1, "files found")
            file_list.append((entry.path, entry.stat().st_size))
        elif entry.is_dir():
            file_list.extend(find_files(entry.path))
    return file_list


# Pop up a directory dialog and then find all files recursively.
def browse_directory():
    global directory
    directory = os.path.normpath(filedialog.askdirectory())
    update_title()
    if not directory:
        return

    root.config(cursor="wait")
    root.update_idletasks()
    root.after(100, process_files)


# Process files into parts.
def process_files():
    global directory
    global part_list
    global file_dict

    start_time = time.time()
    file_dict.clear()
    update_title()
    files = find_files(directory)
    for file_path, file_size in files:
        rel_path = os.path.relpath(file_path, directory)
        file_info = FileInfo(
            rel_path.lower(),
            rel_path,
            os.path.split(rel_path)[-1],
            os.path.splitext(rel_path)[1][1:].upper(),
            file_size,
        )
        update_title(-1, "files to extract parts from")
        parts = get_parts(rel_path)
        for part in parts:
            if part not in file_dict:
                file_dict[part] = set()
            file_dict[part].add(file_info)

    update_title(0, ", sorting...")
    update_title(len(file_dict), " parts to sort")

    def sort_file_list(file_list):
        file_list.sort(key=lambda x: x.key)
        update_title(-1, " parts to sort")
        return file_list

    # Sort file lists for each part.
    update_title(len(file_dict), " parts to sort")
    file_dict = {key: sort_file_list(list(file_dict[key])) for key in file_dict}

    # Sort parts.
    update_title(0, ", sorting list of {len(file_dict)} parts")
    part_list = [key for key in sorted(file_dict.keys())]

    update_title(0, f", displaying")
    show_part_list()
    root.config(cursor="")
    root.update_idletasks()
    elapsed_time = time.time() - start_time
    formatted_part_count = format(len(part_list), ",")
    formatted_file_count = format(len(files), ",")

    update_title(
        0,
        f", found {formatted_part_count} parts among "
        f"{formatted_file_count} files in {elapsed_time:.2f} seconds",
    )


# Create the window.
root = tk.Tk()
custom_font = ("TkDefaultFont", 16, "normal")
update_title()
root.state("zoomed")
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(1, weight=1)
root.bind("<F1>", lambda event: show_help())

# Create the left frame, which holds the autocomplete entry and the file part
# listbox, as well as the browse button.
frame_left = tk.Frame(root)
frame_left.grid(row=1, column=0, sticky="nsew")
frame_left.columnconfigure(0, weight=1)
frame_left.rowconfigure(1, weight=1)

entry_autocomplete = AutocompleteEntry(frame_left, width=40, font=custom_font)
entry_autocomplete.grid(row=0, column=0, sticky="ew")

browse_button = tk.Button(frame_left, text="Browse", command=browse_directory)
browse_button.grid(row=0, column=1, padx=10, sticky="w")

listbox_parts = tk.Listbox(frame_left, width=40, font=custom_font)
listbox_parts.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

scrollbar_parts = tk.Scrollbar(frame_left, command=listbox_parts.yview)
scrollbar_parts.grid(row=1, column=2, sticky="ns")
listbox_parts.config(yscrollcommand=scrollbar_parts.set)

# Create the right frame, which holds the tree control with file info.
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


# Set up the sortable columns, removing sort indicators.
def set_headings():
    tree.heading("name", text="Name", command=lambda c=0: sortby(tree, c))
    tree.heading("type", text="Type", command=lambda c=1: sortby(tree, c))
    tree.heading("size", text="Size", command=lambda c=2: sortby(tree, c))


# Set tree headings and column widths.
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


# Sort when tree heading is clicked.
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

    # Special-case the size column so that it sorts numerically.
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

# Bind double-click to tree rows.
listbox_parts.bind("<<ListboxSelect>>", show_files_with_selected_part)
tree.bind(
    "<Double-Button-1>",
    lambda event: open_selected_file(event) if tree.identify_row(event.y) else None,
)

# Create context menu for tree and bind it to right-click.
tree_menu = tk.Menu(root, tearoff=0)
tree_menu.add_command(label="Open File", command=open_selected_file, font=custom_font)
tree_menu.add_command(
    label="Open Directory", command=open_selected_directory, font=custom_font
)
tree_menu.add_command(
    label="Explore Laterally", command=open_laterally, font=custom_font
)
tree.bind("<Button-3>", show_context_menu)

# Go.
browse_button.focus()
root.mainloop()
