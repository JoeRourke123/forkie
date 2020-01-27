## file-rep0
Group 9 Project for CS1813 Assignment 1

Hosted at: https://file-rep0.herokuapp.com

### Database Examples
#### Querying a database table
To query a db table for an API endpoint simply do the following:
- I'm gonna use the FileVersionTable as an example, all the tables will be imported at the top of the app.py
`
FileVersionTable.query.filter_by(fileid=ID_TO_FETCH_FILES_OF)
`
- This will return all the files with the fileid that you pass it (replacing ID_TO_FETCH_FILES_OF)
- You can add `.first()` to just get the first result from the query if you only want a specific result

#### Inserting into the database
- To insert into the database, you need to create an instance of the table you're inserting to and pass it the data to add - like so:
- This time I'm using the MetadataTable
`
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
`
- After the insert you could return that it was successful or something like that
- Be sure to read the fields required for a table before you insert into it



### Helpful Links
How to connect to Postgres with Python:
https://dev.to/paultopia/the-easiest-possible-way-to-throw-a-webapp-online-flask--heroku--postgres-185o

Flask Docs
http://flask.palletsprojects.com/en/1.1.x/

Creating APIs with Flask
https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask


### How to connect Heroku to your local Git repo
1. Clone the repo from here
2. Enter it in the terminal
3. Enter... `heroku git:remote -a file-rep0`
4. Then when you want to upload to the server enter... `git push heroku master`
