from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
import json
from sqlalchemy import text

# MY db connection
local_server= True
app = Flask(__name__)
app.secret_key='kusumachandashwini'


# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI']='mysql://root:@localhost/studentdbms'
db=SQLAlchemy(app)

# here we will create db models that is tables
class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100))

class Department(db.Model):
    cid=db.Column(db.Integer,primary_key=True)
    branch=db.Column(db.String(100))

class Attendence(db.Model):
    aid=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(100))
    attendance=db.Column(db.Integer())

class Trig(db.Model):
    tid=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(100))
    action=db.Column(db.String(100))
    timestamp=db.Column(db.String(100))


class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))





class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(50))
    sname=db.Column(db.String(50))
    sem=db.Column(db.Integer)
    gender=db.Column(db.String(50))
    branch=db.Column(db.String(50))
    email=db.Column(db.String(50))
    number=db.Column(db.String(12))
    address=db.Column(db.String(100))

class Marks(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(50))
    mid_1=db.Column(db.String(50))
    mid_2=db.Column(db.String(50))
    final=db.Column(db.String(50))
    
    

@app.route('/')
def index(): 
    return render_template('index.html')


@app.route('/triggers')
def triggers():
    # Используем функцию text для создания текстового SQL-выражения
    result = db.session.execute(text("SELECT * FROM `trig`"))
    triggers = result.fetchall()
    return render_template('triggers.html', triggers=triggers)

@app.route('/department',methods=['POST','GET'])
def department():
    if request.method=="POST":
        dept=request.form.get('dept')
        query=Department.query.filter_by(branch=dept).first()
        if query:
            flash("Department Already Exist","warning")
            return redirect('/department')
        dep=Department(branch=dept)
        db.session.add(dep)
        db.session.commit()
        flash("Department Addes","success")
    return render_template('department.html')

@app.route('/addattendance', methods=['POST', 'GET'])
def addattendance():
    if request.method == "POST":
        rollno = request.form.get('rollno')
        attend = request.form.get('attend')
        print(attend, rollno)
        atte = Attendence(rollno=rollno, attendance=attend)
        db.session.add(atte)
        db.session.commit()
        flash("Attendance added", "warning")
        # После добавления лучше сделать редирект, чтобы избежать повторной отправки формы при обновлении страницы
        return redirect(url_for('addattendance'))

    # Если метод не POST, то предполагаем GET и получаем всех студентов для отображения
    students = Student.query.all()
    return render_template('attendance.html', students=students)


        
    return render_template('attendance.html',query=query)

@app.route('/search',methods=['POST','GET'])
def search():
    if request.method=="POST":
        rollno=request.form.get('roll')
        bio=Student.query.filter_by(rollno=rollno).first()
        attend=Attendence.query.filter_by(rollno=rollno).first()
        exam=Marks.query.filter_by(rollno=rollno).first()
        return render_template('search.html',bio=bio,attend=attend,exam=exam)
        
    return render_template('search.html')

@app.route("/delete/<string:id>",methods=['POST','GET'])
@login_required
def delete(id):
    db.Session.execute(f"DELETE FROM `student` WHERE `student`.`id`={id}")
    db.Session.execute(f"DELETE FROM `marks` WHERE `marks`.`id`={id}")
    flash("Slot Deleted Successful","danger")
    return redirect('/studentdetails')


@app.route("/edit/<string:id>",methods=['POST','GET'])
@login_required
def edit(id):
    dept=db.Session.execute("SELECT * FROM `department`")
    posts=Student.query.filter_by(id=id).first()
    if request.method=="POST":
        rollno=request.form.get('rollno')
        sname=request.form.get('sname')
        sem=request.form.get('sem')
        gender=request.form.get('gender')
        branch=request.form.get('branch')
        email=request.form.get('email')
        num=request.form.get('num')
        address=request.form.get('address')
        query=db.Session.execute(f"UPDATE `student` SET `rollno`='{rollno}',`sname`='{sname}',`sem`='{sem}',`gender`='{gender}',`branch`='{branch}',`email`='{email}',`number`='{num}',`address`='{address}'")
        flash("Slot is Updates","success")
        return redirect('/studentdetails')
    
    return render_template('edit.html',posts=posts,dept=dept)


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Проверяем, существует ли уже пользователь с таким email
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email уже существует", "warning")
            return redirect(url_for('signup'))

        # Генерируем хеш пароля
        encpassword = generate_password_hash(password)

        # Создаем нового пользователя
        new_user = User(username=username, email=email, password=encpassword)
        db.session.add(new_user)
        db.session.commit()
        flash("Регистрация прошла успешно. Пожалуйста, войдите", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password,password):
            login_user(user)
            flash("Login Success","primary")
            return redirect(url_for('index'))
        else:
            flash("invalid credentials","danger")
            return render_template('login.html')    

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))



@app.route('/addstudent', methods=['POST', 'GET'])
@login_required
def addstudent():
    if request.method == "POST":
        rollno = request.form.get('rollno')
        sname = request.form.get('sname')
        sem = request.form.get('sem')
        gender = request.form.get('gender')
        branch = request.form.get('branch')
        email = request.form.get('email')
        num = request.form.get('num')
        address = request.form.get('address')

        # Подготовка SQL-запроса с использованием безопасной параметризации
        stmt = text("""
            INSERT INTO student (rollno, sname, sem, gender, branch, email, number, address)
            VALUES (:rollno, :sname, :sem, :gender, :branch, :email, :num, :address)
        """)

        # Выполнение запроса с безопасной передачей параметров
        db.session.execute(stmt, {
            'rollno': rollno, 'sname': sname, 'sem': sem, 'gender': gender,
            'branch': branch, 'email': email, 'num': num, 'address': address
        })
        db.session.commit()

        flash("Student added successfully", "info")
        return redirect(url_for('addstudent'))  # Редирект, чтобы избежать повторного добавления при обновлении страницы

    # Получение всех отделений для отображения в форме
    departments = Department.query.all()
    return render_template('student.html', departments=departments)

@app.route('/marks', methods=['POST', 'GET'])
def marks():
    query = db.session.execute(text("SELECT * FROM student")).fetchall()
    return render_template('marks.html', query=query)


from sqlalchemy import text

@app.route('/addmark/<string:rollno>', methods=['POST','GET'])
@login_required
def addmarks(rollno):
    post = Student.query.filter_by(rollno=rollno).first()
    if request.method == "POST":
        roll = request.form.get('rollno')
        mid1 = request.form.get('mid1')
        mid2 = request.form.get('mid2')
        final = request.form.get('final')
        sql = text("INSERT INTO `marks` (`rollno`, `mid_1`, `mid_2`, `final`) VALUES (:roll, :mid1, :mid2, :final)")
        db.session.execute(sql, {'roll': roll, 'mid1': mid1, 'mid2': mid2, 'final': final})
        db.session.commit()
        flash("Marks added successfully", "info")
        # Здесь изменено на корректное имя функции
        return redirect(url_for('student_details'))
    return render_template('addmark.html', post=post)


@app.route('/studentdetails')
def student_details():
    students = Student.query.all()  # Здесь предполагается, что у вас есть модель Student
    return render_template('studentdetails.html', query=students)

@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'


app.run(debug=True)    