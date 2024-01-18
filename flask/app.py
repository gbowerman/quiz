import os
import psycopg2
import uuid
from flask import Flask, render_template, request

app = Flask(__name__)

# connect to named DB, getting credentials from environment
# to do: add SQL exception handling to all the SQL calls
def connect_db():
    conn = psycopg2.connect(
        host=os.environ['HOST'],
        database=os.environ['DATABASE'],
        user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD'])
    return conn

'''Create a new session'''
def create_session(session_guid, conn, quiz_id):
        cur = conn.cursor()
        # remove any leftover sessions
        # session_cleanup(4)

        # add an entry to the sessions table
        sql_stmt = f"INSERT INTO sessions VALUES('{session_guid}', current_timestamp, {quiz_id}, 0, 0);"
        cur.execute(sql_stmt)

        # load the session questions to the session_qs table
        sql_stmt = f"INSERT INTO session_qs (session_id, question, answer, num_answers) SELECT '{session_guid}', question, answer, num_answers FROM questions WHERE title_id = {quiz_id};"
        cur.execute(sql_stmt)
        # print(f'{cur.rowcount} rows loaded into session_qs for session: {self.session_guid}')
        conn.commit()
        cur.close()

'''Get a random question and related data for a session'''
def get_question(session_guid, conn):
    sql_qry = f"SELECT question, q_id, num_answers FROM session_qs where session_id = '{session_guid}' ORDER BY random() LIMIT 1;"
    # Open cursor
    cur = conn.cursor()
    cur.execute(sql_qry)
    if cur.rowcount == 0: # no questions left
         cur.close()
         return None
    q_set = cur.fetchone()
    cur.close()
    return q_set

''' get the answer for a specific question'''
def get_answer(session_id, conn, question_id):
    sql_qry = f"SELECT answer, num_answers FROM session_qs where session_id = '{session_id}' and q_id = '{question_id}';"
    
    # Open cursor
    cur = conn.cursor()
    cur.execute(sql_qry)
    answer_set = cur.fetchone()
    cur.close()
    return answer_set

'''Check user answer against correct answer'''
def check_answer(attempt, session_id, conn, question_id):
    # get the right answer
    answer_set = get_answer(session_id, conn, question_id)
    answer = answer_set[0]
    num_answers = answer_set[1]
    verdict = ""
    correct = "Correct"
    incorrect = f"Answer is: {answer}"
    result = 1

    for i in range(num_answers):
            # check if more than one answer possible
            if answer[0] == '[':
                result = 0
                answer_list = answer[1:-1].split(',')
                for row in answer_list:
                    if attempt[i].casefold() == row.casefold(): # if anwer matches any of the options it's correct
                        result = 1
                if result == 0: # if one part of a multi-answer question is wrong, fail
                    return incorrect
            else:
                if attempt[i].casefold() == answer.casefold():
                    result = 1
                else:
                    result = 0
    if result == 0:
         verdict = incorrect
    else:
         verdict = correct
    return verdict

'''update session data when a question is answered correctly'''
def session_correct(session_id, conn, q_id):
    cur = conn.cursor()
    # update score
    sql_stmt = f"UPDATE sessions SET score = score + 1, q_count = q_count + 1 WHERE session_id = '{session_id}';"
    cur.execute(sql_stmt)

    # remove question from the session_qs table
    sql_stmt = f"DELETE FROM session_qs WHERE q_id = {q_id};"
    cur.execute(sql_stmt)
    conn.commit()
    cur.close()

'''update session data when a question is answered incorrectly'''
def session_incorrect(session_id, conn):
    cur = conn.cursor()
    # update question count but not score
    sql_stmt = f"UPDATE sessions SET q_count = q_count + 1 WHERE session_id = '{session_id}';"
    cur.execute(sql_stmt)
    conn.commit()
    cur.close()

'''print out the current score'''
def session_report(session_id, conn):
        report = ""
        cur = conn.cursor()
        sql_stmt = f"SELECT score, q_count FROM sessions WHERE session_id = '{session_id}';"
        cur.execute(sql_stmt)
        if cur.rowcount == 0:
            report = f'No session found. Session id: {session_id}'
        else:    
            result = cur.fetchone()
            score = result[0]
            q_so_far = result[1]
            report = f'Score: {score}/{q_so_far}'
        cur.close()
        return report

'''clean up the session metadata'''
def session_close(session_id, conn):
        cur = conn.cursor()
        # delete any remaining session questions
        sql_stmt = f"DELETE FROM session_qs WHERE session_id = '{session_id}';"
        cur.execute(sql_stmt)

        # delete session from sessions table
        sql_stmt = f"DELETE FROM sessions WHERE session_id = '{session_id}';"
        cur.execute(sql_stmt)
        conn.commit()
        cur.close()

def session_cleanup(conn, hrs):
    cur = conn.cursor()
    sql_stmt = f"SELECT session_id FROM sessions WHERE session_start < current_timestamp - interval '{hrs} hours'"
    cur.execute(sql_stmt)
    if cur.rowcount == 0:
        cur.close()
        return
    result = cur.fetchall()
    print(f'Deleting {cur.rowcount} sessions')
    for row in result:
        session_id = row[0]
        session_close(session_id, conn)
    cur.close()

'''main page - show a list of quiz titles'''
@app.route('/')
def index():
    # connect to quiz_db
    conn = connect_db()
    
    # remove any leftover sessions
    session_cleanup(conn, 4)
    
    # query the title_id
    cur = conn.cursor()
    sql_stmt = f"SELECT title_id, title FROM titles;"
    cur.execute(sql_stmt)
    titles = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', titles=titles)

# activated when user presses the quit button
@app.route('/quit')
def quit():
    session_id = request.args.get('session_id', None)

    # connect to quiz_db
    conn = connect_db()

    summary = session_report(session_id, conn)
    session_close(session_id, conn)

    conn.close()
    return render_template('end.html', summary=summary)
     
# creates a session and renders the first question
@app.route('/quiz')
def quiz():
    quiz_id = request.args.get('quiz_id', None)

    # connect to quiz_db
    conn = connect_db()
    
    # create a session
    session_guid = uuid.uuid4()
    create_session(session_guid, conn, quiz_id)

    # get the first question
    q_set = get_question(session_guid, conn)
         
    question = q_set[0]
    question_id = q_set[1]
    num_answers = q_set[2]

    conn.close()
    return render_template('question.html', question=question, session_id=session_guid, question_id=question_id, num_answers=num_answers)

# evaluates an answer and lines up the next question
@app.route('/answer')
def answer():
    question_id = request.args.get('question_id', None)
    session_id = request.args.get('session_id', None)
    answers = request.args.getlist('answer')
    num_answers = request.args.get('num_answers', None)

    # connect to quiz_db
    conn = connect_db()

    # check answer
    verdict = check_answer(answers, session_id, conn, question_id)

    if verdict == "Correct":
         session_correct(session_id, conn, question_id)
    else:
         session_incorrect(session_id, conn)
    
    # get running score
    summary = session_report(session_id, conn)
    # add score to question status string
    verdict = f'{verdict} - {summary}'

    # get the next question
    q_set = get_question(session_id, conn)

    # check if last question
    if q_set is None:
        session_close(session_id, conn)
        conn.close()
        return render_template('end.html', summary=summary)
    
    question = q_set[0]
    question_id = q_set[1]
    num_answers = q_set[2]

    conn.close()
    return render_template('question.html', verdict=verdict, question=question, session_id=session_id, question_id=question_id, num_answers=num_answers)