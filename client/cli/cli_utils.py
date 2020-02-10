from os import system, getenv, getcwd, path
from urllib.parse import urlparse
import requests
import platform
import subprocess

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

def ask_for(question: str, answers: list):
    """ Given a question and a list of answers it will return the answer. If the list of answers has only 2 elements then
        if the answer is equal to the first element it will return True and False otherwise
    """
    answer = str(input(question + " " + str(answers) + ": ")).lower()
    while answer not in answers:
        print("Don't understand that input")
        answer = str(input(question + " " + str(answers))).lower()
    return answer if len(answers) > 2 else answers[0] == answer

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