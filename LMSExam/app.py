# pip install flask
# 플라스크란?
# 파이썬으로 만든 db연동 콘솔 프로그램을 웹으로 연결하는 프레임워크
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 것
# app.py 는 플라스크로 서버를 동작하기 위한 파일명 (기본파일)
# static, templates 폴더 필수 (프론트용 파일 모이는 곳)
# static : 정적 파일을 모아놓는 곳 (html, css, js)
# templates : 동적 파일을 모아놓는 곳 (crud 화면, 레이아웃, index 등..)
import os

from flask import Flask, render_template, request, redirect, url_for, session
from LMS.common.session import Session
from LMS.domain import Board, Score
from LMS.service import PostService

#                플라스크    프론트 연결      요청,응답  주소전달   주소생성  상태저장

app = Flask(__name__)
app.secret_key = '2142315'
# 세션을 사용하기 위해 보안킨 설정 (아무 문자열이나 입력)

@app.route('/login', methods=['GET', 'POST']) # http://localhost:5000/login
    # methods는 웹의 동작에 관여한다
    # GET : URL 주소로 데이터를 처리 (보안상 좋지 않음, 대신 빠름)
    # POST : BODY 영역의 데이터를 처리 (보안상 좋음, 대용량일 때 많이 사용됨)
    # 대부분 처음에 화면(HTML 랜더)을 요청할 때는 GET 방식 처리 ----- 로그인 화면 출력 할 때
    # 화면에 있는 내용을 백앤드로 전달할 때는 POST 방식 처리 ----- 로그인 정보를 데이터베이스에 확인할 때
def login():
    if request.method == 'GET':
        return render_template('login.html')
        # GET 방식으로 요청하면 login.html 화면이 나옴
    # login.html에서 action="/login" method="POST" 처리용코드
    # login.html에서 넘어온 폼 데이터는 uid / upw
    uid = request.form['uid'] # 요청한 폼 내용을 가져옴
    upw = request.form['upw'] # request form get
    # print("/login에서 넘어온 폼 데이터 출력 테스트")
    # print(uid, upw)
    # print("==================================")

    conn = Session.get_connection()
    try :
        with conn.cursor() as cur:
            # 1. 회원 정보 조회
            sql = 'SELECT id,name,uid,role FROM members WHERE uid = %s and password = %s'
            #                                                 uid와 password가 동일한지
            #             id,name,uid,role을 가져옴
            cur.execute(sql, (uid, upw))  # 쿼리문 실행
            user = cur.fetchone()  # 쿼리 결과 1개를 가져와 user 변수에 넣음
            if user:
                # 찾은 계정이 있으면 브라우저 세션영역에 보관한다.
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_uid'] = user['uid']
                session['user_role'] = user['role']
                # 세션에 저장 완료
                # 브라우저에서 f12번을 누르고 애플리케이션 탭에서 쿠키 항목에 가면 session객체가 보인다
                # 이것을 삭제하면 로그아웃 처리 됨
                return redirect(url_for('index'))
            # 처리 후 이동하는 경로 http://localhost:/index로 감 (GET 메서드 방식)
            else:
                return "<script>alert('아이디나 비밀번호가 틀렸습니다.);history.back()</script>"
                #               경고창 실행                           뒤로가기
    finally:
        conn.close() # db 연결 종료

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')

    # POST 메서드인 경우(폼으로 데이터가 넘어올때 처리)

    uid = request.form['uid']
    password = request.form['password']
    name = request.form['name']

    conn = Session.get_connection()
    try :
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM members uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.');history.back()</script>"

            # 회원 정보 저장(role, active는 기본값이 들어감)
            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!'); location.href = '/login';</script>"
    except Exception as e:  # 예외발생시 실행문
        print(f"회원가입 에러: {e}")
        return "가입 중 오류가 발생했습니다. /n join 메서드를 확인하세요!!"

    finally:  # 항상 실행문
        conn.close()

@app.route('/members/edit', methods=['GET', 'POST'])
def members_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = Session.get_connection()
    #  있으면 db에 연결

    try :
        with conn.cursor() as cursor:
            if request.method == 'GET':
                cursor.execute("SELECT * FROM members WHERE uid = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('members_edit.html', user_info=user_info)

            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw : # 비밀번호 입력 시에만 변경
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (new_name, new_pw, session['user_id']))
            else :
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name
            return "<script>alert('정보가 수정되었습니다'); location.href='/mypage';</script>"


    except Exception as e:  # 예외발생시 실행문
        print(f"회원수정 에러:{e}")
        return "가입 중 오류가 발생했습니다. /n member_edit() 메서드를 확인하세요!!"

    finally:  # 항상 실행문
        conn.close()

@app.rote('/mypage') # http"//localhost:5000/mypage get 요청시 처리됨
def mypage():
    if 'user_id' not in session: # 로그인상태인지 확인
        return redirect(url_for('login')) # 로그인아니면  http"//localhost:5000/login으로 보냄

    conn = Session.get_connection() # db연결
    try :
        with conn.cursor() as cursor:
            # 1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            # 로그인한 정보를 가지고 db에서 찾아옴
            user_info = cursor.fetchone() # 찾아온 값 1개를 user_info에 담음(dict)

            # 2. 내가 쓴 게시글 개수 조회(작성하신 boards 테이블 활용)
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (session['user_id'],))
            #                                                   boards 테이블에 조건 member_id 값을 가지고 찾아옴.
            #                      개수를 세어 fetchone()에 넣음 -> board_count 이름으로 개수를 가지고 있음.
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html', user=user_info, board_count=board_count)
            # 결과를 리턴한다.                         mypage.html 에게 user 객체와 board_count 객체를 담아 보냄.
            # 프론트에서 사용하려면 {{user.????}} {{board_count}}
    finally: conn.close()

###################################### 멤버 CRUD END ###################################################

######################################## 게시판 CRUD #####################################################

@app.route('/board/write', methods=['GET', 'POST'])
def board_write():
    if request.method == 'GET':
        if 'user_id' not in session:
            return "<script> alert('로그인 후 이용가능합니다.'); location.href='/login';</script>"
        return render_template('board_write.html')
    elif request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        member_id = request.form['member_id']

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO boards (title, content, member_id) VALUES (%s, %s, %s)"
                cursor.execute(sql, (title, content, member_id))
                conn.commit()
            return redirect(url_for('board_read'))
        except Exception as e:
            print(f"글쓰기 에러 : {e}")
            return "저장중 에러 발생"
        finally:
            conn.close()

@app.route('/board')
def board_read():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql="""
                SELECT b.* m.name as writer_name
                FROM boards b
                JOIN members m ON b.member_id = m.id
                ORDER BY b.id DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows]
            return render_template('board_read.html', boards=boards)
    finally:
        conn.close()

# 게시글 자세히 보기
@app.route('/board/view/<int:board_id>')
def board_view(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """SELECT b.*, m.name as writer_name, m.uid as writer_uid
            FROM boards b
            JOIN members m ON b.member_id = m.id
            WHERE b.id = %s
            """
            cursor.execute(sql, (board_id,))
            row = cursor.fetchall()

            if not row:
                return "<script>alert('존재하지 않는 게시글 입니다.');history.back();</script>"

            board = Board.from_db(row)

            return render_template('board_view.html', board=board)
    finally:
        conn.close()

@app.route('/board/edit/<int:board_id>', methods=['GET', 'POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql, (board_id,))
                row = cursor.fetchone()

                if not row:
                    return "<script>alert('존재하지 않는 게시글 입니다.');history.back();</script>"

                # 본인 확인 로직
                if row['member_id'] != session('user_id'):
                    return "<script>alert('수정 권한이 없습니다.');history.back();</script>"
                board = Board.from_db(row)
                return render_template('board_edit.html', board=board)

            elif request.method == 'POST':
                title = request.form['title']
                content = request.form['content']

                sql = "UPDATE boards SET title = %s, content = %s WHERE id = %s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()

                return redirect(url_for('board_read'))
    finally:
        conn.close()

@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    conn = Session.get_connection()

    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM boards WHERE id = %s"
            cursor.execute(sql, (board_id,))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"게시글 {board_id}번 삭제 성공")
            else :
                return "<script>alert('삭제할 게시글이 없거나 권한이 없습니다.');history.back();</script>"

        return redirect(url_for('board_read'))
    except Exception as e:
        print(f"삭제 에러: {e}")
        return "삭제 중 오류 발생"
    finally:
        conn.close()

####################################### Board CRUD END ##################################################

######################################### 성적 CRUD ######################################################

# 주의사항 : role에 admin과 manager만 CUD를 제공한다.
# 일반 사용자는 role이 user이고 자신의 성적만 볼 수 있다.

####################################### 성적 CRUD END ####################################################


@app.route('/score/add')
def score_add():
    if session.get('user_role') not in ('admin','manager'):
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    target_uid = request.args.get('uid')
    target_name = request.args.get('name')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()


            existing_score = None
            if student:
                cursor.execute("SELECT * FROM scores WHERE member_id = %s", (student.id,))
                row = cursor.fetchone()
                print(row)
                if row:
                    existing_score = Score.from_db(row)

                return render_template('score_from.html',
                                       target_uid = target_uid,
                                       target_name = target_name,
                                       scor = existing_score)
    finally:
        conn.close()


@app.route('/scor/save', methods=['POST'])
def save_score():
    if session.get('user_role') not in ('admin','manager'):
        return "권한 오류", 403

    target_uid = request.form.get('uid')
    kor = int(request.form.get('korean', 0))
    eng = int(request.form.get('english', 0))
    math = int(request.form.get('math', 0))

    conn = Session.get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()
            print(student)
            if not student:
                return "<script>alert('존재하지 않는 학생입니다.');history.back();</script>"

            temp_score = Score(member_id = student.get('id'), kor=kor, eng=eng, math=math)

            cursor.execute("SELECT id FROM scores WHERE member_id = %s", (student['id'],))
            is_exist = cursor.fetchone()

            if is_exist:
                sql = """
                UPDATE scores SET korean=%s, english=%s, math=%s,
                        total=%s, average=%s, grade=%s WHERE member_id = %s                
                """
                cursor.execute(sql, (temp_score.kor, temp_score.eng,temp_score.math,
                                     temp_score.total,temp_score.avg, target_uid.grade,
                                     student['id']))
            else:
                sql = """
                    INSERT INTO scores(member_id, korean, english, math, total, average, grade)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)
                """
            cursor.execute(sql, (student['id'], temp_score.kor, temp_score.eng, temp_score.math,
                                 temp_score.total, temp_score.avg, temp_score.grade))
            conn.commit()
            return f"<script>alert('{target_uid} 학생 성적 저장 완료!'); location.href='/score/list';</script>"
    finally:
        conn.close()


@app.route('/score/list')
def score_list():
    if session.get('user_role') not in ('admin','manager'):
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT m.name, m.uid, s.* FROM scores s
                JOIN members m ON s.member_id = m.id
                ORDER BY m.id DESC
            """
            cursor.execute(sql)
            datas = cursor.fetchall()

            score_objects = []
            for data in datas:
                s = Score.from_db(data)
                s.name = data['name']
                s.uid = data['uid']
                score_objects.append(s)

            return render_template('score_list.html', score_objects=score_objects)
    finally:
        conn.close()


@app.route('/score/my')
def score_my():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM scores WHERE member_id = %s"
            cursor.execute(sql, (session['user_id'],))
            row = cursor.fetchone()
            print(row)

            return render_template('score_my.html', row=row)
    finally:
        conn.close()

####################################### 성적 CRUD END ####################################################

####################################### 파일게시판 CRUD ###################################################

UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/filesboard/write', methods=['get','POST'])
def file_write():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        files = request.files.getlist('files')

        if PostService.save_post(session['user_id'], title, content, files):
            return "<script>alert('게시글이 등록되었습니다.'); location.href='/filesboard';</script>"
        else:
            return "<script>alert('등록 실패'); history.back();</script>"
    return render_template('filesboard_write.html')


@app.route('/filesboard')
def filesboard_list():
    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)

@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id):
    post, files = PostService.get_post_detail(post_id)
    if not post:
        return "<script>alert('해당 게시글이 없습니다.'); location.href='/filesboard';</script>"
    return render_template('filesboard_view.html', post=post, files=files)


@app.route('/download/<path:filename>')
def download_file(filename):
    origin_name = request.args.get('origin_name')
    return send_from_directory('uploads/', filename, as_attachment=True, download_name=origin_name)


@app.route('/filesboard/delete/<int:post_id>')
def filesboard_delete(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    post, _ = PostService.get_post_detail(post_id)

    if not post:
        return "<script>alert('이미 삭제된 게시글입니다.'); location.href='/filesboard';</script>"
    if post['member_id'] != session['user_id'] and session.get('user_role') != 'admin':
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"

    if PostService.delete_post(post_id):
        return "<script>alert('성공적으로 삭제되었습니다.'); location.href='/filesboard';</script>"
    else:
        return "<script>alert('삭제 중 오류가 발생했습니다.'); history.back();</script>"


@app.route('/filesboard/edit/<int:post_id>', methods=['GET', 'POST'])
def filesboard_edit(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')

        if PostService.save_post(session['user_id'], title, content, files):
            return f"<script>alert('수정되었습니다.'); location.href='/filesboard/view/{post_id}';</script>"
        return "<script>alert('수정 실패'); history.back();</script>"

    post, files = PostService.get_post_detail(post_id)
    if post['member_id'] != session['user_id']:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"
    return render_template('filesboard_edit.html', post=post, files=files)

####################################### 파일게시판 CRUD END ################################################

@app.route("/") # url 생성용 코드 http://localhost:5000/ or http://내ip:5000
def index():
    return render_template('main1.html')
    # render_template : 웹브라우저로 보낼 파일명
    # templates 라는 폴더에서 main.html을 찾아보냄

if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000, debug=True)
    # host='0.0.0.0' : 누가 요청하던 응답해라
    # port=5000 : 플라스크에서 사용하는 포트번호
    # debug=True : 콘솔에서 디버그를 보겠다