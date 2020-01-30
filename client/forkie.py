"""forkie CLI

Usage:
    {0} {1} [-v | --verbose] [(-m <message>)] (<file>)...
    {0} {1} [-m <message>] [-v | --verbose] (<name> [-k <keyword>])...
    {0} {1} (-a | (-n <name> -k <keyword>)) [-p <group>] [-v | --verbose] [-c <comment> [-f | --force]]
    {0} {1} [-V [(-a | (-k <keyword>))] [-p <group>]] [-vf]
    {0} {1} (-V [--peeps] [<email>...] | --add [-p <group>] (<email>...) | --rm [-p <group>] (<email>...) | --change (-p <group>) (<email>...)) [-vf]
    {0} {1} (-V (-a | <report>) | --gen [(-p <group> | <email>)]) [-v | --verbose]
    {0} {1} [-v | --verbose]
    {0} -h | --help | --version
Options:
    -n --name     The name the file should have in the repository
    -m --message  The message/description of the file. This is needed.    
    -a            All files
    -k --keyword  Keyword to search for
    -p            Permission group
    -v --verbose  Verbose
    -V --view     Outputs element
    -c --comment  Add comment
    -f --force    Force/Don't ask for permission first
    -h --help     Show help
    --version     Show version
    --peeps       View people
    --add         Add person/people to a group
    --rm          Remove person/people from a group
    --change      Move person/people to another group
    --gen         Generates a report
    <file>        File name argument (path to file)
    <name>        Name argument.
    <message>     Description of file
    <keyword>     Substring inside description
    <comment>     Comment argument
    <group>       One of the available permission groups
    <username>    Username of a user
    <email>       The email of a user
    <report>      The report name of an existing report
"""

from docopt import docopt
from cli import command_handler
import sys

python_interpreter = sys.executable
main_exec = "forkie.py"
commands = {
    "make": command_handler.make, 
    "update": command_handler.update,
    "find": command_handler.find, 
    "archive": command_handler.archive, 
    "group": command_handler.group, 
    "report": command_handler.report, 
    "login": command_handler.login
}

# Template of all commands, options and arguments
args_commands = {
    'make': False, 
    '--message': 0, 
    '<message>': None, 
    '--verbose': 0, 
    '<file>': [], 
    '--name': 0, 
    '<name>': [], 
    'update': False, 
    '--keyword': 0, 
    '<keyword>': [], 
    'find': False, 
    '-a': False, 
    '-p': False, 
    '<group>': None, 
    '--comment': 0, 
    '<comment>': None, 
    '--force': 0, 
    'archive': False, 
    '--view': 0, 
    'group': 0, 
    '--peeps': False, 
    '<email>': [], 
    '--add': False, 
    '--rm': False, 
    '--change': False, 
    'report': 0, 
    '<report>': None, 
    '--gen': False, 
    'login': False, 
    '--help': 0, 
    '--version': 0
}
# commands = ["make", "update", "find", "archive", "group", "report", "login"]

def init_docs(_doc: str) -> str:
    """ Initialises the __doc__ field to be parsed into docopts. Just formats
        the __doc__ with the commands from the commands list and adds the
        main executable command to all subcommands.
        - _doc: the string containing the __doc__
        - returns: a formated string with the main executable command and all subcommands
    """
    docs = []
    com_count = 0
    for doc in _doc.split("\n"):
        if "{" in doc or "}" in doc:
            doc = doc.format(main_exec, list(commands.keys())[com_count] if com_count < len(commands.keys()) else None)
            com_count += 1
        docs.append(doc)
        
    docs = "\n".join(docs)
    return docs

def remove_options(args: dict) -> dict:
    """ Strips options part of doc which gets parsed by docopts
        - args: the dictionary of arguments produced by docopts
        - returns: a dictionary with just the useful arguments in it
    """
    options_flag = False
    new_args = dict()
    for arg in args.keys():
        if arg == "Options:":
            break
        new_args[arg] = args[arg]
    return new_args

def find_difference(dict1: dict, dict2: dict) -> dict:
    """ Finds the items in two dictionaries that are different. Hard to classify this function but here's an
        example. For example if dict1 = {"hello": False, "world": False} and 
        dict2 = {"hello": True, "world": False}, the returned dict would be {"hello": True}
        - dict1: the dictionary to "subtract"
        - dict2: the dictionary to complement
        - returns: the different keys and values between dict1 and dict2
    """
    return {key: dict2[key] for key in dict1.keys() if dict1[key] != dict2[key]}

if __name__ == '__main__':
    arguments = docopt(init_docs(__doc__), version='DEMO 1.0')
    arguments = remove_options(arguments)
    arguments = find_difference(args_commands, arguments)
    found = False

    if len(arguments.keys()) != 0:
        for arg in arguments.keys():
            if arg in commands.keys():
                # Deletes (sub)command key from dictionary then calls the function associated to that
                # (sub)command which is stored in the commands dict
                del arguments[arg]
                commands[arg](arguments)
                # found = True
                break