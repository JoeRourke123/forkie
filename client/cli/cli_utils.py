from os import system, getenv, getcwd, path
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
