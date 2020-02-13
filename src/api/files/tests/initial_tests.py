from src.api.files import file_compare
from os.path import dirname, abspath, join, isfile, basename
from os import listdir
from numpy import uint32
import time
import random

resource_location = join(dirname(dirname(dirname(dirname(abspath(__file__))))), "res/tests/files")
# Gets path of all resource files and creates a dict with
# filename : filepath
res_files = dict()
for f in listdir(resource_location):
    f_loc = join(resource_location, f)
    if isfile(f_loc):
        res_files[basename(f_loc)] = f_loc

random_file = random.choice(list(res_files.keys()))
print("Random file size:")
print(basename(random_file) + " size:", file_compare.get_file_size(res_files[random_file]))
# Inits a new CRC32 (constructor generates lookup)
crc32 = file_compare.CRC32(uint32(0xEDB88320))
# print([hex(no) for no in crc32.crc32lookup])

b = bytearray
# Shows how to use hash on string
print("\nHash of string:")
print("'This is an example.':", hex(crc32.get_crc32(bytearray(b"This is an example."))))
file_count = 0
print("\nHash of all files:")
for file in res_files:
    start_time = time.time()
    print(str(file_count) + ":", file + ":", hex(crc32.get_crc32(file_compare.get_file_bytearray(res_files[file]))), end="")
    print("(%.6fs)" % (time.time() - start_time))
    file_count += 1


# Checks every file against each other for equality
print("\nAll file equality check:")
for oF in res_files:
    for nF in res_files:
        if oF != nF:
            start_time = time.time()
            print(oF + " == " + nF + " :", file_compare.check_if_equal(file_compare.get_file_bytearray(res_files[oF]), file_compare.get_file_bytearray(res_files[nF]), crc32), end="")
            print("(%.5fs)" % (time.time() - start_time))