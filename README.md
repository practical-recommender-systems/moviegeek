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

## Project Setup
The following is expecting you to have python 3.x installed on your machine. I recommend
 looking that the [Hitchhikers guide to Python](http://docs.python-guide.org/en/latest/) if you 
 haven't.
 
 For windows users it's a good idea to install the Anaconda package. Anaconda is the leading open 
 data science platform powered by Python (according to their homepage) [Anaconda](https://www.continuum.io/downloads)
 
### Download code
```bash
> git clone https://github.com/practical-recommender-systems/moviegeek.git
```
### Create a virtual environment for the project 
Look at the following guide for more details [guide](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenvironments-ref)
 
```bash
> cd moviegeek
> virtualenv prs
> source prs/bin/activate
```

if you are running Anaconda you can also use conda virtual environment instead.
### Get the required packages

```bash
pip install -r requirements.txt
```

### Create the dbs. 
If you have a database running on your machine I would encourage 
you to connect it, by updating the settings in `prs_project/settings.py`. To set up another database is 
described in the Django docs [here](https://docs.djangoproject.com/en/1.10/ref/databases/)
```bash
> python manage.py makemigrations
> python manage.py migrate
```
### Populate the db by running the following script. 
(WARNING: this might take some time.)
(WARNING: If you are using python >3.6 on a Mac then you need to run 
"/Applications/Python\ 3.6/Install\ Certificates.command". More details [here](https://bugs.python.org/issue28150))
```bash
> python populate_moviegeek.py`
```
### Start the web server
 To start the development server run:
```bash
> python manage.py runserver 127.0.0.1:8000
```
Running the server like this, will make the website available 
[http://127.0.0.1:8000](http://127.0.0.1:8000) other applications also use this port
so you might need to try out 8001 instead. 

### Create a themoviedb.org id
* go to [https://www.themoviedb.org/account/signup](https://www.themoviedb.org/account/signup) and create an api_key
* create a file in the root of the directory called "`.prs`" and add 
`{ "themoviedb_apikey": <INSERT YOUR APIKEY HERE>}`.
(remember to remove the "<" and ">")

### Closing down.
* when you are finished running the project you can exit the virtual env:
```bash
> deactivate
```
