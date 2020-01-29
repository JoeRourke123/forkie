from hashlib import sha256


def hashPassword(password):
    return str(sha256(password.encode('utf-8')).hexdigest())
