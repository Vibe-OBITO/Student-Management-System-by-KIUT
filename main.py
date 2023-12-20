from io import BytesIO
from os import abort
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.platypus import SimpleDocTemplate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from flask import send_file


# MY db connection
local_server = True
app = Flask(__name__)
app.secret_key = 'kusumachandashwini'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/studentdbms'
app.config['UPLOAD_FOLDER'] = 'static/photos'

pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSansCondensed.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSansCondensed', 'DejaVuSansCondensed.ttf'))






# this is for getting unique user access
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/studentdbms'
db = SQLAlchemy(app)

def create_superuser():
    superuser = User(username='admin', email='admin@example.com', password='your_password', is_superuser=True)
    db.session.add(superuser)
    db.session.commit()

# here we will create db models that is tables
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))


class Department(db.Model):
    cid = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(100))


class Attendence(db.Model):
    aid = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(100))
    attendance = db.Column(db.Integer())


class Trig(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(100))
    action = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))
    is_superuser = db.Column(db.Boolean, default=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(50))
    sname = db.Column(db.String(50))
    sem = db.Column(db.Integer)
    gender = db.Column(db.String(50))
    branch = db.Column(db.String(50))
    email = db.Column(db.String(50))
    number = db.Column(db.String(12))
    address = db.Column(db.String(100))
    photo = db.Column(db.String(255))

class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rollno = db.Column(db.String(50))
    mid_1 = db.Column(db.String(50))
    mid_2 = db.Column(db.String(50))
    final = db.Column(db.String(50))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/triggers')
def triggers():
    # Используем функцию text для создания текстового SQL-выражения
    result = db.session.execute(text("SELECT * FROM `trig`"))
    triggers = result.fetchall()
    return render_template('triggers.html', triggers=triggers)


@app.route('/department', methods=['POST', 'GET'])
def department():
    if request.method == "POST":
        dept = request.form.get('dept')
        query = Department.query.filter_by(branch=dept).first()
        if query:
            flash("Department Already Exist", "warning")
            return redirect('/department')
        dep = Department(branch=dept)
        db.session.add(dep)
        db.session.commit()
        flash("Department Addes", "success")
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

    return render_template('attendance.html', query=query)


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == "POST":
        search_query = request.form.get('search_query')
        results = Student.query.filter(or_(Student.rollno.ilike(f'%{search_query}%'), Student.sname.ilike(f'%{search_query}%'))).all()

        # Также можно добавить логику для обработки результатов поиска

        return render_template('search.html', results=results, search_query=search_query)

    return render_template('search.html')

@app.route('/view_student/<string:rollno>')
def view_student(rollno):
    # Ваш код для получения данных студента по rollno
    student = Student.query.filter_by(rollno=rollno).first()

    # Проверяем, существует ли студент с указанным rollno
    if not student:
        abort(404)  # Если нет, возвращаем ошибку 404

    return render_template('view_student.html', student=student)


@app.route("/delete/<string:id>", methods=['POST', 'GET'])
@login_required
def delete(id):
    if not current_user.is_superuser:
        flash("You don't have permission to delete students.", "danger")
        return redirect('/studentdetails')

    student = db.session.query(Student).get(int(id))
    if student:
        db.session.delete(student)
        try:
            db.session.commit()
            flash("Student Deleted Successfully", "danger")
        except IntegrityError:
            db.session.rollback()
            flash("Error: Student has related marks records", "warning")
    else:
        flash("Student not found", "warning")

    return redirect('/studentdetails')


@app.route('/studentdetails')
def student_details():
    # Ваш запрос к базе данных, чтобы получить студентов
    students = Student.query.all()

    # Получение переменной is_super_user для проверки прав доступа
    is_super_user = current_user.is_superuser

    # Передача данных в шаблон, включая is_super_user
    return render_template('studentdetails.html', query=students, is_super_user=is_super_user)



@app.route("/edit/<string:id>", methods=['POST', 'GET'])
@login_required
def edit(id):
    if not current_user.is_superuser:
        flash("You don't have permission to edit student information.", "danger")
        return redirect('/studentdetails')

    departments = Department.query.all()
    student = Student.query.get(id)

    if student:
        if request.method == "POST":
            rollno = request.form.get('rollno')
            sname = request.form.get('sname')
            sem = request.form.get('sem')
            gender = request.form.get('gender')
            branch = request.form.get('branch')
            email = request.form.get('email')
            num = request.form.get('num')
            address = request.form.get('address')

            student.rollno = rollno
            student.sname = sname
            student.sem = sem
            student.gender = gender
            student.branch = branch
            student.email = email
            student.number = num
            student.address = address

            try:
                db.session.commit()
                flash("Information updated", "success")
                return redirect('/studentdetails')
            except IntegrityError:
                db.session.rollback()
                flash("Error: Duplicate roll number or invalid data", "danger")

    return render_template('edit.html', student=student, departments=departments)


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


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Success", "primary")
            return redirect(url_for('index'))
        else:
            flash("invalid credentials", "danger")
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul", "warning")
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


@app.route('/marks')
def marks():
    sql = text("""
        SELECT
            s.rollno AS StudentRollNo,
            s.sname AS StudentName,
            s.sem AS Semester,
            sm.mark AS Mark,
            sub.name AS SubjectName
        FROM
            student s
        JOIN
            student_marks sm ON s.id = sm.student_id
        JOIN
            subjects sub ON sm.subject_id = sub.subject_id;
    """)
    result = db.session.execute(sql).fetchall()
    students_marks = {}
    for row in result:
        student_rollno = row[0]  # Индекс 0 соответствует StudentRollNo
        if student_rollno not in students_marks:
            students_marks[student_rollno] = {
                'rollno': row[0],          # Индекс 0 соответствует StudentRollNo
                'sname': row[1],          # Индекс 1 соответствует StudentName
                'sem': row[2],            # Индекс 2 соответствует Semester
                'marks': []
            }
        students_marks[student_rollno]['marks'].append({
            'subject_name': row[4],  # Индекс 4 соответствует SubjectName
            'mark': row[3]   # Индекс 3 соответствует Mark
        })

    return render_template('marks.html', students_marks=students_marks.values())





@app.route('/addmark/<string:rollno>', methods=['POST', 'GET'])
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



@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    group = request.args.get('group', 'Группа1')  # По умолчанию открываем Группу1

    # Вам нужно определить путь к изображениям группы в зависимости от выбранной группы
    image_path = f'images/{group}.jpg'

    return render_template('schedule.html', group_photo=image_path)


def create_student_profile_pdf(student_data):
    pass


@app.route('/download_profile_pdf/<string:rollno>')
def download_profile_pdf(rollno):
    # Получение информации о студенте и его оценках из базы данных
    student_data = get_student_info(rollno)

    if student_data:
        pdf_data = create_student_profile_pdf(student_data)
        return send_file(
            BytesIO(pdf_data),
            as_attachment=True,
            download_name=f"{student_data['sname']}_profile.pdf",
            mimetype='application/pdf'
        )
    else:
        # Обработка случая, если студент не найден
        return render_template('student_not_found.html', rollno=rollno)


def get_student_info(rollno):
    sql = text("""
        SELECT
            s.rollno AS StudentRollNo,
            s.sname AS StudentName,
            s.sem AS Semester,
            s.gender AS Gender,
            s.branch AS Branch,
            s.email AS Email,
            sm.mark AS Mark,
            sub.name AS SubjectName
        FROM
            student s
        LEFT JOIN
            student_marks sm ON s.id = sm.student_id
        LEFT JOIN
            subjects sub ON sm.subject_id = sub.subject_id
        WHERE
            s.rollno = :rollno
    """)

    result = db.session.execute(sql, {'rollno': rollno})

    if result.rowcount > 0:
        columns = list(result.keys())
        rows = result.fetchall()

        student_data = {
            'rollno': rows[0][columns.index('StudentRollNo')],
            'sname': rows[0][columns.index('StudentName')],
            'sem': rows[0][columns.index('Semester')],
            'gender': rows[0][columns.index('Gender')],
            'branch': rows[0][columns.index('Branch')],
            'email': rows[0][columns.index('Email')],
            'subjects': []
        }

        for row in rows:
            if row[columns.index('SubjectName')] is not None:
                subject_info = {
                    'name': row[columns.index('SubjectName')],
                    'marks': row[columns.index('Mark')]
                }
                student_data['subjects'].append(subject_info)

        return student_data
    else:
        return None


def create_student_profile_pdf(student_data):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()

    # Заголовок
    title = f"<u>Student Profile</u>"
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'])
    title_paragraph = Paragraph(title, title_style)

    # Информация о студенте
    student_info = f"ID Number: {student_data['rollno']}<br/>" \
                   f"Name: {student_data['sname']}<br/>" \
                   f"Semester: {student_data['sem']}<br/>" \
                   f"Gender: {student_data['gender']}<br/>" \
                   f"Branch: {student_data['branch']}<br/>" \
                   f"Email: {student_data['email']}"

    student_info_style = ParagraphStyle('StudentInfoStyle', parent=styles['BodyText'])
    student_info_paragraph = Paragraph(student_info, student_info_style)

    # Оценки по предметам
    subjects_title = "<b>Subjects and Marks</b>"
    subjects_title_style = ParagraphStyle('SubjectsTitleStyle', parent=styles['Heading2'])
    subjects_title_paragraph = Paragraph(subjects_title, subjects_title_style)

    subjects_info = "<br/>".join([f"{subject['name']}: {subject['marks']}" for subject in student_data['subjects']])
    subjects_info_style = ParagraphStyle('SubjectsInfoStyle', parent=styles['BodyText'])
    subjects_info_paragraph = Paragraph(subjects_info, subjects_info_style)

    # Футер
    footer_text = "<i>Tashkent City Higher Education Institution Привет как дела</i>"
    footer_style = ParagraphStyle('FooterStyle', parent=styles['BodyText'])
    footer_paragraph = Paragraph(footer_text, footer_style)

    # Строим документ
    pdf.build([
        title_paragraph,
        student_info_paragraph,
        subjects_title_paragraph,
        subjects_info_paragraph,
        footer_paragraph,
    ], onFirstPage=lambda canvas, doc: canvas.setFont("DejaVuSansCondensed", 12),
        onLaterPages=lambda canvas, doc: canvas.setFont("DejaVuSansCondensed", 12))


    return buffer.getvalue()

@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except Exception as e:
        return f'My db is not Connected. Error: {e}'


app.run(debug=True)


























