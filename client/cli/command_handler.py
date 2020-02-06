from client.cli import cli_utils
from src.files.file_compare import check_if_equal
from urllib.parse import urljoin
import requests
import subprocess
import os
import time
import pickle


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
    args_norm = {
        "verbose": False,
        "files": args["<file>"]
    }

    # Check if theres verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
        
    # If message is not present then open the default editor
    args_norm["message"] = handle_message(args, args_norm["verbose"])
    if args_norm["verbose"]:
        print_dict(args_norm["message"])
        print("files:", args_norm["files"])
    
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
    args_norm = {
        "verbose": False,
        "keyword": None,
        "files": args["<file>"]
    }
    # print(args)

    # Check if theres verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    # Check for keyword
    args_norm["keyword"] = check_string_option(args, "--keyword", "keyword")
    # If message is not present then open the default editor
    args_norm["message"] = handle_message(args, args_norm["verbose"])
    if args_norm["verbose"]:
        print_dict(args_norm["message"])
        print("files:", args_norm["files"])
        if args_norm["keyword"] is not None:
            print("keyword:", args_norm["keyword"])
    
    # Check all files to see if theres another one that is identical.
    # Find all files containing keyword if there is one or keyword + name. Output a selection choice for the user
    # where they select the files to update. This needs API functions. Remeber to update metadata

def find(args: dict):
    """ Queries the database for all files or a certain file with a name and a keyword
    """
    # (-a | (-n <name> -k <keyword>)) [-p <group>] [-v | --verbose] [-c <comment> [-f | --force]]
    args_norm = {
        "verbose": False,
        "force": False,
        "all_files": False,
        "keyword": None,
        "group": None,
        "comment": None
    }

    # Check if there's verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    # Check if there's a force
    args_norm["force"] = check_bool_option(args, "--force")
    # Check for group
    args_norm["group"] = check_string_option(args, "-p", "group")
    # All
    args_norm["all_files"] = check_bool_option(args, "-a")
    # Get comment
    args_norm["comment"] = check_string_option(args, "--comment", "comment")
    # Get keyword
    args_norm["keyword"] = check_string_option(args, "--keyword", "keyword")
    if args_norm["verbose"]:
        if args_norm["group"] is not None:
            print("group:", args_norm["group"])
        if args_norm["comment"] is not None:
            print("comment: \"" + args_norm["comment"] + "\" (force: " + str(args_norm["force"]) + ")")
        if args_norm["keyword"] is not None:
            print("keyword: \"" + args_norm["keyword"] + "\"")
            
    # Return the files with the given criteria using the database API

def archive(args: dict):
    """ Queries database for archived files or manually archives files not accessed in the past year
    """
    # [-V [(-a | (-k <keyword>))] [-p <group>]] [-vf]
    args_norm = {
        "verbose": False,
        "force": False,
        "all_files": False,
        "view": False,
        "keyword": None,
        "group": None,
    }
    
    # Check if there's verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    # Check if there's a force
    args_norm["force"] = check_bool_option(args, "--force")
    # Check if there's a view
    args_norm["view"] = check_bool_option(args, "--view")
    # Check for group
    args_norm["group"] = check_string_option(args, "-p", "group")
    # All
    args_norm["all_files"] = check_bool_option(args, "-a")
    # Get keyword
    args_norm["keyword"] = check_string_option(args, "--keyword", "keyword")
    if args_norm["verbose"]:
        if args_norm["group"] is not None:
            print("group:", args_norm["group"])
        if args_norm["keyword"] is not None:
            print("keyword: \"" + args_norm["keyword"] + "\"")

def group(args: dict):
    """ View all groups or just peeps and filter by email. Add person to group. Remove person from group. Change person from one group to another.
        All users can access the view commands but only users with group leader or admin positions can access the editing commands. This is done by
        querying the correct tables
    """
    # (-V [--peeps] [<email>...] | --add [-p <group>] (<email>...) | --rm [-p <group>] (<email>...) | --change (-p <group>) (<email>...)) [-vf]
    print(args)

def report(args: dict):
    """ Generate report on everything or an individual group or person. A report is a PDF which is generated from a markdown file and output to a 
        specific location if the -o option is specified
    """
    # (-a | (-p <group> | <email>)) [(-o <file>)] [-v | --verbose]
    print(args)

def login(args: dict):
    """ Logs into the given forkie repository at the given address, this creates a .forkie folder in the current directory which will store the
        cookie returned from the sigin endpoint of the forkie repo. THIS COOKIE HAS TO BE UPDATED EVERY TIME A REQUEST IS MADE TO THE SERVER
    """
    # (<repo>) [-v | --verbose]
    args_norm = {
        "verbose": False,
        "repo": args["<repo>"]
    }
    
    # Check if there's verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    v = args_norm["verbose"]
    repo = args_norm["repo"]
    if args_norm["verbose"]:
        print("Trying to access " + args_norm["repo"])
        
    # Check if .forkie directory exists
    if not os.path.exists(".forkie"):
        # Create .forkie dir
        os.makedirs(".forkie")

    # Check if the server cookie file exists
    hostname = cli_utils.find_hostname(args_norm["repo"])
    if hostname is not None:
        if os.path.exists(hostname) and os.path.isfile(hostname):
            if v:
                print("Repository cookie already exists in .forkie. No need to login")
        else:
            # Ask user to login
            signin_path = urljoin(repo, "/signin")
            signup_path = urljoin(repo, "/signup")
            done = False
            cont = False
            login = {
                "email": "",
                "password": "",
                "client": "cli"
            }
            session = requests.session()

            while not done:            
                login["email"] = str(input("Enter email: "))
                login["password"] = str(input("Enter password: "))
                
                signin = session.get(signin_path)
                msg = signin.json()["msg"]
                # Check for 400
                if signin.status_code == "400":
                    signup_answer = cli_utils.ask_for(msg + ". Do you want to signup?", ["y", "n"])
                    if signup_answer:
                        # Will keep checking if user wants to sign up or if error 401 otherwise break
                        signup = session.get(signup_path)
                        while signup.status_code == "401":
                            # If email already exists
                            signup_answer = cli_utils.ask_for(msg + " Do you want to try again?", ["y", "n"])
                            if not signup_answer:
                                break
                            signup = session.get(signup_path)
                        cont = True
                        if signup.status_code == "500":
                            print(msg + ". Trying again...")
                            cont = False
                        done = True
                    else:
                        done = not cli_utils.ask_for("Do you want to try again?", ["y", "n"])
                elif signin.status_code in ["500", "403"]:
                    done = not cli_utils.ask_for(msg + " Try again?", ["y", "n"])
                    cont = False
                else:
                    if v:
                        print(msg)
                        
            if cont:
                # Create cookie file
                with open(hostname + ".bin", 'wb') as f:
                    pickle.dump(session.cookies, f)
    else:
        print("Error 404: That repository does not exist")
    
def print_dict(args: dict):
    for arg in args.keys():
        print(str(arg) + ": " + str(args[arg]))