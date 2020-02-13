import os
from numpy import uint32, uint8


class CRC32():
    """ Contains the lookup table used for getting CRC32 hashes as well as
        methods to get a hash and to generate a CRC32 hash
    """
    
    def __init__(self, polynomial):
        self.crc32lookup = self.generate_crc32lookup(polynomial)
    
    def get_crc32(self, file_body: bytearray) -> uint32:
        """ Gets a CRC32 hash for the given bytearray. This will use the 
            lookup table stored inside the crc32lookup field
            - filebody: the bytearray to hash
            - returns: a uint32 containing the hash value
        """
        # Pseudo code from https://en.wikipedia.org/wiki/Cyclic_redundancy_check#CRC-32_algorithm
        # Sets all bytes high
        crc32 = uint32(0xFFFFFFFF)
        
        # A CRC32 hash is just the remainder of a division calculation with 
        # the given byte array and a set polynomial expression. A byte can store
        # 256 different values and the polynomial is always going to be the same
        # number so it's possible to compute all the possible division calculations
        # that can occur before getting any hashes and store these inside a lookup
        # which can be accessed for each different possible dividend. This also
        # means that the bytearray can be processed byte by byte instead of bit
        # by bit
        for byte in file_body:
            lookup_index = (crc32 ^ byte) & 0xFF
            crc32 = uint32(crc32 >> 8) ^ self.crc32lookup[lookup_index]
        # Returns the complement of crc32
        return ~crc32
            
    def generate_crc32lookup(self, polynomial: uint32) -> list:
        """ Generates a lookup table for all possible remainders of a division
            calculation between a byte and the given polynomial
            - polynomial: the given polynomial to generate the lookup table for.
                          E.g. a polynomial of x^4 + x^2 + 1 would have a bit
                          pattern of 0b10100
            - returns: the list of all possible remainders for every possible dividend
        """

        remainder: uint32
        crc32lookup = []
        
        for b in range(0, 256):
            remainder = uint32(b)
            # For loop from 8 to 1
            for bit in range(8, 0, -1):
                if remainder & 1:
                    remainder = uint32((uint32(remainder) >> 1) ^ polynomial)
                else:
                    remainder = uint32(uint32(remainder) >> 1)
            crc32lookup.append(remainder)
        return crc32lookup
                    

def get_file_size(path: str) -> int:
    """ Gets the file size (in bytes) of the file at a given path
        - path: the path of the file to get the size of
        - returns: the file size in bytes
        - raises FileNotFoundError: when the file path does not exist or
                                    the file path is not a file
    """
    
    file_size = None
    if os.path.exists(path) and os.path.isfile(path):
        file_size = os.stat(path).st_size
    else:
        raise FileNotFoundError("No file with that path")
    return file_size


def get_file_bytearray(filename: str) -> bytearray:
    """ Gets the file at a given path as a byte array
        - filename: the path of the file to get as a byte array
        - returns: a byte array of the body of the file
        - raises FileNotFoundError: when the file path does not exist or
                                    the file path is not a file
    """
    filebytes: bytearray = None
    if os.path.exists(filename) and os.path.isfile(filename):
        filebytes = open(filename, "rb").read()
    else:
        raise FileNotFoundError("No file with that path")
    return filebytes


def check_if_equal(old_file: bytearray, new_file: bytearray, crc32: CRC32 = None) -> bool:
    """ Checks if two files are equal using a 3 stage method. 
        1. Checks if the two files are of the same size. Continue if so...
        2. Checks if the two files have the same hash. Continue if so...
        3. Checks if the two files have exactly the same byte array data. If so then they are equal.
        If the two files fail any of these checks then the two files are not equal.
        - old_file: the first file as a byte array
        - new_file: the second file as a byte array
        - crc32:    the CRC32 object containing the precomputed lookup table values for a specific
                    polynomial
        - returns: true if equals, false if not
    """
    equal = False
    old_file_size = len(old_file)
    new_file_size = len(new_file)
    
    # First check if sizes are equal
    if old_file_size == new_file_size:
        if crc32 is None:
            # If crc32 isn't instantiated instantiate it with this poly
            crc32 = CRC32(uint32(0xEDB88320))
        old_file_hash = crc32.get_crc32(old_file)
        new_file_hash = crc32.get_crc32(new_file)
        # Then check if hashes are equal
        if old_file_hash == new_file_hash:
            # Then check if bytearrays are equal
            if old_file == new_file:
                equal = True
    return equal