# The MovieGEEK Installation Guide

The MovieGEEK is a website initially implemented to accompany my book, Practical Recommender Systems. 
However, this folder is used for the manning LiveProject, which is currently in MEAP. 
 
The website is not intended as a standalone tutorial or a plug-and-play website for you to install and 
use for your content. 

## Thanks!
This site would not be working if it wasn’t for the [MovieTweetings](https://github.com/sidooms/MovieTweetings) 
dataset and the poster images provided by the [themoviedb.org](https://www.themoviedb.org) API. 
I wish to extend a big thanks to both of them for all their work.

## Project Setup
In the following, we will go through the steps to set up this site. 

The first thing is to download this repository. Secondly, create a themoviedb.org ID needed to run the website. 

### Download source code
You have two choices for downloading the source code – downloading a zip file of the source code or using Git. 

* *Downloading a zip file*
 
   From the main [MovieGEEK directory on GitHub](https://github.com/practical-recommender-systems/moviegeek), 
   click the green “Clone or download” button and choose to download a zip file to your computer.
   
* *Using Git*

   Clone this repository or create a fork in your GitHub, and then clone that instead. The following command 
   will create a copy on your computer.
   `> git clone https://github.com/kimfalk/live-project.git`

 
###  Create an ID for themoviedb.org

You have to create an ID with themoviedb.org to use its pictures.

* Go to [https://www.themoviedb.org/account/signup](https://www.themoviedb.org/account/signup) 
* Sign up
* Login, go to your account settings and [create an API](https://www.themoviedb.org/settings/api). You can access 
settings by clicking the avatar in the upper right-hand corner (the default is a blue circle with a white logo in it). 
Then you’ll see settings on the left. 
* Create a file in the moviegeek directory called ".prs" 
* Open .prs and add { "themoviedb_apikey": <INSERT YOUR APIKEY HERE>}
Remember to remove the "<" and ">" When you are finished, the file contents should look something like 
{"themoviedb_apikey": "6d88c9a24b1bc9a60b374d3fe2cd92ac"}


## Running the site 

There are two ways to run the site:
 * [use Docker container](#run-site-in-a-docker-container) 
 * [run it in a local virtual environment](#run-site-in-a-virtualenv). 

I recommend the first option, as the docker container way is faster and requires less setup. 

### Run site in a Docker container 

As a new addition to this site, this repo will also have a docker container, which should make it 
easier to start. 

Fire up the website simply by first building the docker container

```shell script
docker-compose build web
```
Create the database and download and import data: (This takes some time)
```shell script
./db-migrate.sh
```

And then start it executing the following:

```shell script
docker-compose up web
```

NB: If the website responds with an error about a ```.prs``` file missing, its because you skipped 
the section about creating a themoviedb.org id. [link](#create-an-id-for-themoviedborg)
 
(to close it again by stopping the process (Cltr+C))

### Run site in a virtualenv. 

### Install Python 3.x
 
The MovieGEEK website requires that you have Python 3.x installed. Practical Recommender Systems does not teach you 
Python, though. You’ll need to be able to read Python code to understand the algorithms, and, of course, programming 
experience makes it easier to implement the website. 

The [Hitchhikers guide to Python](http://docs.python-guide.org/en/latest/) provides “both novice and expert Python 
developers a best practice handbook to the installation, configuration, and usage of Python on a daily basis.” 
Mac and Linux users should follow instructions in this guide. 

Windows users, because installing Python and its packages can be tricky for you, I recommend using the 
[Anaconda](https://www.anaconda.com/distribution/) package for the simplest install. 
If you want to, you can use the Windows instructions in the Hitchhiker’s Guide, 
but I have always used the Anaconda package.

## Create a virtual environment for the project

Before you run the code, create a virtual environment. The Hitchhiker’s Guide provides a 
[good overview](https://docs.python-guide.org/dev/virtualenvs) 
if you want more information. Verify that you have virtualenv installed, and if not, read more 
[here](https://docs.python-guide.org/dev/virtualenvs/#lower-level-virtualenv). 
If you followed the Hitchhiker’s Guide or used Anaconda, it should already be installed, though. Use 
this command to verify it’s installed:

```bash
> virtualenv --version
```

Once you have confirmed you have virtualenv installed, create the virtual environment using the following 
commands (Anaconda users, please use the Anaconda-specific commands):

*   *Non-Anaconda users*:
    ```bash
    > cd live-project
    > virtualenv -p python3 prs
    > source prs/bin/activate
    ```
*   *Anaconda users*:
    ```bash
    > cd live-project
    > conda create -n prs python=3.6
    > conda activate prs
    ```
    Note that 3.6 should be replaced with 3.x, with x representing the version you are using. 

### Get the required packages
There are Anaconda specific instructions for this step, too; be sure to use those if they apply!


*   *Non-Anaconda users* 

    Use pip to install the required files:
    ```bash
    > pip3 install -r requirements.txt
    ```
*   *Anaconda users*

    Thanks, TechnologyScout.net for these instructions:
    ```bash
    > while read requirement; do conda install --yes $requirement; done < requirements.txt    
    ```
    
## Database setup

Django is setup to run with Sqllite3 out of the box, which is enough to run everything. However, some 
things will be considerably faster if you install PostGreSQL. 

*   If you do want to install Postgres, follow the Postgres installation steps before you create the databases. 
*   If you don’t want to install Postgres, jump to *Create and populate the MovieGEEKS databases* section.

### [PostGreSQL-OPTIONAL] Install and use PostGreSQL

Django comes with a database that enables you to run the website without an external database. However, using another 
database makes it faster. I had good experiences using the PostGreSQL db.
 
####  Install and run PostGreSQL
First, install Postgres and run it. 
Download the correct postgresql version for your operating system [here](https://www.postgresql.org/download/),
 and follow the instructions on from the download page to install and run it. 

#### Create the database for MovieGEEK 

Use PostGreSQL’s admin tool pgadmin to create a database. Name it `moviegeek`. Write down which username and password you usd to create the database. You will use that information in two steps from now when you change the Django settings.

#### Install the Python database driver 

Once the PostGreSQL database is spinning, it’s time for the Python driver, which enables Django to talk with the 
database. I recommend using [Psycopg](https://www.psycopg.org/). Download it [here](https://pypi.org/project/psycopg2/). 
Install it following these [instructions](https://www.psycopg.org/docs/install.html). 

####  Configure the Django database connection to connect to PostGreSql

If you use a PostGreSQL (or another db) you need to configure the Django database connection for MovieGEEKS, follow 
these steps. Refer to Django docs here if you need more details. 

Open `prs_project/settings.py` 

Update the following:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'moviegeek',                      
        'USER': 'db_user',
        'PASSWORD': 'db_user_password',
        'HOST': 'db_host',
        'PORT': 'db_port_number',
    }
}
```
Update the USER, PASSWORD, HOST, and PORT fields:
* USER(db_user): Use the user name you created with the MovieGEEK database
* PASSWORD(db_user_password): Use the password you created with the MovieGEEK database
* HOST (db_host): localhost (if you have have installed it on your private machine)
* PORT (db_port_number): 5432 (the default port)

For more information please refer to the Django documentation [link](https://docs.djangoproject.com/en/2.2/ref/databases/)

### Create and populate the MovieGEEKS databases
Everyone must follow these steps, whether or not you are using PostGreSQL.

#### Create the MovieGEEKS databases

When the database connection is configured, you can run the following commands to create the databases that Django 
and this website need to run.

```bash
> python3 manage.py makemigrations
> python3 manage.py migrate --run-syncdb
```

#### Populate the database 
Run the following script to download the datasets for the MovieGEEKS website. 

WARNING: Mac users running Python 3.7 or higher, before you populate the databases, you need to run this command. 
`/Applications/Python\ 3.7/Install\ Certificates.command`. More details [here](https://bugs.python.org/issue28150)
 and [here](https://timonweb.com/tutorials/fixing-certificate_verify_failed-error-when-trying-requests_html-out-on-mac/).

Everyone, run these commands to populate the databases.
```bash
> python3 populate_moviegeek.py
> python3 populate_ratings.py
```
WARNING: This might take some time.

### Start the web server
To start the development server, run this command:
```bash
> python3 manage.py runserver 127.0.0.1:8000
```
Running the server like this will make the website available [http://127.0.0.1:8000](http://127.0.0.1:8000) 

WARNING: Other applications also use this port so you might need to try out 8001 instead.

NB: If the website responds with an error about a ```.prs``` file missing, its because you skipped 
the section about creating a themoviedb.org id. [link](#create-an-id-for-themoviedborg)

## Closing down
When you are finished running the project you can close it down doing the following steps, or simply close the 
terminal where the server is running. 

* Close down the server by pressing -c
* Exit the virtual environment

Non-Anaconda users
```bash
>  deactivate
```
Anaconda users
```bash
> conda deactivate
```

## Restart

To restart the project again do the following:

*   *Non-Anaconda users*:
    ```bash
    > cd moviegeek
    > source prs/bin/activate
    ```
*   *Anaconda users*:
    ```bash
    > cd moviegeek
    > conda activate prs
    ```
    
Start the web server again by running the following command:
```bash
> python3 manage.py runserver 127.0.0.1:8000
```
