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
import copy


file_new_end = '/api/files/new'
file_new_version_end = '/api/files/newVersion'
file_query_end = '/api/files/query'
group_query_end = '/api/groups/getGroups'
signin_end = '/api/signin'
signup_end = '/api/signup'
bulk_comment_end = '/api/comment/bulkComment'


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
    if v:
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
                    headers = list(groups_returned[0].keys())
                    headers.sort()
                    headers.insert(0, 'file no.')
                    values = [list(data.values()) for data in groups_returned]
                    print(cli_utils.format_rows(headers, values))
                    chosen_group = groups_returned[cli_utils.ask_for_list(groups_returned)]
                else:
                    print('Only one group found (' + groups_returned[0]['groupname'] + ') so using that one')
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
            identical_files = interface.getEqualFilesList(file_bytes.get_content_sha1(), file_bytes.get_content_length(), filename)
            # 1. Query all the files that belong to groupid
            file_group = requests.Response()
            try:
                file_group = session.post('http://' + chosen_repo['url'] + file_query_end, json={'groupid': chosen_group['groupid']})
            except requests.exceptions.ConnectionError:
                file_group.status_code = "Connection refused"
            try:
                code = file_group.json()['code']
                msg = file_group.json()['msg']
                if v:
                    print('Returned code:', code)
                    print('Returned message:', msg)
                if code == 200:
                    files_returned = file_group.json()['rows']
                else:
                    print(msg + '. Use the "forkie login <repo>" command to login to this repo')
                    return
            except Exception as e:
                print("Woops something went wrong while querying groups")
                print(print_exc())
                return

            # 2. Extract all the fileids from the files
            # 3. compare the identical_files fileid's with the extracted id's from the query
            files_for_user = []
            for file in identical_files:
                for fileid in files_returned:
                    if file.file_info['fileid'] == fileid['fileid']:
                        files_for_user.append(file)

            if len(files_for_user) > 0:
                print('Found file(s) identical to ' + filename + ':')
                file_dicts = [dict(file.file_info) for file in files_for_user]
                headers = list(file_dicts[0].keys())
                headers.sort()
                headers.insert(0, 'file no.')
                values = [list(data.values()) for data in file_dicts]
                print(cli_utils.format_rows(headers, values))
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
                upload_status = requests.Response()
                try:
                    upload_status = session.post(
                        'http://' + chosen_repo['url'] + file_new_end,
                        files=files,
                        data={
                            'groupid': chosen_group['groupid'],
                            'comment': args_norm['message']['description']
                        }
                    )
                except requests.exceptions.ConnectionError:
                    upload_status.status_code = "Connection refused"
                if v:
                    print('Upload status:', upload_status)
                try:
                    code = upload_status.status_code
                    if v:
                        print('Returned code:', code)
                    if code == 401:
                        print('Use the "forkie login <repo>" command to login to this repo')
                        break
                    else:
                        print('Upload successful')
                except Exception as e:
                    print("Woops something went wrong while trying to upload a file")
    else:
        print("No cookie files found in .forkie")
    
def update(args: dict):
    """ Handles the 'update' subcommand. If no message option is found or message is empty then a temp file
        will be made and opened with the default editor. After the arguments have been handled then the
        files along with the message are added to the database using the api. Adds a new version of the file to backblaze
        - args: the args passed in from forkie.py
    """
    # [-v | --verbose] [(-m <message>)] (<file>)...
    args_norm = {
        "verbose": False,
        "files": args["<file>"]
    }
    # print(args)

    # Check if theres verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    v = args_norm['verbose']
    # If message is not present then open the default editor
    args_norm["message"] = handle_message(args, args_norm["verbose"])
    if args_norm["verbose"]:
        print_dict(args_norm["message"])
        print("files:", args_norm["files"])

    session = requests.session()
    repos: list = get_repo_details(v)

    # Get all the files queried by the filename from the passed file arg
    found_rows = False
    session = requests.session()
    repos: list = get_repo_details(v)
    query_json = {}

    if len(repos) != 0:
        offset = 0
        all_queriedfiles = []
        for r in range(len(repos)):
            repo = repos[r]
            files_rep = []
            rep_offset = 0
            
            # Query all filenames from the repo
            for filename in args_norm['files']:
                filename = os.path.basename(filename)
                query_json['filename'] = filename
                found_rows_current = False
                found_rows_current, files_queried, rep_offset = query_allrepos(query_json, session, repo, v, False, r, offset)
                found_rows = found_rows_current if found_rows_current else found_rows
                files_rep.extend(files_queried[:])
                # print(all_queriedfiles)

            # Display all queried files
            print('\n\n' + str(r + 1) + '. Repo name:', str(repo['repo_name']), '(url:', str(repo['url']) + ')')
            if len(files_rep) != 0:
                # Unfortunately there needs to be a deepcopy in here to stop the format function from breaking everything
                print(format_file_rows(files_rep, offset))
            else:
                print('No file(s) of the requested filename(s) found in this repository')
            all_queriedfiles.append(files_rep[:])
            offset += len(files_rep)
    else:
        print("No cookie files found in .forkie")

    if found_rows:
        print('\n\nUpdating...')
        while True:
            print('Which repo contains the file(s) to update? ', end='')
            repo_num = cli_utils.ask_for_list(repos)
            if len(all_queriedfiles[repo_num]) != len(args_norm['files']):
                print('Repo doesn\'t contain:')
                not_contains = args_norm['files'].copy()
                for filename in all_queriedfiles[repo_num]:
                    filename = filename['filename']
                    if filename in not_contains:
                        not_contains.remove(filename)
                [print(row) for row in not_contains]
                # Ask the user if they still want to continue. 
                if not cli_utils.ask_for('Do you want to choose another repo?', ['y', 'n']):
                    print('Ignoring files that aren\'t contained inside repo...')
                    # Remove the files that aren't contained so that later only the files that exist are loaded
                    for filename in not_contains:
                        args_norm['files'].remove(filename)
                    break
            else:
                break

        # Opens all files in args_norm into files_loaded
        files_loaded = [open(filename, 'rb') for filename in args_norm['files']]
        if v:
            for file in files_loaded:
                file.seek(0, 2)
                print(file.name + ' size:', file.tell())

        # API doesn't support bulk versioning so have to iterate through all files
        for fileq in all_queriedfiles[repo_num]:
            # Finds the correct file object inside the files_loaded list
            file_open = next((file for file in files_loaded if file.name == fileq['filename']), None)
            file_open.seek(0, 0)  # Seeks back to the beginning of the file
            files = {'file': file_open}
            version_json = {
                'title': args_norm['message']['title'] if 'title' in args_norm['message'] else args_norm['message']['description'],
                'fileid': fileq['fileid']
            }
            print(version_json)
            
            if v:
                print('Posting: https://' + repos[repo_num]['url'] + file_new_version_end)
            version = requests.Response()
            try:
                version = session.post('http://' + repos[repo_num]['url'] + file_new_version_end, data=version_json, files=files)
            except requests.exceptions.ConnectionError:
                version.status_code = "Connection refused"
            print(version)
            try:
                try:
                    code = version.json()['code']
                    msg = version.json()['msg']
                    if v:
                        print('Returned code:', code)
                        print('Returned message:', msg)
                    print(msg)
                    print('New version created successfully')
                except json.JSONDecodeError:
                    if version.status_code == 200:
                        print('New version created successfully')
                        return
                    raise Exception
            except Exception as e:
                # Check redirect url for below string to check
                if 'your+new+version+already+matches+one+in+this+file' in version.url:
                    print('Your new version matches the old one')
                elif 'New+version+created+successfully' in version.url:
                    print('New version created successfully')
                else:
                    print("Woops something went wrong while posting new version of " + fileq['filename'])
    else:
        print('No files found matching file argument(s). Use "forkie make" to start tracking file(s)')

def find(args: dict):
    """ Queries the every repo registered in the .forkie folder in the current directory for all files 
        or a certain file with a name and a keyword
    """
    # (-a | -n <name> [(-p <group>)]) [-vd] [(-c <comment>) [-f | --force]]
    args_norm = {
        "verbose": False,
        "force": False,
        "all_files": False,
        "name": None,
        "group": None,
        "download": False,
        # Whether to comment
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
    found_rows = False
    session = requests.session()
    repos: list = get_repo_details(v)
    files_queried = []

    if len(repos) != 0:
        offset = 0
        for r in range(len(repos)):
            files_rep = []
            repo = repos[r]
            found_rows, files_rep, offset = query_allrepos(query_json, session, repo, v, True, r, offset)
            files_queried.extend(files_rep[:])
    else:
        print("No cookie files found in .forkie")

    # If download then display a custom context to select the file to download from the query
    if found_rows:
        if args_norm['download']:
            print('\n\nDownloading...')
            print('Which repo do you want to download from? ', end='')
            repo_num = cli_utils.ask_for_list(repos)
            print('Which file do you want to download? ', end='')
            row_num = cli_utils.ask_for_list(files_queried)
            b2_key = repos[repo_num]['b2']
            interface = B2Interface(b2_key['application_key_id'],
                                    b2_key['application_key'],
                                    b2_key['bucket_name'])

            chosen_file = files_queried[row_num]
            versions = chosen_file['versions'].copy()
            version_num = 0
            if len(versions) != 1:
                # Format the version data for the chosen file if there are more than one versions
                for v in range(len(versions)):
                    version = versions[v]
                    print('before', version)
                    version['versionhash'] = version['versionhash'][:6]  # Shortens the version hash
                    uploaded = version['uploaded']
                    # Removes everything after the first dot (in this case the milliseconds)
                    uploaded = uploaded.split(".")[0]
                    version['uploaded'] = uploaded
                    version['uploaded by'] = version['author']['email']
                    # Some version data don't have titles
                    if 'title' not in version:
                        version['title'] = '~'
                    versions[v] = dict(sorted(version.items()))
                cli_utils.delete_listdict_keys(versions, ['versionid', 'author'])
                headers = list(versions[0].keys())
                headers.sort()
                headers.insert(0, 'file no.')
                values = [list(data.values()) for data in versions]
                print('\n\nHere are all the versions for ' + chosen_file['filename'] + ":")
                print(cli_utils.format_rows(headers, values))
                # for v in range(len(chosen_file['versions'])):
                #     version = chosen_file['versions'][v]
                #     print(str(v + 1) + '.', version)
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
    
        # If comment then display context on which files to comment on
        if args_norm['comment'] is not None:
            print('\n\nCommenting...')
            print('Which repo contains the file(s) to comment on? ', end='')
            repo_num = cli_utils.ask_for_list(repos)
            session.cookies.update(repos[repo_num]['cookie'])

            print('Which file(s) do you want to comment on? ', end='')
            rows_num = cli_utils.ask_for_multiple_list(files_queried, 'Do you want to select another file?', ['y', 'n'])
            chosen_files = [files_queried[num] for num in rows_num]
            
            # If not force then check for the users permission for every file
            if not args_norm['force']:
                if v:
                    print('Force wasn\'t specified so asking for permission for every file...')
                for file in chosen_files:
                    if not cli_utils.ask_for('Are you sure you want to comment "' + args_norm['comment'] + '" on ' + file['filename'] + '?', ['y', 'n']):
                        # Delete
                        chosen_files.remove(file)

            if v:
                print('Posting: https://' + repos[repo_num]['url'] + bulk_comment_end)
            comment = requests.Response()
            try:
                comment = session.post('http://' + repos[repo_num]['url'] + bulk_comment_end, json={'fileids': [file['fileid'] for file in chosen_files], 'comment': args_norm['comment']})
            except requests.exceptions.ConnectionError:
                comment.status_code = "Connection refused"
            try:
                try:
                    code = comment.json()['code']
                    msg = comment.json()['msg']
                    if v:
                        print('Returned code:', code)
                        print('Returned message:', msg)
                    print(msg)
                    print('Done!')
                except json.JSONDecodeError:
                    if comment.status_code == 200:
                        print('Done!')
                        return
                    raise Exception
            except Exception as e:
                print("Woops something went wrong while posting comments")
                print(print_exc())

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

def query_allrepos(query_json: dict, session: requests.Session, repo: dict, v: bool, p: bool, r: int, offset: int):
    files_queried = []
    found_rows = False
    formatted_rows = []
    return_offset = 0
    if p:
        print('\n\n' + str(r + 1) + '. Repo name:', str(repo['repo_name']), '(url:', str(repo['url']) + ')')
    session.cookies.update(repo['cookie'])
    returned = session.post('http://' + repo['url'] + file_query_end, json=query_json)
    code = returned.json()['code']
    msg = returned.json()['msg']
    if v and p:
        print('Query JSON:', query_json)
    if code == 200:
        if 'rows' in returned.json():
            if len(returned.json()['rows']) != 0:
                found_rows = True
                files_queried = returned.json()['rows']
                if p:
                    if v:
                        print('Returned rows (raw):', returned.json()['rows'])
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

def format_file_rows(formatted_rows: list, offset: int) -> str:
    formatted_rows = copy.deepcopy(formatted_rows)
    for row in formatted_rows:
        group_name_list = []
        for group in row['groups']:
            group_name_list.append(group['groupname'])
        row['belongs to'] = ', '.join(group_name_list)
        versions = len(row['versions'])
        row['no. of versions'] = versions

    formatted_rows = cli_utils.delete_listdict_keys(formatted_rows, ['groups', 'versions'])
    headers = list(formatted_rows[0].keys())
    headers.insert(0, 'file no.')
    return cli_utils.format_rows(headers, [list(data.values()) for data in formatted_rows], offset)