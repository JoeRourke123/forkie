import client.cli.cli_utils as cli_utils

def make(args: dict):
    # Template used in temporary message files to explain to the user that they need to add a
    # message in order to add the file
    tmp_msg_body = "\n# Please write a name and description of this add in the line above.\n# If no message is added then you will not be able to add the files you wanted to.\n# The general overview should be written on the first line and more in depth descriptions on the third."
    message = ""
    
    # [-m <message>] [-v | --verbose] (<file>)...    
    # If message is not present then open the default editor
    try:
        if args["<message>"] == "":
            raise KeyError
        else:
            print("Success!")
    except KeyError:
        try:
            # Create tmp message file then open it in default editor
            cli_utils.create_file_incwd("message.txt", )
        except TypeError:
            # If the default editor could not be found then
            print("File additions require a message (use: -m)")
    
def update(args: dict):
    print(args)

def find(args: dict):
    for arg in args.keys():
        print(arg, args[arg])

def archive(args: dict):
    print(args)

def group(args: dict):
    print(args)

def report(args: dict):
    print(args)

def login(args: dict):
    print(args)
    
def print_dict(args: dict):
    for arg in args.keys():
        print(str(arg) + ":" + str(args[arg]))