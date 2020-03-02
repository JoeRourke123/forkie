from client import cli_utils
from client.abstractions import check_bool_option, check_if_equal, check_string_option, handle_message, print_dict, get_emailandpass, get_repo_details, format_file_rows, query_allrepos, generatePdfFromHtml
from src.api.files.backblaze import B2Interface, UploadSourceBytes
from urllib.parse import urljoin
from traceback import print_exc

import requests
import os
import time
import pickle
import json
import io
import copy
import datetime


file_new_end = '/api/files/new'
file_new_version_end = '/api/files/newVersion'
file_query_end = '/api/files/query'
group_query_end = '/api/groups/getGroups'
group_users_query_end = '/api/groups/getGroupUsers'
group_new_end = '/api/groups/new'
group_del_end = '/api/groups/delete'
group_rename_end = '/api/groups/rename'
group_newmem_end = '/api/groups/addMember'
group_remmem_end = '/api/groups/removeMember'
group_movmem_end = '/api/groups/moveMember'
signin_end = '/api/signin'
signup_end = '/api/signup'
bulk_comment_end = '/api/comment/bulkComment'
report_end = '/api/report/generateReport'

""" Module which handles all subcommands to the forkie CLI
"""

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
            print('COULD NOT CONNECT TO THIS REPO')
            return
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
                print('COULD NOT CONNECT TO THIS REPO')
                return
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
                print('\nFound file(s) identical to ' + filename + ':')
                file_dicts = [dict(file.file_info) for file in files_for_user]
                headers = list(file_dicts[0].keys())
                headers.sort()
                headers.insert(0, 'file no.')
                values = [list(data.values()) for data in file_dicts]
                print(cli_utils.format_rows(headers, values), '\n')
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
                    print('COULD NOT CONNECT TO THIS REPO')
                    return
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
                        print('Uploaded "' + file_open.name + '" successfully')
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
                if files_queried is not None:
                    files_rep.extend(files_queried[:])

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
            # print(version_json)
            
            if v:
                print('Posting: https://' + repos[repo_num]['url'] + file_new_version_end)
            version = requests.Response()
            try:
                version = session.post('http://' + repos[repo_num]['url'] + file_new_version_end, data=version_json, files=files)
            except requests.exceptions.ConnectionError:
                print('COULD NOT CONNECT TO THIS REPO')
                return

            try:
                try:
                    code = version.json()['code']
                    msg = version.json()['msg']
                    if v:
                        print('Returned code:', code)
                        print('Returned message:', msg)
                    print(msg)
                    if code == 200:
                        print('New version created successfully')
                except json.JSONDecodeError:
                    if version.status_code == 200:
                        print('New version created successfully')
                        return
                    raise Exception
            except Exception as e:
                # Check redirect url for below string to check
                if 'your+new+version+already+matches+one+in+this+file' in version.url:
                    print('\nYour new version matches the old one')
                elif 'New+version+created+successfully' in version.url:
                    print('\nNew version created successfully')
                else:
                    print("\nWoops something went wrong while posting new version of " + fileq['filename'])
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
    if check_string_option(args, "-p", "group"):
        args_norm['group'] = args['<group>']
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
            found_rows_current, files_rep, offset = query_allrepos(query_json, session, repo, v, True, r, offset)
            found_rows = found_rows_current if found_rows_current else found_rows
            if files_rep is not None:
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
                print('COULD NOT CONNECT TO THIS REPO')
                return
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

def group(args: dict):
    """ View all groups or just peeps and filter by email. Add person to group. Remove person from group. Change person from one group to another.
        All users can access the view commands but only users with group leader or admin positions can access the editing commands. This is done by
        querying the correct tables
    """
    # (-V [--peeps] [<email>...] | (--add | --rm | --change) (-p <group>) [<email>]) [-vf]
    args_norm = {
        "verbose": False,
        "view": False,
        "peeps": False,
        "force": False,
        "add": False,
        "remove": False,
        "change": False,
        "group": None,
        "email": None
    }
    # print(args)
    
    # Check whether querying for people
    args_norm['peeps'] = check_bool_option(args, '--peeps')
    # Check for add
    args_norm['add'] = check_bool_option(args, '--add')
    # Check for remove
    args_norm['remove'] = check_bool_option(args, '--rm')
    # Check for change
    args_norm['change'] = check_bool_option(args, '--change')
    # Check if there's verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    v = args_norm['verbose']
    # Check if there's a force
    args_norm["force"] = check_bool_option(args, "--force")
    # Check if there's a view
    args_norm["view"] = check_bool_option(args, "--view")
    # Check for email
    if '<email>' in args:
        args_norm['email'] = args['<email>']
    # Check for group
    if check_string_option(args, "-p", "group"):
        args_norm['group'] = args['<group>']
        
    # Get all group data for user. This includes all groups that the user belongs to and all users that are a part of them
    # 1. First get all groups user belongs to
    found_rows = False
    session = requests.session()
    repos: list = get_repo_details(v)
    files_queried = []
    repos_groups_belong = []
    print('Gathering some info...')

    if len(repos) != 0:
        offset = 0
        for r in range(len(repos)):
            repo = repos[r]
            session.cookies.update(repo['cookie'])
            repos_groups_belong.append({'repo_name': repo['repo_name'], 'groups': []})
            if v:
                print('Getting: https://' + repo['url'] + group_query_end)
            groups = requests.Response()
            try:
                groups = session.get('http://' + repo['url'] + group_query_end)
            except requests.exceptions.ConnectionError:
                print('Could not connect to ' + repo['repo_name'])
                continue
            try:
                code = groups.json()['code']
                msg = groups.json()['msg']
            except Exception:
                print('Something went wrong when querying ' + repo['repo_name'])
                continue
            if v:
                print('Returned code:', code)
                print('Returned message:', msg)
            # Always display repo name, url and number
            if code == 200:
                if 'rows' in groups.json():
                    groups_returned = groups.json()['rows']
                    print('\n\nRepo no.: ' + str(r + 1) + '. Repo name:', str(repo['repo_name']), '(url:', str(repo['url']) + ')', end="\n" if args_norm['view'] else ' no. of groups: ' + str(len(groups_returned)) + '\n')
                    if not args_norm['view']:
                        print()
                    repos_groups_belong[r]['groups'].extend(copy.deepcopy(groups_returned))
                    if args_norm['view'] and not args_norm['peeps'] and not args_norm['email']:
                        print('\nHere are all your groups in repo "' + repo['repo_name'] + '":')
                        if len(groups_returned) > 0:
                            headers = list(groups_returned[0].keys())
                            headers.sort()
                            headers.insert(0, 'file no.')
                            values = [[data['groupid'], data['groupleaderid'], data['groupname']] for data in groups_returned]
                            print(cli_utils.format_rows(headers, values))
                        else:
                            print('You have no groups in this repo')

                    # Query users inside that group
                    if len(repos_groups_belong[r]['groups']) > 0:
                        for g in range(len(repos_groups_belong[r]['groups'])):
                            group = repos_groups_belong[r]['groups'][g]
                            if args_norm['view'] and args_norm['peeps']:
                                print('\nUsers in "' + group['groupname'] + '":')
                            if v:
                                print('Getting: https://' + repo['url'] + group_users_query_end)
                            users = requests.Response()
                            try:
                                users = session.post('http://' + repo['url'] + group_users_query_end, json={'groupid': group['groupid']})
                            except requests.exceptions.ConnectionError:
                                print('Could not connect to ' + repo['repo_name'])
                                continue

                            try:
                                code = users.json()['code']
                                msg = users.json()['msg']
                            except Exception:
                                print('Something went wrong when querying ' + repo['repo_name'])
                                continue
                            if v:
                                print('Returned code:', code)
                                print('Returned message:', msg)
                            if code == 200:
                                if 'rows' in users.json():
                                    users_returned = users.json()['rows']
                                    repos_groups_belong[r]['groups'][g]['users'] = copy.deepcopy(users_returned)
                                    if args_norm['view'] and args_norm['peeps']:
                                        rows = []
                                        headers = ['user no.', 'username', 'email', 'group name']
                                        for user in repos_groups_belong[r]['groups'][g]['users']:
                                            contains_email = True
                                            # Will check all specified <email> args if they are contained in the current users email
                                            # If one email arg isn't contained then the user will not be displayed
                                            if args_norm['email'] is not None:
                                                for email in args_norm['email']:
                                                    if email not in user['email']:
                                                        contains_email = False
                                                        break
                                            if contains_email:
                                                row = []
                                                row.append(user['username'])
                                                row.append(user['email'])
                                                row.append(repos_groups_belong[r]['groups'][g]['groupname'])
                                                rows.append(row)
                                        if len(rows) != 0:
                                            print(cli_utils.format_rows(headers, rows, 0))
                                        else:
                                            print('There are no users in ' + repo['repo_name'] + ' that fit that criteria')
                            else:
                                print(msg + '. Use the "forkie login <repo>" command to login to this repo')
                                return
                    else:
                        if v:
                            print('Didn\'t find any groups in ' + repo['repo_name'])
                else:
                    print("Woops something went wrong while querying groups for " + repo['repo_name'])
            else:
                print(msg + '. Use the "forkie login <repo>" command to login to this repo')
                return
    else:
        print("No cookie files found in .forkie")
    # print(repos_groups_belong)

    cont = True
    # 2. Check which subsubcommand was specified (if there was one)
    if args_norm['add'] or args_norm['remove'] or args_norm['change']:
        # 3. Ask user to choose repo to apply command to
        gerund = next((item if item not in ['remove', 'change'] else item[:-1] for item in args_norm if item in ['add', 'remove', 'change'] and args_norm[item]), None) + 'ing'  # Fancy python club
        print('\nYou are ' + gerund + ' "' + args_norm['group'] + '"')
        print('Which repo are you choosing? ', end='')
        repo_num = cli_utils.ask_for_list(repos)
        chosen_repo = repos[repo_num]
        chosen_data = repos_groups_belong[repo_num]
        chosen_group = next((item for item in chosen_data['groups'] if item['groupname'] == args_norm['group']), None)
        if chosen_group is not None or (args_norm['add'] and args_norm['email'] is None):
            chosen_user = None

            session.cookies.update(chosen_repo['cookie'])
            # If no emails are specified then the subsubcommands are taking place on the group not the user
            group_flag = args_norm['email'] is None

            end_point = ''
            post_json = {}
            # Assigning the correct end point based on the selected option and the flag set above
            if args_norm['add']:
                end_point = group_new_end if group_flag else group_newmem_end
                post_json = {'groupname': args_norm['group']} if group_flag else {'groupid': chosen_group['groupid'], 'email': args_norm['email'][0]}
            elif args_norm['remove']:
                if group_flag:
                    end_point = group_del_end
                    post_json = {'groupid': chosen_group['groupid']}
                else:
                    end_point = group_remmem_end
                    chosen_user = next((item for item in chosen_group['users'] if item['email'] == args_norm['email'][0]), None)
                    if chosen_user is None:
                        print('The email you specified doesn\'t belong to the repository you choice')
                        cont = False
                    else:
                        post_json = {'groupid': chosen_group['groupid'], 'userid': chosen_user['userid']}
            else:
                if group_flag:
                    end_point = group_rename_end
                    post_json = {'groupid': chosen_group['groupid'], 'newname': cli_utils.ask_for_string('Enter a name for the new group')}
                else:
                    chosen_user = next((item for item in chosen_group['users'] if item['email'] == args_norm['email'][0]), None)
                    if chosen_user is None:
                        print('The email you specified doesn\'t belong to the repository you choice')
                        cont = False
                    else:
                        end_point = group_movmem_end
                        # If using the change subsubcommand along with an email then this means that you want to move someone from one group to another
                        # Therefore there needs to be a dialog to chose a destination group
                        print('\nWhich group do you want to move ' + chosen_user['username'] + ' to?')
                        group_headers = ['group no.', 'group name', 'groupid', 'group leader']
                        # Compiles all the groups the user can choose from in the current repository
                        group_rows = [[group['groupname'], group['groupid'], next((item['email'] for item in group['users'] if item['userid'] == group['groupleaderid']), None)] for group in chosen_data['groups']]
                        print(cli_utils.format_rows(group_headers, group_rows, 0))
                        destination_group = chosen_data['groups'][cli_utils.ask_for_list(chosen_data['groups'])]
                        post_json = {'userid': chosen_user['userid'], 'email': args_norm['email'][0], 'src_groupid': chosen_group['groupid'], 'dst_groupid': destination_group['groupid']}
        else:
            print('\nYour chosen group doesn\'t exist inside ' + chosen_repo['repo_name'])
            cont = False
    if v:
        print('JSON to post:', post_json)
        print('Endpoint to POST to:', end_point)
    
    cont = False if args_norm['view'] else cont   # Stop view command from continuing onto next section
    
    # 4. Post to endpoint found above (only if cont)
    if cont:
        if v:
            print('\n\nContinuing to post...')
            print('Getting: https://' + chosen_repo['url'] + end_point)
        post = requests.Response()
        try:
            post = session.post('http://' + chosen_repo['url'] + end_point, json=post_json)
        except requests.exceptions.ConnectionError:
            print('\nCould not connect to ' + chosen_repo['repo_name'])
            return
        # print(post)
        try:
            code = post.json()['code']
            msg = post.json()['msg']
        except Exception:
            print('\nSomething went wrong when querying ' + chosen_repo['repo_name'])
            return
        if v:
            print('Returned code:', code)
            print('Returned message:', msg)
        print()
        print(msg)
    print('Done!')

def report(args: dict):
    """ Generate report on everything or an individual group or person. A report is a PDF which is generated from a markdown file and output to a 
        specific location if the -o option is specified
    """
    # (-p <group> | <email>) [(-o <file>)] [-v | --verbose]
    args_norm = {
        'group': None,
        'email': None,
        'output': None,
        'verbose': False
    }

    # Check if there's verbose
    args_norm["verbose"] = check_bool_option(args, "--verbose")
    v = args_norm['verbose']
    # Check for email
    if '<email>' in args:
        args_norm['email'] = args['<email>'][0]
    # Check for group
    if check_string_option(args, "-p", "group"):
        args_norm['group'] = args['<group>']
    # Check for output
    if check_string_option(args, '--output', "file"):
        args_norm['output'] = args['<file>'][0]

    # Check if the server cookie file exists
    session = requests.session()
    repos: list = get_repo_details(v)

    if len(repos) != 0:
        offset = 0
        for r in range(len(repos)):
            repo = repos[r]
            session.cookies.update(repo['cookie'])
            print('\n\n' + str(r + 1) + '. Repo name:', str(repo['repo_name']), '(url:', str(repo['url']) + ')')
    else:
        print('No cookie files found in .forkie')
        return

    print('Which repo do you want? ', end='')
    chosen_repo = repos[cli_utils.ask_for_list(repos)]

    # Query groups
    if args_norm['group'] is not None:
        # Display all groups with the given groupname
        if v:
            print('Getting: https://' + chosen_repo['url'] + report_end)
        groups = requests.Response()
        try:
            groups = session.get('http://' + chosen_repo['url'] + group_query_end)
        except requests.exceptions.ConnectionError:
            print('\nCould not connect to ' + chosen_repo['repo_name'])
            return

        try:
            code = groups.json()['code']
            msg = groups.json()['msg']
        except Exception:
            print('\nSomething went wrong generating a report ' + chosen_repo['repo_name'])
            return
        if v:
            print('Returned code:', code)
            print('Returned message:', msg)

        if code == 200:
            groups_queried = groups.json()['rows']
            groups_matching = list(filter(lambda x: x['groupname'] == args_norm['group'], groups_queried))
            if len(groups_matching) > 1:
                print('\nThere are multiple groups with that name which one do you mean?:')
                for g in range(len(groups_matching)):
                    group = groups_matching[g]
                    print(str(g) + '. Groupname ID: ' + group['groupid'] + "| Groupleader ID: " + group['groupleaderid'])
                chosen_group = groups_matching[cli_utils.ask_for_list(groups_matching)]
            else:
                chosen_group = groups_queried[0]
        else:
            print(msg)
            

    if v:
        print('Getting: https://' + chosen_repo['url'] + report_end)
    report = requests.Response()
    try:
        report = session.post('http://' + chosen_repo['url'] + report_end, json={'groupid': chosen_group['groupid']} if args_norm['group'] is not None else {'email': args_norm['email']})
    except requests.exceptions.ConnectionError:
        print('\nCould not connect to ' + chosen_repo['repo_name'])
        return

    try:
        code = report.json()['code']
        msg = report.json()['msg']
    except Exception:
        print('\nSomething went wrong generating a report ' + chosen_repo['repo_name'])
        return
    if v:
        print('Returned code:', code)
        print('Returned message:', msg)

    if code == 200:
        output_path = os.getcwd()
        if args_norm['output'] is not None:
            if not os.path.isfile(args_norm['output']) or not os.path.isdir(os.path.dirname(args_norm['output'])):
                print('Saving report to "' + args_norm['output'] + '"')
                output_path = args_norm['output']
            else:
                print('Output path doesn\'t exist')
                return
        else:
            print('Saving to cwd (' + output_path + ')')
        generatePdfFromHtml(report.json()['report'], os.path.join(output_path, datetime.datetime.now().strftime("%d|%m|%Y") + '.pdf'))
    else:
        print(msg)
    print('Done!')

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

                try:
                    signin = session.post(signin_path, json=login, headers=headers)
                except requests.ConnectionError:
                    print('COULD NOT CONNECT TO THIS REPO')
                    return
                msg = str(signin.json()["msg"])
                if v:
                    print("Signin_path:", signin_path)
                    print("Signup_path:", signup_path)
                    print("Status code:", signin.status_code)
                    print("Response:", msg)

                if signin.status_code in [500, 403]:
                    if cli_utils.ask_for(msg + " Do you want to signup?", ["y", "n"]):
                        # Keep the email and pass from signin
                        if cli_utils.ask_for("Do you want to enter a new email and password?", ["y", "n"]):
                            login = get_emailandpass(login)
                        login["username"] = str(input("Enter a username: "))
                        # Will keep checking if user wants to sign up or if error 401 otherwise break
                        while True:
                            try:
                                signup = session.post(signup_path, json=login, headers=headers)
                            except requests.ConnectionError:
                                print('COULD NOT CONNECT TO THIS REPO')
                                return
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
                            print("JSON returned:", signup.json())
                        if signup.status_code in [400, 500]:
                            print(msg + ". Try again another time.")
                            cont = False
                        else:
                            print(msg)
                            b2_app_key = signup.json()['b2'] if 'b2' in signup.json() else None
                        done = True
                    else:
                        done = not cli_utils.ask_for('Try again?', ['y', 'n'])
                else:
                    if v:
                        print(msg)
                    done = True
                    cont = True
                    b2_app_key = signin.json()['b2'] if 'b2' in signin.json() else None

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