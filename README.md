## file-rep0
Group 9 Project for CS1813 Assignment 1

Hosted at: https://file-rep0.herokuapp.com

---
### Database Examples
#### Querying a database table
To query a db table for an API endpoint simply do the following:
- I'm gonna use the FileVersionTable as an example, all the tables will be imported at the top of the app.py
```
  FileVersionTable.query.filter_by(fileid=ID_TO_FETCH_FILES_OF)
```
- This will return all the files with the fileid that you pass it (replacing ID_TO_FETCH_FILES_OF)
- You can add `.first()` to just get the first result from the query if you only want a specific result

#### Inserting into the database
- To insert into the database, you need to create an instance of the table you're inserting to and pass it the data to add - like so:
- This time I'm using the MetadataTable
```
  newMetadataEntry = MetadataTable({
    "fileversionid": THE_FILE_TO_APPLY_THE_METADATA_TO,
    "title": THE_METADATA_TITLE,          # e.g: 'author'
    "content": THE_METADATA_CONTENT       # e.g: the userID of the author
  })

  try:
    db.session.add(newMetadataEntry)
    db.session.commit()
  except Exception as e:
    print(e)
```
- After the insert you could return that it was successful or something like that
- Be sure to read the fields required for a table before you insert into it

### B2 Backblaze
- Using B2 Backblaze for file storage (see helpful links)
- Using the `b2sdk` python library as a wrapper for the b2 api calls
- To use the library you need to first authenticate your account using:
```
  from b2sdk.v1 import InMemoryAccountInfo, B2Api

  info = InMemoryAccountInfo()
  b2_api = B2Api(info)
  application_key_id = '4a5b6c7d8e9f'
  application_key = '001b8e23c26ff6efb941e237deb182b9599a84bef7'
  b2_api.authorize_account("production", application_key_id, application_key)
```
- This creates a B2Api object which you can use for api calls such as
  1. Bucket stuff
     - Viewing all buckets (doesn't work if the key only applies to one bucket)
        ```
          b2_api.list_buckets()
        ```
     - Creating buckets
        ```
          bucket_name = 'example-mybucket-b2-1'  # must be unique in B2 (across all accounts!)
          bucket_type = 'allPublic'  # or 'allPrivate'
          b2_api.create_bucket(bucket_name, bucket_type)
        ```
     - Deleting
        ```
          bucket_name = 'example-mybucket-b2-to-delete'
          bucket = b2_api.get_bucket_by_name(bucket_name)
          b2_api.delete_bucket(bucket)
        ```
     - Update info
        ```
          new_bucket_type = 'allPrivate'
          bucket_name = 'example-mybucket-b2'

          bucket = b2_api.get_bucket_by_name(bucket_name)
          bucket.update(bucket_type=new_bucket_type)
          {'accountId': '451862be08d0',
          'bucketId': '5485a1682662eb3e60980d10',
          'bucketInfo': {},
          'bucketName': 'example-mybucket-b2',
          'bucketType': 'allPrivate',
          'corsRules': [],
          'lifecycleRules': [],
          'revision': 3}
        ```
  2. Downloading a file
  ```
    local_file_path = '/home/user1/b2_example/new2.pdf'
    file_id = '4_z5485a1682662eb3e60980d10_f1195145f42952533_d20190403_m130258_c002_v0001111_t0002'
    download_dest = DownloadDestLocalFile(local_file_path)
    progress_listener = DoNothingProgressListener()

    b2_api.download_file_by_id(file_id, download_dest, progress_listener)
    {'fileId': '4_z5485a1682662eb3e60980d10_f1195145f42952533_d20190403_m130258_c002_v0001111_t0002',
    'fileName': 'som2.pdf',
    'contentType': 'application/pdf',
    'contentLength': 1870579,
    'contentSha1': 'd821849a70922e87c2b0786c0be7266b89d87df0',
    'fileInfo': {'src_last_modified_millis': '1550988084299'}}
  ```
  3. Downloading files (uses large file API automatically)
    ```
      local_file_path = '/home/user1/b2_example/new.pdf'
      b2_file_name = 'dummy_new.pdf'
      file_info = {'how': 'good-file'}

      bucket = b2_api.get_bucket_by_name(bucket_name)
      bucket.upload_local_file(
        local_file=local_file_path,
        file_name=b2_file_name,
        file_infos=file_info,
      )
    ```
- Application keys can be generated in the backblaze dashboard for specific buckets (for our purposes we should only need one)

---
### Helpful Links
How to connect to Postgres with Python:
https://dev.to/paultopia/the-easiest-possible-way-to-throw-a-webapp-online-flask--heroku--postgres-185o

Flask Docs
http://flask.palletsprojects.com/en/1.1.x/

Creating APIs with Flask
https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

B2 Backblaze service
https://www.backblaze.com/

b2sdk docs
https://b2-sdk-python.readthedocs.io/en/master/index.html


### How to connect Heroku to your local Git repo
1. Clone the repo from here
2. Enter it in the terminal
3. Enter... `heroku git:remote -a file-rep0`
4. Then when you want to upload to the server enter... `git push heroku master`
