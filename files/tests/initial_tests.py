from files import file_compare
from os.path import dirname, abspath, join, isfile, basename
from os import listdir
from numpy import uint32
import time
import random

resource_location = join(dirname(dirname(dirname(abspath(__file__)))), "res")
# Gets path of all resource files
res_files = [join(resource_location, f) for f in listdir(resource_location) if isfile(join(resource_location, f))]

random_file = random.randint(0, len(res_files))
print(basename(res_files[random_file]) + " size:", file_compare.get_file_size(res_files[random_file]))
crc32 = file_compare.CRC32(uint32(0xEDB88320))
# print([hex(no) for no in crc32.crc32lookup])

b = bytearray
print("'This is an example.':", hex(crc32.get_crc32(bytearray(b"This is an example."))))
file_count = 0
for file in res_files:
    start_time = time.time()
    print(str(file_count) + ":", basename(file) + ":", hex(crc32.get_crc32(file_compare.get_file_bytearray(file))), end="")
    print("(%.6fs)" % (time.time() - start_time))
    file_count += 1


# Checks every file against each other for equality
for oF in res_files:
    for nF in res_files:
        if oF != nF:
            start_time = time.time()
            print(basename(oF) + " == " + basename(nF) + " :", file_compare.check_if_equal(file_compare.get_file_bytearray(oF), file_compare.get_file_bytearray(nF), crc32), end="")
            print("(%.5fs)" % (time.time() - start_time))