def make(args: dict):
    print(args)
    
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