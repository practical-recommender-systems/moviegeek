# The MovieGEEK Installation Guide

The MovieGEEK is a website implemented to accompany my book, Practical Recommender Systems. 
It is used in the book to show how recommender systems work and how you can implement them. 
The book describes how the algorithms work and provides more detail into how the site works.

The website is not intended as a standalone tutorial or a plug-and-play website for you to install 
and use for your own content. 

## Thanks!
This site would not be working if it wasn’t for the [MovieTweetings](https://github.com/sidooms/MovieTweetings) 
dataset and the poster images provided by the [themoviedb.org](https://www.themoviedb.org) API. 
I wish to extend a big thanks to both of them for all their work.


###  First, Create an ID for themoviedb.org to use their API assets

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


## Project Setup

The project runs through docker-compose, which downloads all the dependencies and starts up a Django web and Postgres server
that talk to each other on your local machine at `http://0.0.0.0:8000/`.

To start the server, run `docker-compose up`. 

## Closing Down and Restart

To restart the project again do the following:
`docker-compose down &&docker-compose up`

To rebuild the docker image and restart the server, do the following: 
`docker-compose down && docker-compose build --pull && docker-compose up`

To check out any additional server logs, use 
`docker-compose logs`