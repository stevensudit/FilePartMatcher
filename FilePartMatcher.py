import os
import re
import tkinter as tk
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
# file open it. Right-clicking on it opens the directory it's in.
#
# To run it conveniently under Windows, create a shortcut to this file. It
# needs to launch python, passing the full path to this file as a parameter.
#
# As this was written primarily by ChatGPT-4 and I don't even know tkinter,
# literally no effort was made to optimize the code or add convenient but non-
# essential features. It could benefit from such obvious improvements as
# showing the selected path in the window bar, adding a button to change sort
# direction, supporting non-Windows systems, and offering sideways navigation
# from files.
# 
# The way that last feature might work is that you select a file, click
# something to see a list of its parts, and then choose one that is pasted
# into the autocomplete field for you. Probably, you'd want to have right-
# click bring up a context menu to choose between opening the directory and
# doing that sideways navigation. All this is abover my pay grade, though,
# as this is an unpaid project that I'm hardly qualified to maintain. Maybe
# I should ask ChatGPT-4 to finish the job it started. At least it's getting
# paid.

directory = ""


def show_help():
    messagebox.showinfo(
        "Help",
        "Enter start of part to autocomplete. Prefix with space for wildcard search. Double-click on file to launch. Right-click to open diretory.",
    )


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
                if current_text in part.lower():
                    temp_list.append(part)
        else:
            # Otherwise, search `text*`.
            for part in file_dict:
                if part.lower().startswith(current_text):
                    temp_list.append(part)
        temp_list.sort(key=str.lower)
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
    if listbox_parts.curselection():
        selected_part = listbox_parts.get(listbox_parts.curselection())
        listbox_files.delete(0, tk.END)
        for file in file_dict[selected_part]:
            listbox_files.insert(tk.END, file)


def open_selected_file(event=None):
    selected_file = os.path.join(
        directory, listbox_files.get(listbox_files.curselection())
    )
    os.startfile(selected_file)


def open_selected_directory(event=None):
    selected_directory = os.path.dirname(
        os.path.join(directory, listbox_files.get(listbox_files.curselection()))
    )
    os.startfile(selected_directory)


root = tk.Tk()
custom_font = ("TkDefaultFont", 16)
root.title("File Part Matcher")
root.state("zoomed")

root.bind("<F1>", lambda event: show_help())

root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

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

                for part in parts:
                    p = re.sub(r"\d*$", "", part.lower())
                    if len(p) != 0:
                        if p not in file_dict:
                            file_dict[p] = set()
                        file_dict[p].add(file_path)

        for key in file_dict:
            file_dict[key] = sorted(file_dict[key])

        listbox_parts.delete(0, "end")
        for part in sorted(file_dict.keys(), key=str.lower):
            listbox_parts.insert(tk.END, part)
        entry_autocomplete.clear_text()
        entry_autocomplete.focus()


entry_autocomplete = AutocompleteEntry(root, width=40, font=custom_font)
entry_autocomplete.grid(row=0, column=0, sticky="ew")

frame_left = tk.Frame(root)
frame_left.grid(row=1, column=0, sticky="nsew")

browse_button = tk.Button(frame_left, text="Browse", command=browse_directory)
browse_button.pack(side=tk.TOP, padx=10)

listbox_parts = tk.Listbox(frame_left, width=40, font=custom_font)
listbox_parts.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

scrollbar_parts = tk.Scrollbar(frame_left, command=listbox_parts.yview)
scrollbar_parts.pack(side=tk.LEFT, fill=tk.Y)
listbox_parts.config(yscrollcommand=scrollbar_parts.set)

frame_files = tk.Frame(root)
frame_files.grid(row=1, column=1, sticky="nsew")

listbox_files = tk.Listbox(frame_files, width=80, font=custom_font)
listbox_files.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

scrollbar_files = tk.Scrollbar(frame_files, command=listbox_files.yview)
scrollbar_files.pack(side=tk.LEFT, fill=tk.Y)
listbox_files.config(yscrollcommand=scrollbar_files.set)

listbox_parts.bind("<<ListboxSelect>>", get_files_with_selected_part)
listbox_files.bind("<Double-Button-1>", open_selected_file)
listbox_files.bind("<Button-3>", open_selected_directory)

root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)

browse_button.focus()

root.mainloop()
