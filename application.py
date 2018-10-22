import os
import psycopg2,requests

from flask import Flask, session, render_template, request,flash,url_for,redirect,logging
from flask_session import Session
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from postgres import Postgres
from functools import wraps

app = Flask(__name__)

# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
#engine = create_engine(os.getenv("DATABASE_URL"))#postgresql://localhost:5432/postgres
#db = scoped_session(sessionmaker(bind=engine))

conn = psycopg2.connect("host=localhost dbname=postgres user=postgres password=raghuram771231")


# initially opens up the registration page after the flask is run
@app.route("/")
def index():
    return render_template("index.html")

#registration form class-----------------------
class RegisterForm(Form):
    email=StringField('email',[validators.Length(min=6,max=100)])
    password=PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm',message='passwords do not match')])
    confirm=PasswordField('Confirm Password')

#user registration--------------------------
@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        email=form.email.data
        password=sha256_crypt.encrypt(str(form.password.data))

        cur = conn.cursor()
        cur.execute("insert into users values(%s,%s)",(email,password))
        conn.commit()
        cur.close()

        flash('you are now registered and can login.','success')
        return redirect(url_for('Login_Page'))

    return render_template('register.html',form=form)

#user login---------------------------------------
@app.route("/Login_Page",methods=["GET","POST"])
def Login_Page():
    if request.method=='POST':
        #get form fields
        email=request.form['email']
        password_candidate=request.form['password']

        cur = conn.cursor()
        #get user by email
        cur.execute("select * from users where email=%s",[email])
        result =cur.rowcount

        if result >0:
            #get stored hash
            data=cur.fetchone()
            password=data[1]

            #compare passwords
            if sha256_crypt.verify(password_candidate,password):
                #passed
                session['logged_in']=True
                session['email']=email

                flash('you are now logged in','success')
                return redirect(url_for('dashboard'))
            else:
                error='Invalid Login'
                return render_template('Login_Page.html',error=error)
            cur.close()
        else:
            error='email not found'
            return render_template('Login_Page.html',error=error)
    return render_template("Login_Page.html")

#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else:
            flash('unauthorized,please login','danger')
            return redirect(url_for('Login_Page'))
    return wrap

#logout
@app.route('/logout')
def logout():
    session.clear()
    flash('you are now logged out','success')
    return  redirect(url_for('Login_Page'))

#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template("dashboard.html")

#result displayed for isbn search-----------------------------
@app.route("/result_isbn",methods=["POST"])
def result_isbn():
    if request.method=="POST":
        isbn=request.form.get("search_isbn")

        cur = conn.cursor()
        cur.execute("select * from book where isbn=%s",[isbn])
        books=list(cur.fetchall())
        if list(books) is None:
            return render_template('error.html',message="NO book with the required isbn.")
        cur.close()
    return render_template('search_results.html',books=list(books))

#result displayed for title search------------------------------
@app.route("/result_title",methods=["POST"])
def result_title():
    if request.method=="POST":
        title=request.form.get("search_title")

        cur = conn.cursor()
        cur.execute("select * from book where title=%s",[title])
        books=list(cur.fetchall())
        if list(books) is None:
            return render_template('error.html',message="NO book with the required isbn.")
        cur.close()
    return render_template('search_results.html',books=list(books))

#result displayed for author search---------------------------------
@app.route("/result_author",methods=["POST"])
def result_author():
    if request.method=="POST":
        author=request.form.get("search_author")

        cur = conn.cursor()
        cur.execute("select * from book where author=%s",[author])
        books=list(cur.fetchall())
        if list(books) is None:
            return render_template('error.html',message="NO book with the required isbn.")
        cur.close()
    return render_template('search_results.html',books=list(books))

#book page
@app.route("/book/<string:book_id>",methods=["GET","POST"])
def book(book_id):
    cur = conn.cursor()

    #make sure book exist
    cur.execute("select * from book where isbn=%s",[book_id])
    books = cur.fetchall()
    print(books)
    if books is None:
        return render_template('error.html', message="No book with the required isbn.")

    KEY ="YskmXuxTfMdJvWVKY57mg"
    res = requests.get("https://www.goodreads.com/book/review_counts.json?isbns=book_id&key=KEY",params={"key":KEY, "isbns":book_id})
    if res.status_code !=200:
       return render_template('error.html', message="API request unsuccessful.")
    data=res.json()
    review=data["books"]
    cur.close()
    return render_template('book.html',books=books,review=list(review))




if __name__== '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

