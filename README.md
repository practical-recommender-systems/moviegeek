# The MovieGEEK

The MovieGEEK is a movie site implemented to accompany my book
["Practical Recommender Systems"](https://www.manning.com/books/practical-recommender-systems).
It is used in the book to show how recommender systems work and how you can implement them. The book describes how the algorithms work, and provides more detail into how the site works.  

# Installation guide:

This site would not be working if it wasnt for the  [MovieTweetings](https://github.com/sidooms/MovieTweetings) dataset, and the poster images provided by the  
[themoviedb.org](https://www.themoviedb.org) API. A big thanks to both of them for all their work.
 
## Project Setup
The following is expecting you to have python 3.x installed on your machine. I recommend looking at the [Hitchhikers guide to Python](http://docs.python-guide.org/en/latest/) if you haven't.
 
For *windows users* it's a good idea to install the Anaconda package. Anaconda is the leading open data science platform powered by Python (according to their homepage) [Anaconda](https://www.continuum.io/downloads)
 
### Download code
Retrieve the source code either by downloading a zip-file (click the green button above that says `Clone or download`) or using git. 

Using git, you can either clone this repository or create a fork in your github, and then clone that instead. The following command will create a copy on your computer. 

```bash
> git clone https://github.com/practical-recommender-systems/moviegeek.git
```
### Create a virtual environment for the project 
Before running the code it is a good idea to create a virtual environment
(Look at the following guide for more details [guide](http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtualenvironments-ref)).
Create the virtual env using the following commands (assumes that you have virtualenv installed)
 
```bash
> cd moviegeek
> virtualenv -p python3 prs
> source prs/bin/activate
```

Note: if you are running Anaconda you should conda virtual environment instead( ```conda create -n myenv python=3.6```)

### Get the required packages
using Pip you can now install the required files:
```bash
pip3 install -r requirements.txt
```
Again it is slightly different for conda users, they should run (thanks to https://www.technologyscout.net/2017/11/how-to-install-dependencies-from-a-requirements-txt-file-with-conda/):
```bash 
while read requirement; do conda install --yes $requirement; done < requirements.txt
```


## Database setup
Django is setup to run with sqllite3 out of the box, which is enough to run everything. 
However, some things will be considerably faster if you install Postgres.

If you are not installing Postgres, please jump to configuration. 

### [OPTIONAL] install and use PostGreSQL

#### The Postgres database
You need a Postgres database running. It can be downloaded from the following site:

Get it here [postgresql download](https://www.postgresql.org/download/) 
and follow the instructions on the site.

When it installed and running, create a database. 
In the following, the database is called `moviegeek`. You can do this using the admin tool (pgadmin)

#### The database driver (only if you are running Postgres)
When the Postgres database is spinning its time for the python driver. I recommend using the following 
[http://initd.org/psycopg/](http://initd.org/psycopg/). Follow the instructions on the site (https://www.psycopg.org/docs/install.html)

### Configuration of Django database connection

To update the database in MovieGEEKS go to in prs_project/settings.py 
and update the following 

```bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'db_name',                      
        'USER': 'db_user',
        'PASSWORD': 'db_user_password',
        'HOST': '',
        'PORT': 'db_port_number',
    }
}
```
you should update the NAME, USER, PASSWORD, HOST, PORT fields.

### Create the dbs (for all databases)
If you have a database running on your machine I would encourage 
you to connect it, by updating the settings in `prs_project/settings.py` (fx like shown above). 

To set up another database is described in the Django docs [here](https://docs.djangoproject.com/en/2.0/ref/databases/)

When the database connection is configured you can now run the following commands. This will create the 
databases the Django and this website needs to run. 

```bash
> python3 manage.py makemigrations
> python3 manage.py migrate --run-syncdb
```
When the databases are created, its time to put some data in them. This is described in the following section:

### Populate the db by running the following script. 

The following script will download the datasets used on the website. 

(WARNING: this might take some time.)
(WARNING: If you are using python >3.6 on a Mac then you need to run 
"/Applications/Python\ 3.7/Install\ Certificates.command". More details [here](https://bugs.python.org/issue28150) and [here](https://timonweb.com/tutorials/fixing-certificate_verify_failed-error-when-trying-requests_html-out-on-mac/)
```bash
> python3 populate_moviegeek.py
> python3 populate_ratings.py
```

### Create a themoviedb.org id
To be allowed to use themoviedb.org's pictures you need to create an account there. 

* go to [https://www.themoviedb.org/account/signup](https://www.themoviedb.org/account/signup) and create an api_key
* create a file in the root of the directory called "`.prs`" and add 
`{ "themoviedb_apikey": <INSERT YOUR APIKEY HERE>}`.
(remember to remove the "<" and ">") 
When you are finished, the file contents should look something like 
```{"themoviedb_apikey": "6d88c9a24b1bc9a60b374d3fe2cd92ac"}```

### Start the web server
 To start the development server run:
```bash
> python3 manage.py runserver 127.0.0.1:8000
```
Running the server like this, will make the website available 
[http://127.0.0.1:8000](http://127.0.0.1:8000) other applications also use this port
so you might need to try out 8001 instead. 

### Closing down.
when you are finished running the project you can:
* Close down the server by pressing <CLTR>-c  
* exit the virtual env:
```bash
> deactivate
```
if running conda run instead:
```bash
conda deactivate
```
