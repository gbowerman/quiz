#!/usr/bin/python3
'''load_quiz.py - load a CSV quiz file into the quiz database'''
import os
import sys
import psycopg2
import csv
from dotenv import load_dotenv

# connect to named DB, getting credentials from environment
def connect_db():
    conn = psycopg2.connect(
        host=os.environ['HOST'],
        database=os.environ['DATABASE'],
        user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD'])
    return conn

# insert a row into the titles table and return the title_id
def add_title(conn, quiz_name):
    # Open cursor
    cur = conn.cursor()

    # insert title
    sql_stmt = f"INSERT INTO titles(title) VALUES('{quiz_name}');"
    cur.execute(sql_stmt)
    conn.commit()

    # query the title_id
    sql_stmt = f"SELECT title_id FROM titles WHERE title = '{quiz_name}';"
    cur.execute(sql_stmt)
    result = cur.fetchone()
    quiz_num = result[0]
    print(f'Quiz created - id: {quiz_num}')
    cur.close()

    return quiz_num

def main():
    # load environment
    load_dotenv()

    # check args
    if (len(sys.argv)) != 2:
        sys.exit("Invalid argument(s). Expecting quiz name.")
    quiz_name = sys.argv[1]

    # connect to quiz_db
    conn = connect_db()

    # open quiz_file and read in data - assume relative path of quiz files
    quiz_path = f"../subjects/{quiz_name}.csv"
    rows_loaded = 0
    with open(quiz_path, "r") as file:
 
        # if file opens ok, add an entry to quiz titles table
        quiz_num = add_title(conn, quiz_name)

        # read in the questions file
        reader = csv.reader(file, delimiter='|')
        # Open cursor
        cur = conn.cursor()
        for row in reader:
            # populate the questions table
            cur.execute("INSERT INTO questions(title_id, question, answer, num_answers) VALUES(%s, %s, %s, %s)",
                        (quiz_num, row[0], row[1], row[2]))
            rows_loaded += 1
        conn.commit()
        cur.close()
    print(f'{rows_loaded} rows loaded')
    conn.close()

if __name__ == "__main__":
    main()
