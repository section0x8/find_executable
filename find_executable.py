#!/usr/bin/env python

from sys import version_info

if not (version_info.major >= 3 and version_info.minor >= 7):
    print("Error: Python 3.7 or higher required.")
    quit(1)

from pathlib import Path
from subprocess import run, PIPE

g_file_list = []
g_result_list = []

class ExecutableFile:

    def __init__(self, filepath):
        self.filename = filepath.name
        self.filepath = filepath.resolve()
        self.functions = self._get_functions()
        self.libraries = self._get_libraries()
    
    @classmethod
    def create(cls, filepath):
        if filepath.is_file():
            try:
                with open(filepath, "rb") as f:
                    data = f.read(4)
                if data == b'\x7f\x45\x4c\x46':
                    return cls(filepath)
            except:
                print("Warning: unable to open file", filepath)

        return None

    def _get_functions(self):
        cmd = ["nm", "-D", self.filepath]
        cp = run(cmd, capture_output=True)
        output = cp.stdout.strip()
        output = [str(line, "ascii").strip().split()[-1] for line in output.split(b'\n')]
        return output

    def _get_libraries(self):
        cmd = ["objdump", "-p", self.filepath]
        cp = run(cmd, capture_output=True)
        output = cp.stdout.strip()
        output = [ str(line, "ascii").strip().split()  for line in output.split(b'\n')]
        libraries = []
        for line in output:
            if len(line) == 2 and line[0] == "NEEDED":
                libraries.append(line[1])
        return libraries

    def __str__(self):
        output = ""
        output += "File Name: {}\nFile Path: {}\nFunctions:\n".format(self.filename, self.filepath)
        for function in self.functions:
            output += "\t{}\n".format(function)
        output += "Libraries:\n"
        for library in self.libraries:
            output += "\t{}\n".format(library)
        return output

def enumerate_files(filepath):
    
    global g_file_list
    # Clean up. No idea why. Python 
    # memory usage just bugs me.
    if isinstance(g_file_list, list):
        g_file_list.clear()

    g_file_list = []
     
    if filepath.is_file():
        ef = ExecutableFile.create(filepath)
        if ef is not None:
            g_file_list.append(ef)
    elif filepath.is_dir():
        for child in filepath.rglob("*"):
            if child.is_file():
                ef = ExecutableFile.create(child)
                if ef is not None:
                    g_file_list.append(ef)

def check_file_path(p):
    # Get a list of ExecutableFile objects.
    filepath = Path(p).resolve()
    if not filepath.exists():
        print("Error: file or path does not exist.")
        return False
    if filepath.is_file() or filepath.is_dir():
        return True
    else:
        print("Error: invalid file or path.")
        return False

def search(strict_mode, search_mode):
    
    global g_file_list
    global g_result_list

    if g_file_list == None:
        return False
    
    if len(g_file_list) == 0:
        print("Error: please use 'Set file path' to load files to search.")
        return False

    search_type = 0
    found = False

    print("1. File name search.")
    print("2. Function name search.")
    print("3. Library name search.")
    choice = input("> ")
    
    if choice == "1":
        search_type = 1
    elif choice == "2":
        search_type = 2
    elif choice == "3":
        search_type = 3
    else:
        print("Error: invalid search type.")
        return False
    
    keyword = input("Search: ")

    # If strict search then we will look for an exact match.
    # if not then we will do a case insensitive *keyword* search.
    
    # Depending on the search mode we will be searching through either 
    # the main list or the result list.
    if search_mode == 1:
        g_result_list.clear()

    for ef in g_file_list:
        # File name search
        if search_type == 1:
            if strict_mode:
                if ef.filename == keyword:
                    found = True
            else:
                if keyword.lower() in ef.filename.lower():
                    found = True
        elif search_type == 2:
            for function in ef.functions:
                if strict_mode:
                    if function == keyword:
                        found = True
                else:
                    if keyword.lower() in function.lower():
                        found = True
        elif search_type == 3:
            for library in ef.libraries:
                if strict_mode:
                    if keyword == library:
                        found = True
                else:
                    if keyword.lower() in library.lower():
                        found = True
        if found:
            found = False
            if ef not in g_result_list:
                g_result_list.append(ef)
                print("Match found:", ef.filename)

def print_file_list(verbose=False):

    global g_file_list

    for ef in g_file_list:
        if verbose:
            print(ef)
        else:
            print(ef.filename)

def print_result_list(verbose=False):
    
    global g_result_list

    for ef in g_result_list:
        if verbose:
            print(ef)
        else:
            print(ef.filename)

def save_results():
    
    global g_result_list

    try:
        location = Path(input("Path: "))
    except:
        print("Error: invalid path")
        return False
    if location.is_dir():
        try:
            filename = Path(input("Filename: "))
        except:
            print("Error: invalid value entered.")
            return False
        fullpath = location.joinpath(filename)
        with open(fullpath, "w+") as f:
            for ef in g_result_list:
                f.write(str(ef))
                f.write("\n")
    else:
        with open(location, "w+") as f:
            for ef in g_result_list:
                f.write(str(ef))
                f.write("\n")
    return True


def save_files():

    global g_result_list

    try:
        location = Path(input("Folder: "))
    except:
        print("Error: invalid path.")
        return False
    
    fullpath = None
    
    if location.is_dir():
        fullpath = location
    elif not location.exists():
        try: 
            location.mkdir(parents=True)
        except:
            print("Error: could not create directory.")
            return False
        fullpath = location
    else:
        print("Error: please enter either an existing or folder name to create.")
        return False
    
    if fullpath == None:
        print("Error: fullpath should not be None")
        return False

    for ef in g_result_list:
        src = ef.filepath
        dst = fullpath.joinpath(ef.filename)
        dst.write_bytes(src.read_bytes())

    return True

def main():

    running = True
    strict_mode = False
    search_mode = 1

    # Interactive search menu.
    while running:
        print("\nExecutable Finder")
        print("-----------------\n")
        print("1. Search.")
        print("2. Set strict mode.")
        print("3. Set file path.")
        print("4. Set search mode.")
        print("5. Print executable files.")
        print("6. Print results.")
        print("7. Save results.")
        print("8. Clear Results.")
        print("9. Save Files.")
        print("0. Exit.")
        choice = input("> ")
        print("\n")
        if choice == "1":
            search(strict_mode, search_mode)
        elif choice == "2":
            strict_mode = not strict_mode
            print("Info: strict mode set to", strict_mode)
        elif choice == "3":
             choice = input("Enter file path: ")
             if check_file_path(choice):
                 print("Info: setting file path to", choice)
                 filepath = choice
                 enumerate_files(Path(filepath))
                 print("Info: Found {} files.".format(len(g_file_list)))
        elif choice == "4":
            print("1. Regular search. (Every search yields new results.)")
            print("2. Incremental search. (Every search appends to results.)")
            try:
                choice = int(input("> "), 10)
                print("\n")
                if choice > 0 and choice <= 2:
                    search_mode = choice
                    print("Search mode set to", search_mode)
                else:
                    raise ValueError
            except:
                print("\nError: invalid search mode.")
        elif choice == "5":
            print("1. Summary.")
            print("2. Detail.")
            choice = input("> ")
            if choice == "1":
                print_file_list()
            elif choice == "2":
                print(print_file_list(True))
            else:
                print("Error: invalid choice.")
        elif choice == "6":
            print("1. Summary.")
            print("2. Detail.")
            choice = input("> ")
            if choice == "1":
                print_result_list()
            elif choice == "2":
                print(print_result_list(True))
            else:
                print("Error: invalid choice.")
        elif choice == "7":
            save_results()
        elif choice == "8":
            g_result_list.clear()
        elif choice == "9":
            save_files()
        elif choice == "0":
            running = False
        else:
            print("Error: invalid choice.")


if __name__ == "__main__":
    main()
