import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from random import randint
from datetime import datetime
from datetime import date

app = Flask(__name__)

DATABASEURI = 'postgresql://localhost/nhulam'

engine = create_engine(DATABASEURI)

engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace doan'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/')
def index():
  students = get_students()
  return render_template("index.html", students = students)

@app.route('/add', methods=['POST'])
def add(): 
  try: 
    fname = request.form['fname']
    lname = request.form['lname']
    program = request.form['program']
    status = request.form['status']
    tuition = request.form['tuition']
    paid = request.form['paid']

    g.conn.execute("INSERT INTO students (fname, lname, program, status, tuition, paid) VALUES (%s, %s, %s, %s, %s, %s)", fname, lname, program, status, tuition, paid)
    
    return redirect('/')
  except: 
    return redirect('/')

# HELPER FUNCTIONS

def get_students(): 
    
    students = {} 

    cursor = g.conn.execute("SELECT * from students"); 
    for student in cursor: 
        sid = student['id']
        fname = student['fname']
        lname = student['lname']
        program = student['program']
        status = student['status']
        tuition = student['tuition']
        paid = student['paid']
        balance = student['balance']
        
        students[sid] = (sid, fname, lname, program, status, tuition, paid, balance)

    return students



if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()