from client.cli import cli_utils
from src.files.file_compare import check_if_equal
import subprocess
import os
import time


def check_bool_option(args: dict, option: str) -> bool:
    """ Check if theres a boolean option with the given name
        - args: the args to check for the option
        - option: the name of the option to check for
        - return: whether option is True or False
    """
    try:
        return args[option] > 0 if type(args[option]) == int else args[option]
    except KeyError:
        return False
    
def check_string_option(args: dict, option: str, arg: str) -> str:
    """ Check if theres a boolean option with the given name
        - args: the args to check for the option
        - option: the name of the option to check for
        - return: whether the string that follows the option or None if not found
    """
    try:
        equal = False if type(args[option]) == bool else 0
        if args[option] != equal:
            if args["<" + arg + ">"] != "":
                return args["<" + arg + ">"] 
    except KeyError:
        return None

def handle_message(args: dict, verbose: bool) -> dict:
    """ Handles the message if no message option is specified in make and update subcommands
        - args: the dictionary of arguments from the input command
        - verbose: whether or not the verbose option was included in the args or not
        - return: dictionary of the message where 'title' is the title of the message and 'description' is the description
    """
    # Template used in temporary message files to explain to the user that they need to add a
    # message in order to add the file
    tmp_msg_body: str = "\n# Please write a name and description of this add in the line above.\n# If no message is added then you will not be able to add the files you wanted to.\n# The general overview should be written on the first line and more in depth descriptions on the third.\n# DO NOT REMOVE OR EDIT ANY OF THE TEXT STARTING WITH '#'"
    tmp_msg_lines: int = tmp_msg_body.count("\n")
    message: dict = {}
    
    try:
        if args["<message>"] == "":
            raise KeyError
        else:
            message["description"] = args["<message>"]
            if verbose:
                print("Message defined in command: " + message["description"])
    except KeyError:
        if verbose:
            print("Message NOT defined in command starting default editor")
        tmp_file_path = os.path.join(os.getcwd(), "message.txt")
        # Will generate a new temp message filename if a file with that name already exists
        while os.path.exists(tmp_file_path) and os.path.isfile(tmp_file_path):
            tmp_file_path = os.path.join(os.path.dirname(tmp_file_path), os.path.splitext(tmp_file_path)[0] + "_tmp.txt")
        
        changed = False
        message_complete = False
        
        # Create tmp message file then open it in default editor. Then check if there were changes made to the message file
        while not message_complete:
            cli_utils.create_file_incwd(os.path.basename(tmp_file_path), tmp_msg_body)
            while not changed:
                # Opens the default editor for text files and waits for it to exit before opening another
                process = cli_utils.open_default_editor(tmp_file_path).wait()
                message_file = open(tmp_file_path, "rb").read()
                if not check_if_equal(bytearray(tmp_msg_body, "utf-8"), message_file):
                    changed = True
            with open(tmp_file_path, "r") as mf:
                mf_lines = mf.readlines()
                if len(mf_lines) >= tmp_msg_lines:
                    # If the template and the read message have equal line length then the user just input the title
                    message["title"] = mf_lines[0]
                    if len(mf_lines) > tmp_msg_lines + 1:
                        # Title and description with newline seperating them
                        message["description"] = ""
                        for line in range(2, len(mf_lines) - tmp_msg_lines):
                            message["description"] += mf_lines[line]
                    message_complete = True
                else:
                    print("Don't delete the template message (any text with #)")
            mf.close()
            # Delete temp message file. Sleep is kinda jank
            time.sleep(3)
            os.remove(tmp_file_path)
    return message

def make(args: dict):
    """ Handles the 'make' subcommand. If no message option is found or message is empty then a temp file
        will be made and opened with the default editor. After the arguments have been handled then the
        the database is searched for files with the same names as the files given and the given keyword (if there was one).
        The user can then select the files they want to update 
        - args: the args passed in from forkie.py
    """
    # [-v | --verbose] [(-m <message>)] (<file>)...
    verbose = False
    files: list = args["<file>"]

    # Check if theres verbose
    verbose = check_bool_option(args, "--verbose")
        
    # If message is not present then open the default editor
    message = handle_message(args, verbose)
    if verbose:
        print_dict(message)
        print("files:", files)
    
    # Check all files to see if theres another one that is identical. If there is prompt
    # the user if they want to use the 'update' subcommand instead. Call API functions 
    # to add this file/files to the database remember to also add metadata and generate 
    # the hash for the fileVersionTable.
    
def update(args: dict):
    """ Handles the 'update' subcommand. If no message option is found or message is empty then a temp file
        will be made and opened with the default editor. After the arguments have been handled then the
        files along with the message are added to the database using the api
        - args: the args passed in from forkie.py
    """
    # [-v | --verbose] [(-m <message>)] [(-k <keyword>)] (<file>)...
    verbose = False
    keyword: str
    files: list = args["<file>"]
    # print(args)

    # Check if theres verbose
    verbose = check_bool_option(args, "--verbose")
    # Check for keyword
    keyword = check_string_option(args, "--keyword", "keyword")
    # If message is not present then open the default editor
    message = handle_message(args, verbose)
    if verbose:
        print_dict(message)
        print("files:", files)
        if keyword is not None:
            print("keyword:", keyword)
    
    # Check all files to see if theres another one that is identical.
    # Find all files containing keyword if there is one or keyword + name. Output a selection choice for the user
    # where they select the files to update. This needs API functions. Remeber to update metadata

def find(args: dict):
    """ Queries the database for all files or a certain file with a name and a keyword
    """
    # (-a | (-n <name> -k <keyword>)) [-p <group>] [-v | --verbose] [-c <comment> [-f | --force]]
    verbose: bool = False
    force: bool = False
    keyword: str
    group: str
    comment: str

    # Check if there's verbose
    verbose = check_bool_option(args, "--verbose")
    # Check if there's a force
    force = check_bool_option(args, "force")
    # Check for group
    group = check_string_option(args, "-p", "group")
    # All
    all_files = check_bool_option(args, "-a")
    # Get comment
    comment = check_string_option(args, "--comment", "comment")
    if verbose:
        if group is not None:
            print("group:", group)
        if comment is not None:
            print("comment: \"" + comment + "\" (force: " + str(force) + ")")
            
    # Return the files with the given criteria using the database API

def archive(args: dict):
    print(args)

def group(args: dict):
    print(args)

def report(args: dict):
    print(args)

def login(args: dict):
    print(args)
    
def print_dict(args: dict):
    for arg in args.keys():
        print(str(arg) + ": " + str(args[arg]))