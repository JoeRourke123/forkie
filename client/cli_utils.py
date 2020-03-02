from os import system, getenv, getcwd, path
from urllib.parse import urlparse
import requests
import platform
import subprocess

""" Module which contains the functions relating to frequently used tasks to do with the command line
"""

class UndefinedSystem(Exception):
    """ Raised when the user's system is unhandled/unrecognized """
    def __init__(self, message):
        super().__init__(message)

def create_file_incwd(filename: str, body: str):
    """ Creates a file with the given body in current working dir
    """
    file_path = path.join(getcwd(), filename)
    tmp_f = open(filename, "w+").write(body)

def open_default_editor(filename: str) -> subprocess.Popen:
    """ Opens a given filename inside the default editor of the os. Returns
        a subprocess.Popen which can be manipulated in any way the invoker sees
        fit. If the specified file does not exist then create it.
    """
    if not path.exists(filename):
        create_file_incwd(filename, "")
    
    sys = platform.system()
    args = {
        "Windows": [filename],
        "Linux": ["xdg-open", filename],
        "Darwin": ["open", filename]
    }

    if path.exists(filename) and path.isfile(filename):
        try:
            msg_input = subprocess.Popen(args[sys])
            return msg_input
        except TypeError:
            # If there's no system which matches the user's system in the args dict
            raise UndefinedSystem("Sorry your system is not supported yet")
    else:
        raise FileNotFoundError("Filename specified does not exist")

def ask_for_string(prompt: str) -> str:
    """ Asks the user for a string and asks if that the string they entered is ok
    """
    while True:
        output = str(input(prompt + ': '))
        if ask_for('Is "' + output + '" ok?', ['y', 'n']):
            break
    return output

def ask_for(question: str, answers: list) -> int:
    """ Given a question and a list of answers it will return the answer. If the list of answers has only 2 elements then
        if the answer is equal to the first element it will return True and False otherwise
    """
    answer = str(input(question + " " + str(answers) + ": ")).lower()
    while answer not in answers:
        print("Don't understand that input")
        answer = str(input(question + " " + str(answers)) + ': ').lower()
    return answer if len(answers) > 2 else answers[0] == answer

def ask_for_list(input_ls: list) -> int:
    """ Handles the logic for a list select """
    while True:
        try:
            line_no = int(input(('Enter a number: ')))
            if line_no > len(input_ls) or line_no - 1 < 0:
                print('Input number is out of range. Try again.')
            else:
                if ask_for('Are you sure?', ['y', 'n']):
                    break
        except ValueError:
            print('Line number is not a integer. Try again.')
    return line_no - 1

def ask_for_multiple_list(input_ls: list, question: str, answers: list) -> list:
    """ Handles the logic for a multiple element list select """
    output_list = []
    while True:
        line_no = ask_for_list(input_ls)
        output_list.append(line_no) if line_no not in output_list else print('Already selected.')
        more = ask_for(question, answers)
        if not more:
            break
    return output_list

def format_rows(headers: list, rows: list, offset: int = 0) -> str:
    """ Formats rows into a prettier tabular format given the headers and rows. The first header
        will always be a number count to aid with selection during the CLI flow.
        Modified from: https://stackoverflow.com/questions/9535954/printing-lists-as-tabular-data
        - headers: a list containing the headers which are printed at the top of the table, first header must be a number count
        - rows: the list containing the row data to input
        - offset: the offset the the number count
        - returns: the string to print
    """
    output = []
    header_format = ''
    row_format = ''
    top_format = '{:^{}}'
    left_format = '{:<{}}'
    cell_format = '{:>{}}'
    row_delim = '\n'
    col_delim = ' | '
    table = [headers] + [[name] + row for name, row in zip([nos for nos in range(offset + 1, offset + len(rows) + 1)], rows)]
    table_format = [len(headers) * [top_format]] \
        + len(rows) * [[left_format] + len(headers) * [cell_format]]
    col_widths = [max(len(format.format(cell, 0)) for format, cell in zip(col_format, col)) for col_format, col in zip(zip(*table_format), zip(*table))]
    return row_delim.join(col_delim.join(format.format(cell, width) for format, cell, width in zip(row_format, row, col_widths)) for row_format, row in zip(table_format, table))

def delete_listdict_keys(listOfDicts: list, toDelete: list) -> list:
    """ Deletes the given list of keys from a list dicts
    """
    new_data = []
    for row in listOfDicts:
        for delete in toDelete:
            if delete in row:
                del row[delete]
        new_data.append(row)
    return new_data

def check_if_404(url: str) -> bool:
    """ Checks if URL returns a 404
        - url: URL to check
        - returns: true if 404 found, false otherwise
    """
    check = requests.get(url)
    return check.status_code == 404

def find_hostname(url: str) -> str:
    """ Finds the hostname of the given URL and splits it on the first dot (used to form filename)
    """
    if not check_if_404(url):
        urlname = urlparse(url)
        urlhost = urlname.hostname
        # Strips everything after the first dot
        a = urlname.hostname.split(".")[0]
        pos = urlhost.find(a)
        return urlhost[:pos + len(a)]
    else:
        return None