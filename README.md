# forkie

Group 9 Project for CS1813 Assignment 1

Hosted at: <https://file-rep0.herokuapp.com>

---

## Database Examples

### Querying a database table

To query a db table for an API endpoint simply do the following:

- I'm gonna use the FileVersionTable as an example, all the tables will be imported at the top of the app.py

```python
  FileVersionTable.query.filter_by(fileid=ID_TO_FETCH_FILES_OF)
```

- This will return all the files with the fileid that you pass it (replacing ID_TO_FETCH_FILES_OF)
- You can add `.first()` to just get the first result from the query if you only want a specific result

### Inserting into the database

- To insert into the database, you need to create an instance of the table you're inserting to and pass it the data to add - like so:
- This time I'm using the MetadataTable

```python
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

#### B2 Backblaze

- Using B2 Backblaze for file storage (see helpful links)
- Using the `b2sdk` python library as a wrapper for the b2 api calls
- To use the library you need to first authenticate your account using:

```python
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

        ```python
          b2_api.list_buckets()
        ```

     - Creating buckets

        ```python
          bucket_name = 'example-mybucket-b2-1'  # must be unique in B2 (across all accounts!)
          bucket_type = 'allPublic'  # or 'allPrivate'
          b2_api.create_bucket(bucket_name, bucket_type)
        ```

     - Deleting

        ```python
          bucket_name = 'example-mybucket-b2-to-delete'
          bucket = b2_api.get_bucket_by_name(bucket_name)
          b2_api.delete_bucket(bucket)
        ```

     - Update info

        ```python
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

  2. Downloading files (can also download by file name)
  
    ```python
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

  3. Uploading files (uses large file API automatically)

    ```python

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

### How to connect Heroku to your local Git repo

1. Clone the repo from here
2. Enter it in the terminal
3. Enter... `heroku git:remote -a file-rep0`
4. Then when you want to upload to the server enter... `git push heroku master`

### How to use the forkie CLI

The forkie CLI was made to **accompany** the forkie website not replace it

---

#### Main flow

- `forkie login <repo>` this will "log you in" to the repository with the `<repo>` URL (this is the full URL) and create a `.forkie` directory inside the current directory as well as a directory for the repo including a `.bin` (which contains the users cookie) and a `b2.json` which contains the b2 backblaze keys used to access the forkie bucket
- The `login` subcommand will ask the user if they want to create an account if no account is found on the web server
- You can then use any of the commands listed below

#### The subcommands

**The subcommands require you to be in the same directory as the `.forkie` directory**. You can view all usages by using the `--help` option...

- *make*: start tracking new file in repository
  - Usage:
    - `forkie make [-v | --verbose] [(-m <message>)] (<file>)...`
    - Will search through all the available repository cookies inside the `.forkie` directory and prompt the user as to which they want to add to and then prompt which group to add to
    - If an identical file is found then forkie will prompt the user to either start tracking the new file or to use the `update` subcommand instead
    - The ellipsis denotes that more than one file can be specified (with optional name)
    - If no `<message>` argument is given then the default editor will be opened
  - Options:
    - -m --message: The message/description of the file.
    - -v --verbose: Display info about the inner workings
- *update*: create revision to file
  - Usage:
    - `forkie update [-v | --verbose] [(-m <message>)] (<file>)...`
    - The `update` subcommand works in a similar way to the `make` subcommand
    - Will first find every file that matches the filename of `<file>` in every repository in `.forkie` directory
    - The user then gets to pick which repository to update. If one of the files isn't contained inside the chosen repository then the user can either continue with the ones that or abort
    - If the user uploads a verion that matches the current version inside the chosen repository then uploading will be aborted and the user is prompted
  - Options:
    - -m --message: The message/description of the file.
    - -v --verbose: Display info about the inner workings
- *find*: find a file/list files
  - Usage:
    - `forkie find (-a | -n <name> [(-p <group>)]) [-vd] [(-c <comment>) [-f | --force]]`
    - The `-a` option returns all files in every repository in `.forkie`
    - If the `-n` is specified then it will search all repos by filename. The optional `-p <group>` is used to also search by group name
    - You can download any of the returned files by adding the `-d` option
    - Bulk commenting can be done by adding the `-c <comment>` option and argument. Force `-f` can be used not ask for permissions
  - Options:
    - -a: All files
    - -n: Search by name
    - -p: Search by group name
    - -v --verbose: Verbose
    - -c --comment: Bulk comment
    - -f --force: Force/Don't ask for permission first
- *group*: command to handle everything to do with groups
  - Usage:
    - `forkie group (-V [--peeps] [<email>...] | (--add | --rm | --change) (-p <group>) [<email>]) [-vf]`
    - Four main options:
      - View: view all groups, or just peeps by using `--peeps`, and filter by email (only can view the groups that the user is a part of)
      - Add: if only `-p` is specified then it will create a group with name `<group>`. If `-p` and `<email>` is specified then it will add the user of the given email and add them to the group of `<group>` (only if you are the groupleader).
      - Remove: remove group by just specifying '-p' or a remove a user from the `<group>` by also specifying the user's `<email>` (only if you are the group leader)
      - Change: rename the group by just specifying `-p` or move a user to another group by also specifying the user's `<email>` (only if you are the group leader of both groups)
    - All of these, except view, all require permission (y/n) to complete the chosen action
  - Options:
    - --peeps: View people
    - --add: Add person/people to a group
    - --rm: Remove person/people from a group
    - --change: Move person/people to another group
- *report*: for generating and viewing reports about groups/users
  - Usage:
    - `forkie report (-p <group> | <email>) [(-o <file>)] [-v | --verbose]`
    - Generate a PDF report containing information on:
      - On a group using `-p`
      - On an individual user by specifying the user's `<email>`
    - Specify the local output path of the PDF by using `-o`
- *login*: "logs into" the web server to authenticate the users identity. Then will create a bin file containing the cookie that will authenticate the user in the web server
  - Usage:
    - `forkie login (<repo>) [-v | --verbose]`
    - Used to login to the repo with the URL of `<repo>`
    - Will suggest the user to signup if their credentials aren't found on the repository

#### Helpful Links

How to connect to Postgres with Python:
<https://dev.to/paultopia/the-easiest-possible-way-to-throw-a-webapp-online-flask--heroku--postgres-185o>

Flask Docs
<http://flask.palletsprojects.com/en/1.1.x/>

Creating APIs with Flask
<https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask>

B2 Backblaze service
<https://www.backblaze.com/>

b2sdk docs
<https://b2-sdk-python.readthedocs.io/en/master/index.html>
