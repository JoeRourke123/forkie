from src.api.files.file_compare import check_if_equal
from client import cli_utils
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration

import getpass
import requests
import copy
import pickle
import time
import json
import os

file_query_end = '/api/files/query'

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

def print_dict(args: dict):
    """ Prints dictionaries in 'key: value' format 
        - args: dict to print
    """
    for arg in args.keys():
        print(str(arg) + ": " + str(args[arg]))
        
def get_emailandpass(login: dict) -> dict:
    """ Asks for user email and pass input. Uses the getpass package to handle the invisible pass input 
        - login: the dictionary to populate with the email and pass
    """
    login["email"] = str(input("Enter email: "))
    login["password"] = str(getpass.getpass(prompt="Enter password: "))
    return login

def get_repo_details(v: bool) -> list:
    """ Gets the list of repositories in the .forkie folder and returns a dict with the binary cookies
        and url for all available repos
        -v: verbose
    """
    repos = []
    if not os.path.exists(".forkie"):
        print(".forkie directory does not exist try logging in")
    else:
        directories = [name for name in os.listdir('./.forkie') if os.path.isdir(os.path.join('.forkie', name))]
        for directory in directories:
            # Read the cookie bin
            current_repo = {}
            current_dir = os.path.join('.forkie', directory)
            cookie_file_path = os.path.join(current_dir, directory + '.bin')
            b2_file_path = os.path.join(current_dir, 'b2.json')
            current_repo['repo_name'] = directory
            with open(cookie_file_path, 'rb') as f:
                current_repo['cookie'] = pickle.load(f)
            f.close()
            # Get the url from the list of domains inside the cookie
            current_repo_url = current_repo['cookie'].list_domains()[0]
            if current_repo_url == '0.0.0.0':
                current_repo_url += ':5000'
            current_repo['url'] = current_repo_url
            # Get B2 bucket info from b2.json
            if v:
                print('Cookies:', cookie_file_path)
                print('B2 keys:', b2_file_path)
            if os.path.exists(b2_file_path) and os.path.isfile(b2_file_path):
                with open(b2_file_path) as b2:
                    current_repo['b2'] = json.load(b2)
                b2.close()
            repos.append(current_repo)

    return repos

def query_allrepos(query_json: dict, session: requests.Session, repo: dict, v: bool, p: bool, r: int, offset: int):
    """ Queries a repo with the file query endpoint. Usually called from a loop through all repos
        - query_json: the json to post to the endpoint
        - session: the requests session object containing the user cookies
        - repo: the dict containing the current repo details
        - v: verbose
        - p: whether to print
        - r: the current repo (used for print)
        - offset: the int offset of files (used so that file no. continues from last repo)
    """
    files_queried = []
    found_rows = False
    formatted_rows = []
    return_offset = 0
    if p:
        print('\n\n' + str(r + 1) + '. Repo name:', str(repo['repo_name']), '(url:', str(repo['url']) + ')')
    session.cookies.update(repo['cookie'])
    try:
        returned = session.post('http://' + repo['url'] + file_query_end, json=query_json)
        try:
            code = returned.json()['code']
            msg = returned.json()['msg']
        except Exception:
            print('Something went wrong when querying for ' + str(repo['repo_name']))
            return False, None, 0

        if v and p:
            print('Query JSON:', query_json)
        if code == 200:
            if 'rows' in returned.json():
                if len(returned.json()['rows']) != 0:
                    found_rows = True
                    files_queried = returned.json()['rows']
                    if p:
                        if v:
                            print('Returned rows (raw):', returned.json()['rows'], '\n')
                        formatted_rows = returned.json()['rows'][:]
                        print(format_file_rows(formatted_rows, offset))
                    return_offset = len(returned.json()['rows'])
                else:
                    if p:
                        print('No files found')
            else:
                if p:
                    print('Something went wrong with querying your files')
        else:
            if p:
                print(msg)
        return found_rows, files_queried, return_offset
    except requests.ConnectionError:
        if p:
            print('COULD NOT CONNECT TO THIS REPO')
        return False, None, 0

def format_file_rows(formatted_rows: list, offset: int) -> str:
    """ Formats the rows returned from the file query endpoint to be in a pretty tabulated format 
        - formatted_rows: input data
        - offset: the offset at which to start the file numbering
    """
    formatted_rows = copy.deepcopy(formatted_rows)
    for row in formatted_rows:
        group_name_list = []
        for group in row['groups']:
            group_name_list.append(group['groupname'])
        row['belongs to'] = ', '.join(group_name_list)
        versions = len(list(row['versions'].keys()))
        row['no. of versions'] = versions

    formatted_rows = cli_utils.delete_listdict_keys(formatted_rows, ['groups', 'versions', 'versionorder'])
    headers = list(formatted_rows[0].keys())
    headers.insert(0, 'file no.')
    return cli_utils.format_rows(headers, [[data['fileid'], data['filename'], data['extension'], data['belongs to'], data['no. of versions']] for data in formatted_rows], offset)

# Copied from src.api.report.utils to avoid weird setuptools things for CLI
# From weazyprint docs (https://weasyprint.readthedocs.io/en/latest/tutorial.html#instantiating-html-and-css-objects)
def generatePdfFromHtml(html: str, outputPath: str, cssPath: str = None):
    """ Generates a pdf from a given html string and outputs to the specified path. Will also include css style if specified
        - Uses: weazyprint
        _ html: given html string to convert and save to pdf
        - outputPath: the path at which to save pdf
        - cssPath: if specified, will add the css from the given path to the pdf doc
    """
    font_config = FontConfiguration()
    html = HTML(string=html)
    css = CSS(string=open(cssPath, "r").read(), font_config=font_config) if cssPath is not None else None

    html.write_pdf(
        outputPath, 
        stylesheets=[css] if css is not None else None,
        font_config=font_config
    )