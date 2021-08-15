# syntax=docker/dockerfile:1
FROM python:3.6
ENV PYTHONUNBUFFERED=1
WORKDIR /moviegeek
COPY requirements.txt /moviegeek/
RUN pip install -r requirements.txt
COPY . /moviegeek/
#RUN python populate_moviegeek.py
#RUN python populate_ratings.py
