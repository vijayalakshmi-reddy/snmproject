from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
import mysql.connector 
from mysql.connector import(connection)
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session
from io import BytesIO
import flask_excel as excel
import re
app=Flask(__name__)
app.secret_key='codegnan@2018'
app.config['SESSION_TYPE']='filesystem'
Session(app)
#mydb=mysql.connector.connect(host='localhost',user='root',password='admin',db='snmproject')
mydb=connection.MySQLConnection(user='root',password='admin',host='localhost',database='snmproject')
@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        username=request.form['user_name']
        uemail=request.form['email']
        password=request.form['password']
        conformpassword=request.form['confirm_password']
        cursor=mydb.cursor()
        cursor.execute("select count(user_email) from users where user_email=%s",[uemail])
        result=cursor.fetchone() 
        print(result)
        if result[0]==0:
            gotp=genotp()
            print(gotp)
            udata={'username':username,'uemail':uemail,'password':password,'otp':gotp}
            subject="OTP for Simple Notes Manager"
            body=f"otp for registration of Simple notes manger {gotp}"
            sendmail(to=uemail,subject=subject,body=body)
            flash('OTP has send to your mail')
            return redirect(url_for('otp',enudata=encode(data=udata)))  
        elif result[0]>0:
            flash('Email already existed')
            return redirect(url_for('login')) 
        else:
            return 'something is wrong'
    return render_template('create.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        uemail=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(user_email) from users where user_email=%s',[uemail])
        c=cursor.fetchone()
        if c[0]==0:
            flash("Your details not Exist please register first")
            return redirect(url_for('create'))
        else:
            cursor.execute('select password from users where user_email=%s',[uemail])
            bpassword=cursor.fetchone() 
            # print("password:",password)
            # print("result password:",bpassword[0].decode('utf-8'))
            # print(type(password),type(bpassword[0].decode('utf-8')))
            if bpassword[0].decode('utf-8') == password:
                print(session)
                session['user']=uemail
                print("After:",session)
                return redirect(url_for("dashboard"))
            else:
                return "Incorrect Credientails"
    return render_template('login.html')

@app.route('/otp/<enudata>',methods=['POST','GET'])
def otp(enudata):
    if request.method=='POST':
        otpr=request.form.get("otp")
        try:
            dudata=decode(data=enudata)   #{'userid':userid,'username':username,'uemail':uemail,'password':password,'otp':gotp}
        except Exception as e:
            print(e)
            return "Something is wrong"
        else:
            if otpr==dudata['otp']:
                cursor=mydb.cursor()
                cursor.execute("insert into users(user_name,user_email,password) values(%s,%s,%s)",[dudata['username'],dudata['uemail'],dudata['password']])
                mydb.commit()
                cursor.close()
                return redirect(url_for('login'))
            else:
                return "Invalid OTP"   
    return render_template('otp.html')

@app.route("/dashboard",methods=['POST','GET'])
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route("/addnotes",methods=['POST','GET'])
def addnotes():
    if session.get('user'):
        if request.method=="POST":
            title=request.form["title"]
            desc=request.form["desc"]
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users where user_email=%s",[session.get('user')])
            id=cursor.fetchone()
            if id:
                try:
                    cursor.execute('insert into notes(title,ndescription,user_id) values(%s,%s,%s)',[title,desc,id[0]])
                    mydb.commit()
                    cursor.close()
                except mysql.connector.errors.IntegrityError:
                    flash("Duplicate Title Entry")
                    return redirect(url_for('dashboard'))
                else:
                    flash("Notes add successfully")
                    return redirect(url_for('dashboard'))
            else:
                return "Something went wrong"
        return render_template("addnotes.html")
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route('/viewallnotes',methods=['POST',"GET"])
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users where user_email=%s",[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select nid,title,create_at from notes where user_id=%s',[uid[0]])
            result=cursor.fetchall()
            print(result)
        except Exception as e:
            print(e)
            return redirect(url_for("dashboard"))
        else:
            return render_template("viewallnotes.html",result=result)
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route('/viewnotes/<uid>')
def viewnotes(uid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select * from notes where nid=%s",[uid])
            notes=cursor.fetchone()
        except Exception as e:
            print(e)
            return redirect(url_for("viewallnotes"))
        else:
            return render_template("viewnotes.html",notes=notes)
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route("/updatenotes/<uid>",methods=["POST","GET"])
def updatenotes(uid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from notes where nid=%s",[uid])
        notes=cursor.fetchone()
        if request.method=="POST":
            try:
                title=request.form["title"]
                desc=request.form["desc"]
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update notes set title=%s,ndescription=%s where nid=%s',[title,desc,uid])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
            else:
                flash("Notes updates successfully")
                return redirect(url_for('dashboard'))
        return render_template("updatenotes.html",notes=notes)
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route("/deletenotes/<uid>",methods=["POST","GET"])
def deletenotes(uid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("delete from notes where nid=%s",[uid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not delete notes')
            return redirect(url_for('viewallnotes'))
        else:
            flash("Deleted successfully")
            return redirect(url_for("viewallnotes"))
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route('/uploadfile', methods=['GET','POST'])
def upload_file():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            fdata=filedata.read()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select user_id from users where user_email=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
                mydb.commit()
            except Exception as e:
                print(e)
                flash("couldn't upload file")
                return redirect(url_for('dashboard'))
            else:
                flash('file uploaded successfully')
                return redirect(url_for('dashboard'))
        return render_template('uploadfile.html')
    else:
        flash("Please login first")
        return redirect(url_for("login"))
@app.route('/allfiles',methods=['POST','GET'])
def all_files():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users where user_email=%s",[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select fid,filename,create_at from filedata where added_by=%s',[uid[0]])
            filesdata=cursor.fetchall()
        except Exception as e:
            print(e)
            return redirect(url_for('dashboard'))
        else:
            return render_template("allfiles.html",filesdata=filesdata)
    

@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
        except Exception as e:
            print(e)
            flash("couldn't not open file")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for('login'))
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash("couldn't not open file")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for('login'))
@app.route("/deletefile/<fid>",methods=["POST","GET"])
def deletefile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("delete from filedata where fid=%s",[fid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash("Can't delete the file")
            return redirect(url_for("dashboard"))
        else:
            flash("Deleted successfully")
            return redirect(url_for("all_files"))
    else:
        flash("please login first")
        return redirect(url_for("login"))
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users_info where user_email=%s",[session.get('user')])
            uid=cursor.fetchone()#(1,)
            cursor.execute('select nid,title,ndescription,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall() #[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 |       2 ),(inko data ela tuple lo vastundi)]
            print(ndata)
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for("dashboard"))
        else:
            array_data=[list(i) for i in ndata]
            columns=['Notes_id','title','content','created_time']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')#[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 |       2 ),(inko data ela tuple lo vastundi)]

        # return render_template("viewallnotes.html",ndata=ndata) 
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE)
                if(pattern.match(sdata)):
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select * from notes where nid like %s or title like %s or ndescription like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('No Data Found')
                    return render_template('dashboard.html')
            else:
                return render_template('dashboard.html')
        except Exception as e:
            print(e)
            flash("Can't find anything")
            return render_template('dashboard.html')
    else:
        return render_template('login')


app.run(use_reloader=True,debug=True)
