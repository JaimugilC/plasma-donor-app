from flask import Flask, render_template, redirect, url_for, request, session
import ibm_db
import re
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import socket

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

app = Flask(__name__)
app.secret_key = 'a'

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=54a2f15b-5c0f-46df-8954-7e38e612c2bd.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32733;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt; UID=rrj92864; PWD=maDr7SBpdojnrqgv;", '', '')


@app.route('/')
def home():
    return render_template('login.html', ip=ip)


@app.route('/login', methods=["GET", "POST"])
def login():
    global userid
    msg = " "

    if request.method == "POST":
        email = request.form['email']
        password = request.form['pwd']
        sql = "SELECT * FROM Users WHERE EMAIL=? AND PASSWORD=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.bind_param(stmt, 2, password)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['loggedin'] = True
            session['id'] = account['USERNAME']
            userid = account["USERNAME"]
            session['email'] = account["EMAIL"]
            msg = 'Logged in successfully!'
            return redirect(url_for('search'))
        else:
            msg = "Incorrect Username/Password"
            return render_template('login.html', msg=msg, ip=ip)


@ app.route('/signup', methods=["GET", "POST"])
def signup():
    msg = " "

    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['pwd']
        sql = "SELECT * FROM USERS WHERE USERNAME=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, username)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        if account:
            msg = "Account already exists!"
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = "Invalid Email Address."
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = "Username must contain only alphabets and numbers."
        else:
            insert_sql = "INSERT INTO USERS(EMAIL, USERNAME, PASSWORD) VALUES(?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, email)
            ibm_db.bind_param(prep_stmt, 2, username)
            ibm_db.bind_param(prep_stmt, 3, password)
            ibm_db.execute(prep_stmt)
            msg = "You have successfully registered."
        return render_template('login.html', msg=msg, ip=ip)

    elif request.method == 'POST':
        msg = "Please fill out the form."
        return render_template('login.html', msg=msg, ip=ip)


@ app.route('/search')
def search():
    msg = " "
    username = session['id']

    sql = "SELECT COUNT(USERNAME) AS COUNT FROM USERS WHERE BLOODGROUP=?;"
    stmt = ibm_db.prepare(conn, sql)

    ibm_db.bind_param(stmt, 1, 'A+')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    ap = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'A-')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    an = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'B+')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    bp = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'B-')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    bn = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'AB+')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    abp = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'AB-')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    abn = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'O+')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    op = account['COUNT']

    ibm_db.bind_param(stmt, 1, 'O-')
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    on = account['COUNT']

    return render_template('search.html', ap=ap, an=an, bp=bp, bn=bn, abp=abp, abn=abn, op=op, on=on, ip=ip)


@ app.route('/requestmail', methods=["GET", "POST"])
def requestmail():

    if request.method == "POST":
        blood = request.form['blood']
        sql = "SELECT USERNAME, CITY, EMAIL FROM USERS WHERE BLOODGROUP=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, blood)
        ibm_db.execute(stmt)
        account = []
        while ibm_db.fetch_row(stmt) != False:
            tmp = []
            for i in range(3):
                tmp.append(ibm_db.result(stmt, i))
            account.append(tuple(tmp))

        headings = ['Username', 'City', 'Mail']
        msg = ""
        if (len(account) > 0):
            msg = blood + " Donors found"
        else:
            msg = blood + " Donors not found"

        return render_template('request.html', headings=headings, msg=msg, account=account, ip=ip)
    else:
        return render_template('request.html', ip=ip)


@ app.route('/donation', methods=["GET", "POST"])
def donation():

    msg = " "
    if request.method == "POST":
        blood = request.form['blood']
        city = request.form['city']
        username = session['id']
        update_sql = "UPDATE USERS SET CITY=?, BLOODGROUP=? WHERE USERNAME=?;"
        stmt = ibm_db.prepare(conn, update_sql)
        ibm_db.bind_param(stmt, 1, city)
        ibm_db.bind_param(stmt, 2, blood)
        ibm_db.bind_param(stmt, 3, username)
        ibm_db.execute(stmt)
        msg = "You have successfully registered"
        return render_template('donation.html', msg=msg, ip=ip)

    else:
        msg = "Please fill out the form."
        return render_template('donation.html', msg=msg, ip=ip)


def sendgridmail(to_mail_id):
    try:
        sg = sendgrid.SendGridAPIClient(
            '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')
    # Change to your verified sender
        from_email = Email("kencydanielfdo@gmail.com")
        to_email = To(to_mail_id)  # Change to your recipient
        subject = "Plasma Donation request "
        htmlcontent = "Hi, A user has sent you a request for plasma donation. If you are willing to donate kindly contact them with this email id. Email: " + \
            session['email']
        content = Content("text/plain", htmlcontent)
        mail = Mail(from_email, to_email, subject, content)
    # Get a JSON-ready representation of the Mail object
        mail_json = mail.get()
    # Send an HTTP POST request to /mail/send
        response = sg.client.mail.send.post(request_body=mail_json)
        print(response.status_code)
    except Exception as e:
        print(e.message)


@ app.route('/sendmail', methods=["GET", "POST"])
def sendmail():

    if request.method == "POST":
        receivermail = request.form['mailbtn']
        sendgridmail(receivermail)
        return redirect(url_for('search'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return render_template('login.html', ip=ip)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
