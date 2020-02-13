from b2sdk.v1 import InMemoryAccountInfo, B2Api, UploadSourceBytes, DownloadDestBytes
from src.api.files.utils import getFileExtension
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
        if extension is None:
            extension = getFileExtension(filename)
        # Replace CRC32 hash with SHA1 generated by B2?
        print("Version ID:", versionid)
        print("Filename:", filename)
        print("File ID:", fileid)
        print("Extension:", extension)
        print("SHA1:", data.get_content_sha1())
        print("Content length:", data.get_content_length())
        self.bucket.upload(
            upload_source=data,
            file_name=versionid,
            content_type=extension,
            file_info={
                'filename': filename,
                'fileid': fileid
            }
        )

    def downloadFile(self, versionid: str, filename: str = None, fileid: str = None) -> dict:
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
    

# Create B2Interface object
interface = B2Interface(application_key_id, application_key, file_rep_bucket)

# Testing uploading
resource_location = join(dirname(dirname(dirname(dirname(abspath(__file__))))), "res/tests/files")
test_filename = 'asyoulik.txt'
print(resource_location)
filebytes = open(join(resource_location, test_filename), "rb").read()
interface.uploadFile(filebytes, str(uuid1().hex), test_filename, str(uuid1().hex))

# Testing downloading
version_id = '825ffa8e4dec11eaac99d5d125025aed'
file_data = interface.downloadFile(version_id)