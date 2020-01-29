import hashlib

def hashPassword(password):
    hash = hashlib.sha256
    hash.update(password)

    return str(hash.hexdigest())