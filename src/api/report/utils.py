import io
import json
import markdown

from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration

from io import BytesIO

from src.api.user.utils import getUserDataFromEmail, getUserData
from src.api.groups.utils import getGroupData, getGroupUsers, getUserGroups
from src.api.comments.utils import getComments
from src.api.files.file_query import file_query

def generateReportHTML(groupid: str, email: str) -> str:
    """ Generate the report file in memory and returns the markdown string in html using markdown package

        - groupid: if not none then create a group report
        - email: if not none then create a user report
        - returns: if both params are not none then report on user inside group, otherwise as above
    """
    # Create the StringIO object to store the report file in memory
    report = io.StringIO()
    title = "# Report on " + (("group \"" + getGroupData(groupid)['groupname'] + "\"") if groupid is not None and email is None else ("user \"" + getUserDataFromEmail(email)['username'] + "\"") + (" in group \"" + getGroupData(groupid)['groupname'] + "\"" if email is not None and groupid is not None else ""))
    report.write(title + '\n\n---\n\n')
    user_list_prefix = ""
    users_in_group = []

    if groupid is not None and email is None:
        users_in_group = getGroupUsers(groupid)
        users_heading = "## Users in group\n\n"
        user_list_prefix = "1. "
        tabulations = "\t"
        report.write(users_heading)

    if email is not None:
        users_in_group.append(getUserDataFromEmail(email))
        user_list_prefix = "## "
        tabulations = ""

    # Write user's info to report
    for user in users_in_group:
        user_info = user_list_prefix + "Info on user \"" + user['username'] + "\"\n\n" + tabulations + "- User ID: " + str(user['userid']) + "\n" + tabulations + "- Email: " + user['email'] + "\n" + tabulations + "- Last login: " + str(user['lastlogin']) + "\n" + tabulations + "- Admin: " + ("Yes" if user['admin'] else "No") + "\n\n"
        report.write(user_info)
    
    # Write group details if groupid or groupid and email is not None
    if groupid is not None or (groupid is not None and email is not None):
        group = getGroupData(groupid)
        group_info = "## Info on group \"" + group['groupname'] + "\"\n\n- Group ID: " + groupid + "\n- Groupleader: " + getUserData(group['groupleader']['userid'])['username'] + " (ID: " + str(getUserData(group['groupleader']['userid'])['userid']) + ")\n\n"
        report.write(group_info)
    
    # Display all the files belonging to the group if groupid is not none
    if groupid is not None and email is None:
        group = getGroupData(groupid)
        report.write("## Files belonging to \"" + group['groupname'] + "\"\n\n")
        files_in_group = file_query({'groupid': groupid})
        if len(files_in_group) > 0:
            for file in files_in_group:
                file_info = "1. Filename: \"" + file['filename'] + "\"\n\t- File ID: " + file['fileid'] + "\n\t- Extension: " + file['extension'] + "\n\t- Comments:\n"
                report.write(file_info)
                # Then display a list of all comments relating to the file
                comments = getComments(file['fileid'])
                if len(comments) > 0:
                    for comment in comments:
                        comment_info = "\t\t1. \"" + comment['comment'] + "\"\n\t\t\t- By: " + comment['user']['username'] + "\n\t\t\t- Written on: " + str(comment['date']) + "\n\t\t\t- Read: " + ("Yes" if comment['read'] else "No") + "\n"
                        report.write(comment_info)
                else:
                    report.write("\t\t- No comments for this file\n")
                report.write("\t- Versions:\n")
                
                # Display version info
                versions = file['versions']
                version_info = ""
                if len(versions) > 0:
                    for version in versions.keys():
                        version = versions[version]
                        version_info += "\t\t1. \"" + version['title'] + "\" (Hash: " + version['versionhash'] + ")\n\t\t\t- Uploaded on: " + version['uploaded'] + "\n\t\t\t- Author: " + str(version['author']['username']) + "\n"
                    report.write(version_info)
                else:
                    report.write("\t\t- No versions found\n")
            report.write("\n")
        else:
            report.write("No files for this group\n\n")
    
    # Display all file versions that the user with email has created. If groupid is not none then it will only display file versions from that group
    if email is not None:
        user = getUserDataFromEmail(email)
        group = getGroupData(groupid) if groupid is not None else None
        report.write("## File versions belonging to \"" + user['username'] + "\"" + ((" in group \"" + group['groupname'] + "\"\n\n") if group is not None else "\n\n"))
        groups_to_find_versions = []
        if groupid is None:
            # Find all the groups that the user is in
            groups_to_find_versions = [getGroupData(group['groupid']) for group in getUserGroups(user['userid'])]
        else:
            # Add only the group that is specified by groupid
            groups_to_find_versions = [group]
        
        versions_user_has_authored = {}
        # Find all versions inside the group['files'] that the user in question has authored
        for group in groups_to_find_versions:
            for file in group['files']:
                # Create a more succint file dictionary used later
                small_file = {}
                small_file['filename'] = file['filename']
                small_file['versions'] = []
                found_something = False
                for version in file['versions'].keys():
                    version = file['versions'][version]
                    if version['author']['email'] == email:
                        found_something = True
                        print('found version', version)
                        small_file['versions'].append(version)
                # Only add small file if it contains versions related to the user
                if found_something:
                    versions_user_has_authored[file['fileid']] = small_file
        
        # Display version data found
        if len(versions_user_has_authored) > 0:
            for fileid in versions_user_has_authored.keys():
                file = versions_user_has_authored[fileid]
                version_info = "1. For \"" + file['filename'] + "\" (File ID: " + fileid + ") they created:\n"
                for version in file['versions']:
                    version_info += "\t2. \"" + version['title'] + "\"\n\t\t- Hash: " + version['versionhash'] + "\n\t\t- Version ID: " + version['versionid'] + "\n\t\t- Uploaded: " + str(version['uploaded']) + "\n\t\t- Author: " + version['author']['username'] + "\n"
                report.write(version_info)
            report.write("\n")
        else:
            report.write("User has authored no versions" + (" inside this group\n\n" if groupid is not None else "\n\n"))
    return markdown.markdown(report.getvalue()).replace("\n", "")

# From weazyprint docs (https://weasyprint.readthedocs.io/en/latest/tutorial.html#instantiating-html-and-css-objects)
def generatePdfFromHtml(html: str, cssPath: str = None) -> BytesIO:
    """ Generates a pdf from a given html string and outputs to a BytesIO. Will also include css style if specified
        - Uses: weazyprint
        _ html: given html string to convert and save to pdf
        - cssPath: if specified, will add the css from the given path to the pdf doc
    """
    font_config = FontConfiguration()
    html = HTML(string=html)
    css = CSS(string=open(cssPath, "r").read(), font_config=font_config) if cssPath is not None else None

    return BytesIO(html.write_pdf(
        stylesheets=[css] if css is not None else None,
        font_config=font_config
    ))

# From: https://stackoverflow.com/questions/9320370/markdown-to-html-using-a-specified-css/9470679
def linkCSSToReport(cssPath: str, body: str) -> str:
    """ Opens the CSS file at path cssPath and links it the given html body. 
        Note: this adds all the CSS to the header so your html files aren't going to look pretty
        - cssPath: the path of the CSS to open and add to header
        - body: The body of the html as a string (usually comes from the function above)
    """
    output = """<!DOCTYPE html>
            <html lang="en">

            <head>
                <meta charset="utf-8">
                <style type="text/css">
            """

    cssin = open(cssPath)
    output += cssin.read()

    output += """
        </style>
    </head>

    <body>
    """

    output += body

    output += """</body>

    </html>
    """

    return output.replace("\n", "")