from client.cli import cli_utils
from src.api.files.file_compare import check_if_equal
from src.api.files.backblaze import B2Interface, application_key, application_key_id, file_rep_bucket, UploadSourceBytes
from urllib.parse import urljoin
from traceback import print_exc

import requests
import subprocess
import os
import time
import pickle
import getpass
import json
import io


file_new_end = '/api/files/new'
file_query_end = '/api/files/query'
group_query_end = '/api/groups/getGroups'
signin_end = '/api/signin'
signup_end = '/api/signup'


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
    v = args_norm['verbose']
        
    # If message is not present then open the default editor
    args_norm["message"] = handle_message(args, args_norm["verbose"])
    if args_norm["verbose"]:
        print_dict(args_norm["message"])
        print("files:", args_norm["files"])
    
    # Opens all files into files_loaded
    files_loaded = [open(filename, 'rb') for filename in args_norm['files']]
    for file in files_loaded:
        file.seek(0, 2)
        print(file.name + ' size:', file.tell())
    session = requests.session()
    repos: list = get_repo_details(v)
    
    if len(repos) > 0:
        if len(repos) != 1:
            print('Which repo do you want to add to:')
            for r in range(len(repos)):
                repo = repos[r]
                print('\nRepo no. ' + str(r + 1) + ':', str(repo['repo_name']), '(url:', str(repo['url']) + ')')
            line_no = cli_utils.ask_for_list(repos)
            chosen_repo = repos[line_no]
        else:
            chosen_repo = repos[0]
        
        session.cookies.update(chosen_repo['cookie'])
        
        # Gets all groups that the user is a member of
        # This is to choose which group the file should be uploaded to
        # print("blah")
        if v:
            print('Getting: https://' + chosen_repo['url'] + group_query_end)
        groups = requests.Response()
        try:
            groups = session.get('http://' + chosen_repo['url'] + group_query_end)
        except requests.exceptions.ConnectionError:
            groups.status_code = "Connection refused"
        try:
            code = groups.json()['code']
            msg = groups.json()['msg']
            if v:
                print('Returned code:', code)
                print('Returned message:', msg)
            if code == 200:
                groups_returned = groups.json()['rows']
                print('\n\nPlease choose a group to upload to:')
                if len(groups_returned) != 1:
                    for r in range(len(groups_returned)):
                        row = groups_returned[r]
                        print('\n' + str(r + 1) + '\'s group info:', row)
                    chosen_group = groups_returned[cli_utils.ask_for_list(groups_returned)]
                else:
                    chosen_group = groups_returned[0]
            else:
                print(msg + '. Use the "forkie login <repo>" command to login to this repo')
                return
        except Exception as e:
            print("Woops something went wrong while querying groups")
            print(print_exc())
            return
        
        # Use B2Interface to find if there are equal files
        b2_key = chosen_repo['b2']
        interface = B2Interface(b2_key['application_key_id'],
                                b2_key['application_key'],
                                b2_key['bucket_name'])
        for file_open in files_loaded:
            cont_upload = False
            file_open.seek(0, 0)
            filename = os.path.basename(file_open.name)
            file_bytes = UploadSourceBytes(file_open.read())
            if v:
                print('Searching for files identical to ' + filename)
            # ONLY CHECK FILES THAT ARE PART OF THE GROUP THE USER WANTS TO UPLOAD TO
            # 1. Query all the files that belong to groupid
            # 2. Extract all the fileids from the files
            # 3. compare the identical_files fileid's with the extracted id's from the query
            identical_files = interface.checkForEqualFiles(file_bytes.get_content_sha1(), file_bytes.get_content_length(), filename)
            if len(identical_files) > 0:
                print('Found file(s) identical to ' + filename + ':')
                for x in range(len(identical_files)):
                    identical_file = identical_files[x]
                    print(str(x + 1) + '\'s file info:', identical_file.file_info)
                cont_upload = cli_utils.ask_for('Do you still want to start tracking a new file?', ['y', 'n'])
                if not cont_upload:
                    print('Please use "forkie update" to create a new version of the file')
            else:
                if v:
                    print('No identical files found continuing...')
                cont_upload = True
        
            if cont_upload:
                file_open.seek(0, 0)  # Seeks back to the beginning of the file
                files = {'file': file_open}
                if v:
                    print('Posting to: http://' + chosen_repo['url'] + file_new_end)
                upload_status = session.post('http://' + chosen_repo['url'] + file_new_end, files=files, data={'groupid': chosen_group['groupid']})
                if v:
                    print('Upload status:', upload_status)
                # try:
                code = upload_status.json()['code']
                msg = upload_status.json()['msg']
                if v:
                    print('Returned code:', code)
                    print('Returned message:', msg)
                if code == 401:
                    print(msg + '. Use the "forkie login <repo>" command to login to this repo')
                    break
                else:
                    print(msg)
                # except Exception as e:
                #     print(e)
                #     print("Woops something went wrong while trying to upload a file")
    else:
        print("No cookie files found in .forkie")    
    
def update(args: dict):
    """ Handles the 'update' subcommand. If no message option is found or message is empty then a temp file
        will be made and opened with the default editor. After the arguments have been handled then the
        files along with the message are added to the database using the api. Adds a new version of the file to backblaze
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

def find(args: dict):
    """ Queries the every repo registered in the .forkie folder in the current directory for all files 
        or a certain file with a name and a keyword
    """
    # (-a | (-n <name> -k <keyword>)) [(-p <group>)] [-vd] [(-c <comment>) [-f | --force]]
    args_norm = {
        "verbose": False,
        "force": False,
        "all_files": False,
        "name": None,
        "keyword": None,
        "group": None,
        "download": False,
        "comment": None
    }
    # print(args)

    # Check if there's verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    v = args_norm['verbose']
    # Check if there's a force
    args_norm["force"] = check_bool_option(args, "--force")
    # Check for group
    args_norm["group"] = check_string_option(args, "-p", "group")
    # Check for download flag
    args_norm["download"] = check_bool_option(args, "--download")
    # All
    args_norm["all_files"] = check_bool_option(args, "-a")
    # Get comment
    args_norm["comment"] = check_string_option(args, "--comment", "comment")
    # Get name
    args_norm["name"] = check_string_option(args, "--name", "name")
    # Get keyword
    args_norm["keyword"] = check_string_option(args, "--keyword", "keyword")
    if args_norm["verbose"]:
        for arg in args_norm.keys():
            print(str(arg) + ": " + str(args_norm[arg]))
            
    # Return the files with the given criteria using the file_query API
    query_json = {}
    if not args_norm['all_files']:
        if args_norm['group'] is not None:
            query_json['groupname'] = args_norm['group']
        if args_norm['name'] is not None:
            query_json['filename'] = args_norm['name']
    
    # Get query
    found_rows = True
    session = requests.session()
    repos: list = get_repo_details(v)
    files_queried = []
    
    if len(repos) != 0:
        # Iterate through all repos and query and display them
        offset = 0
        for r in range(len(repos)):
            repo = repos[r]
            print('\n\n' + str(r + 1) + '. Repo name:', str(repo['repo_name']), '(url:', str(repo['url']) + ')')
            session.cookies.update(repo['cookie'])
            returned = session.post('http://' + repo['url'] + file_query_end, json=query_json)
            code = returned.json()['code']
            msg = returned.json()['msg']
            if v:
                print('Query JSON:', query_json)
                print('Returned JSON:', returned.json())
            if code == 200:
                if 'rows' in returned.json():
                    rows = returned.json()['rows']
                    files_queried.extend(rows)
                    if len(rows) != 0:
                        found_rows = True
                        for row in range(len(rows)):
                            print('\t' + str(offset + row + 1) + ':', rows[row])
                        offset += len(rows)
                    else:
                        print('No files found')
                else:
                    print('Something went wrong with querying your files')
            else:
                print(msg)
    else:
        print("No cookie files found in .forkie")

    # If download then display a custom context to select the file to download from the query
    if args_norm['download'] and found_rows:
        print('Which repo do you want to download from? ', end='')
        repo_num = cli_utils.ask_for_list(repos)
        print('Which file do you want to download? ', end='')
        row_num = cli_utils.ask_for_list(files_queried)
        b2_key = repos[repo_num]['b2']
        interface = B2Interface(b2_key['application_key_id'],
                                b2_key['application_key'],
                                b2_key['bucket_name'])
        chosen_file = files_queried[row_num]
        print('\n\nHere are all the versions for ' + chosen_file['filename'] + ":")
        for v in range(len(chosen_file['versions'])):
            version = chosen_file['versions'][v]
            print(str(v + 1) + '.', version)
        print('Which version of the file do you want to download? ', end='')
        version_num = cli_utils.ask_for_list(chosen_file['versions'])
        print('\nDownloading...')
        file_info = interface.downloadFileByVersionId(chosen_file['versions'][version_num]['versionid'])
        file_data = bytes(file_info['file_body'])
        filename = file_info['filename']
        # At this point decode file data and save locally. At some point do something to output
        with open(filename, 'wb') as f:
            f.write(file_data)
        f.close()
        print('Done!')

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
    if v:
        print("Trying to access " + args_norm["repo"])
        
    # Check if .forkie directory exists
    if not os.path.exists(".forkie"):
        # Create .forkie dir
        os.makedirs(".forkie")

    # Check if the server cookie file exists
    hostname = cli_utils.find_hostname(args_norm["repo"])
    forkie_cookies = os.path.join(".forkie/" + hostname, hostname + ".bin")
    b2_path = os.path.join('.forkie/' + hostname, 'b2.json')
    if v:
        print("Cookie will be written to:", forkie_cookies)

    if hostname is not None:
        if os.path.exists(forkie_cookies) and os.path.isfile(forkie_cookies):
            print("Repository cookie already exists in .forkie. No need to login")
        else:
            # Ask user to login
            signin_path = urljoin(repo, signin_end)
            signup_path = urljoin(repo, signup_end)
            done = False
            cont = False
            login = {
                "email": "",
                "password": ""
            }
            headers = {"Content-Type": "application/json"}
            session = requests.session()

            while not done:
                login = get_emailandpass(login)

                signin = session.post(signin_path, json=login, headers=headers)
                msg = str(signin.json()["msg"])
                if v:
                    print("Signin_path:", signin_path)
                    print("Signup_path:", signup_path)
                    print("Status code:", signin.status_code)
                    print("Response:", msg)
                # Check for 400
                if signin.status_code == 400:
                    signup_answer = cli_utils.ask_for(msg + ". Do you want to signup?", ["y", "n"])
                    if signup_answer:
                        # Keep the email and pass from signin
                        if cli_utils.ask_for("Do you want to enter a new email and password?", ["y", "n"]):
                            login = get_emailandpass(login)
                        login["username"] = str(input("Enter a username: "))
                        # Will keep checking if user wants to sign up or if error 401 otherwise break
                        while True:
                            signup = session.post(signup_path, json=login, headers=headers)
                            msg = str(signup.json()["msg"])
                            if signup.status_code == 401:
                                # If email already exists
                                signup_answer = cli_utils.ask_for(msg + " Do you want to try again?", ["y", "n"])
                                if not signup_answer:
                                    break
                            else:
                                break
                        cont = True
                        if v:
                            print("JSON returned:", signup.json)
                        if signup.status_code in [400, 500]:
                            print(msg + ". Try again another time.")
                            cont = False
                        done = True
                    else:
                        done = not cli_utils.ask_for("Do you want to try again?", ["y", "n"])
                elif signin.status_code in [500, 403]:
                    done = not cli_utils.ask_for(msg + " Try again?", ["y", "n"])
                    cont = False
                else:
                    if v:
                        print(msg)
                        done = True
                        cont = True
                    if 'b2' in signin.json():
                        b2_app_key = signin.json()['b2']
                    else:
                        b2_app_key = None
                        
            if cont:
                # Create cookie file folder 
                os.makedirs(os.path.dirname(forkie_cookies))
                with open(forkie_cookies, 'wb') as f:
                    pickle.dump(session.cookies, f)
                f.close()
                # Create b2.json file to store application keys
                if b2_app_key is not None:
                    with open(b2_path, 'w+') as app_key:
                        json.dump(b2_app_key, app_key)
                    app_key.close()
                if v:
                    print("Created " + hostname + " cookie file in .forkie/" + hostname)
    else:
        print("Error 404: That repository does not exist")
    
def print_dict(args: dict):
    for arg in args.keys():
        print(str(arg) + ": " + str(args[arg]))
        
def get_emailandpass(login: dict) -> dict:
    login["email"] = str(input("Enter email: "))
    login["password"] = str(getpass.getpass(prompt="Enter password: "))
    return login

def get_repo_details(v: bool) -> list:
    """ Gets the list of repositories in the .forkie folder and returns a dict with the binary cookies
        and url for all available repos
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