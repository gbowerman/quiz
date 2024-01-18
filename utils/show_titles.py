#!/usr/bin/python3

''' show_titles.py - list the available quizzes in the quiz DB'''
import os
import psycopg2
from dotenv import load_dotenv

# load environment
load_dotenv()

conn = psycopg2.connect(
        host=os.environ['HOST'],
        database=os.environ['DATABASE'],
        user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD'])

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a command: get a list of titles
cur.execute('SELECT title_id, title FROM titles;')
result = cur.fetchall()

for row in result:
    print(f"Title_id: {row[0]}, Title: {row[1]}\n")

cur.close()
conn.close()
