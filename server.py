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
  payments = get_payments()

  context = dict(students=students, payments=payments)
  
  return render_template("index.html", **context)

@app.route('/add_student', methods=['POST'])
def add_student(): 
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

@app.route('/add_payment', methods=['POST'])
def add_payment(): 
  try: 
    uuid = request.form['uuid'].strip() #Remove trailing whitespace

    student = get_specific_student(uuid)
    fname = student['fname']
    lname = student['lname']
    date = request.form['date']
    amount = request.form['amount']

    #Insert into payments table
    g.conn.execute("INSERT INTO payments (student_id, fname, lname, date, amount) VALUES (%s, %s, %s, %s, %s);", uuid, fname, lname, date, amount)

    #Update paid column in corresponding student 
    g.conn.execute("UPDATE students s SET paid=paid+%s WHERE s.student_id=%s", amount, uuid)
 
    return redirect('/')
  except Exception as e: 
    print(e)
    return redirect('/')

@app.route('/generate_receipt', methods=['POST'])
def generate_receipt(): 
  try:
    uuid = request.form['uuid'].strip()
    
    student = get_specific_student(uuid)
    fname = student['fname']
    lname = student['lname']

    print(fname)
    print(lname)

    payments = get_payments_from_specific_student(uuid)

    f = open('[' + uuid + '] ' + fname + " " + lname + '\'s receipt', "w+")
    f.write("CLOUD NINE BEAUTY SCHOOL RECEIPT\n")

    entry_count = 1 
    for key, value in payments.items(): 
      f.write(str(entry_count) + ". " + str(value[0]) + "\t" + str(value[1]) + "\n")
      entry_count += 1

    return redirect('/')
    
  except Exception as e: 
    print(e)
    return redirect('/')


# HELPER FUNCTIONS

def get_students(): 
    try:
      students = {} 

      cursor = g.conn.execute("SELECT * from students")
      for student in cursor: 
          sid = student['student_id']
          fname = student['fname']
          lname = student['lname']
          program = student['program']
          status = student['status']
          tuition = student['tuition']
          paid = student['paid']
          balance = student['balance']
          
          students[sid] = (sid, fname, lname, program, status, tuition, paid, balance)

      return students
    except: 
      return redirect('/')

# Get the student corresponding to the given id (there should only be one)
def get_specific_student(uuid): 
  try:
    cursor = g.conn.execute("SELECT * from students s where CAST(s.student_id as uuid)=%s", uuid)
    for student in cursor: 
      return student

  except: 
    return redirect('/')

def get_payments():
  try: 
    payments = {}

    cursor = g.conn.execute("SELECT * from payments")
    for payment in cursor: 
      sid = payment['student_id']
      pid = payment['payment_id']
      fname = payment['fname']
      lname = payment['lname']
      date = payment['date']
      amount = payment['amount']

      payments[pid] = (sid, pid, fname, lname, date, amount)

    return payments

  except: 
    return redirect('/')

def get_payments_from_specific_student(uuid): 

  try: 
    payments = {}

    cursor = g.conn.execute("SELECT * from payments p where p.student_id=%s", uuid)
    for payment in cursor: 
      pid = payment['payment_id']
      date = payment['date']
      amount = payment['amount']

      payments[pid] = (date, amount)

    return payments

  except: 
    return redirect('/')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='localhost')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()