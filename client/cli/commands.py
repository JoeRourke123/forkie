"""forkie CLI

Usage:
    {0} {1} [-m <message>] [-v | --verbose] (<file> [-n <name>])...
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
import sys

python_interpreter = sys.executable
main_exec = __name__
commands = ["make", "update", "find", "archive", "group", "report", "login"]

def init_docs(_doc: str) -> str:
    docs = []
    com_count = 0
    for doc in _doc.split("\n"):
        if "{" in doc or "}" in doc:
            doc = doc.format(main_exec, commands[com_count] if com_count < len(commands) else None)
            com_count += 1
        docs.append(doc)
        
    docs = "\n".join(docs)
    return docs

if __name__ == '__main__':
    arguments = docopt(init_docs(__doc__), version='DEMO 1.0')
    for arg in arguments.keys():
        print(arg, ":", arguments[arg])
        if arg in commands:
            print()