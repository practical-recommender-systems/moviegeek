# moviegeek

The MovieGEEKs is a movie site implemented to accompany my book
["Practical Recommender Systems"](https://www.manning.com/books/practical-recommender-systems).
It is used in the book to show how recommender systems work, and how you can implement them. 

The book is still being written, and so this is still under construction.

# installation guide:

This site is using the [MovieTweetings](https://github.com/sidooms/MovieTweetings) dataset, and uses 
[themoviedb.org](www.themoviedb.org) to get poster images. 
A big thanks to both of them for all their work. Please go and visit them. 
 
The dataset is used in the populate_moviegeek script which downloads it and imports the data 
into the database configured in Django. 

* download code
* run the following two commands to create the dbs.
  * `python manage.py makemigrations`
  * `python manage.py migrate`
* run `populate_moviegeek.py` to populate the db. (WARNING: this might take some time.)
* start the web server by doing python manage.py runserver.
* go to http://docs.themoviedb.apiary.io/# and create an api_key
* create a file in the root of the directory called "`.prs`" and add 
`{ "themoviedb_apikey": <INSERT YOUR APIKEY HERE>}`.