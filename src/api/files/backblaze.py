from b2sdk.v1 import InMemoryAccountInfo, B2Api, UploadSourceBytes, DownloadDestBytes, FileVersionInfo
from uuid import uuid1
from os.path import join, dirname, abspath

# THIS IS JUST USED FOR TESTING
# These are my b2 key details for a bucket called file-rep0
application_key_id = '0003976a482cd540000000001'
application_key = 'K0000L+ZHdPrf3wT4G+7enptKGSct68'
file_rep_bucket = 'file-rep0'

class CouldNotFindCorrectFile(Exception):
    """ Raised when the b2api cannot find the specified folder in the bucket """
    def __init__(self, message):
        super().__init__(message)
        
class B2Interface:
    """ Wrapper for b2sdk functions used on the forkie web server and client side
    """
    
    def __init__(self, application_key_id, application_key, bucket_name):        
        """ Initialize b2_api and authenticate account
        """
        info = InMemoryAccountInfo()
        self.b2_api = B2Api(info)
        self.application_key_id = application_key_id
        self.application_key = application_key
        self.b2_api.authorize_account("production", application_key_id, application_key)
        self.bucket = self.b2_api.get_bucket_by_name(bucket_name)

    def uploadFile(self, data: bytearray, versionid: str, filename: str, fileid: str, extension: str = None):
        data: UploadSourceBytes = UploadSourceBytes(data)

        # Replace CRC32 hash with SHA1 generated by B2?
        print("Version ID:", versionid)
        print("Filename:", filename)
        print("File ID:", fileid)
        print("Extension:", extension)
        print("SHA1:", data.get_content_sha1())
        print("Content length:", data.get_content_length())
        self.bucket.upload_bytes(
            data_bytes=data.data_bytes,
            file_name=versionid,
            file_infos={
                'filename': filename,
                'fileid': fileid
            }
        )

        return data

    def downloadFileByVersionId(self, versionid: str, filename: str = None, fileid: str = None) -> dict:
        # Creates a space in memory for the downloaded file
        memory_location = DownloadDestBytes()
        self.bucket.download_file_by_name(
            file_name=versionid,
            download_dest=memory_location
        )
        file_body = memory_location.get_bytes_written()
        # Constructs a return dictionary
        return_data = {
            'file_body': file_body,
            'content_length': memory_location.content_length,
            'content_type': memory_location.content_type,
            'content_sha1': memory_location.content_sha1,
            'fileid': memory_location.file_info['fileid'],
            'filename': memory_location.file_info['filename']
        }
        del memory_location  # Cleanup memory (idk if this actually does anything)
        
        # Check if returned file matches filename and fileid if not raise CouldNotFindFile
        if filename is not None:
            if return_data['filename'] != filename:
                raise CouldNotFindCorrectFile('File found does not match the filename given')
        if fileid is not None:
            if return_data['fileid'] != fileid:
                raise CouldNotFindCorrectFile('File found does not match the fileid given')

        print(return_data)
        return return_data
    
    def downloadFileByFileId(self, fileid: str, filename: str = None, versionid: str = None) -> dict:
        """ Downloads a file by fileid. This is the fileid inside the database (not backblaze's fileid) which is
            stored inside the file_info. Gets a list of all files inside the bucket and finds the file with that fileid inside
        """
        bucket_gen = self.bucket.ls(
            folder_to_list='',
            show_versions=False,
            recursive=False,
            fetch_count=None
        )
        
        for f in bucket_gen:
            # Gets the fileid from the FileVersionInfo object
            file_data: FileVersionInfo = f[0]
            if file_data.file_info['fileid'] == fileid:
                break
        print(file_data.file_name)
        return self.downloadFileByVersionId(file_data.file_name)
    
    def checkForEqualFiles(self, sha1: str, size: int, filename: str = None) -> list:
        """ Checks for files that are equal in the bucket """
        bucket_gen = self.bucket.ls(
            folder_to_list='',
            show_versions=False,
            recursive=False,
            fetch_count=None
        )
        equal_files: list = []

        for f in bucket_gen:
            file_data: FileVersionInfo = f[0]
            # print('\n' + file_data.file_info['filename'])
            # print(file_data.size)
            # print(file_data.content_sha1)
            if file_data.size == size:
                if file_data.content_sha1 == sha1:
                    # Checks filename if filename not none
                    currFName = file_data.file_info['filename']
                    if currFName == filename if filename is not None else currFName:
                        print('Equal')
                        equal_files.append(file_data)

        return equal_files

# # Create B2Interface object
interface = B2Interface(application_key_id, application_key, file_rep_bucket)
#
# # Testing uploading
# resource_location = join(dirname(dirname(dirname(dirname(abspath(__file__))))), "res/tests/files")
# test_filename = 'asyoulik.txt'
# print(resource_location)
# filebytes = open(join(resource_location, test_filename), "rb").read()
# interface.uploadFile(filebytes, str(uuid1().hex), test_filename, str(uuid1().hex))
#
# # Testing downloading
# version_id = '825ffa8e4dec11eaac99d5d125025aed'
# # file_data = interface.downloadFileByVersionId(version_id)
#
# file_data = interface.downloadFileByFileId('57ce10114de911eaac99d5d125025aed')

# Testing equality
# sha1 = 'ae1f2eb0965e7bc2d9c12e7c4283e1c96303d585'
# print([x.file_info for x in interface.checkForEqualFiles(sha1, 3263)])
