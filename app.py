from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'library-management-system-secret-key-2024'

# 数据库配置 - 支持 PostgreSQL (Neon/Railway) 和 SQLite (本地)
if os.environ.get('TESTING') == 'true':
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
elif os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')
    status = db.Column(db.String(20), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    category = db.Column(db.String(50), default='其他')
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    borrow_count = db.Column(db.Integer, default=0)

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='borrowed')

    book = db.relationship('Book')
    user = db.relationship('User')

# 密码加密函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

# 权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('需要管理员权限！', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录！', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 首页
@app.route('/')
def index():
    books = Book.query.all()
    categories = db.session.query(Book.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template('index.html', books=books, categories=categories)

# 搜索
@app.route('/search')
def search():
    keyword = request.args.get('keyword', '')
    category = request.args.get('category', '')

    query = Book.query
    if keyword:
        query = query.filter(
            (Book.title.contains(keyword)) |
            (Book.author.contains(keyword)) |
            (Book.isbn.contains(keyword))
        )
    if category and category != '全部':
        query = query.filter(Book.category == category)

    books = query.all()
    categories = db.session.query(Book.category).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('index.html', books=books, categories=categories,
                          keyword=keyword, selected_category=category)

# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password(password, user.password):
            if user.status == 'frozen':
                flash('账号已被冻结，请联系管理员！', 'error')
                return redirect(url_for('login'))

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        flash('用户名或密码错误！', 'error')
    return render_template('login.html')

# 用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('用户名已存在！', 'error')
            return redirect(url_for('register'))

        user = User(username=username, password=hash_password(password), role='user')
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# 退出登录
@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

# 借书
@app.route('/borrow/<int:book_id>')
@login_required
def borrow(book_id):
    user = User.query.get(session['user_id'])
    if user.status == 'frozen':
        flash('账号已被冻结，无法借书！', 'error')
        return redirect(url_for('index'))

    borrowed_count = BorrowRecord.query.filter_by(
        user_id=session['user_id'], status='borrowed'
    ).count()
    if borrowed_count >= 5:
        flash('您已达到借阅上限（5本），请先归还部分图书！', 'error')
        return redirect(url_for('index'))

    book = Book.query.get_or_404(book_id)
    if book.available_copies < 1:
        flash('这本书已被借完！', 'error')
        return redirect(url_for('index'))

    existing = BorrowRecord.query.filter_by(
        user_id=session['user_id'], book_id=book_id, status='borrowed'
    ).first()
    if existing:
        flash('您已经借阅了这本书，请先归还！', 'error')
        return redirect(url_for('index'))

    due_date = datetime.utcnow() + timedelta(days=30)
    borrow = BorrowRecord(user_id=session['user_id'], book_id=book_id, due_date=due_date)
    book.available_copies -= 1
    book.borrow_count += 1
    db.session.add(borrow)
    db.session.commit()

    flash(f'借书成功！请在 {due_date.strftime("%Y-%m-%d")} 前归还', 'success')
    return redirect(url_for('index'))

# 还书
@app.route('/return/<int:record_id>')
@login_required
def return_book(record_id):
    record = BorrowRecord.query.get_or_404(record_id)

    if record.user_id != session['user_id'] and session.get('role') != 'admin':
        flash('无权操作！', 'error')
        return redirect(url_for('index'))

    book = Book.query.get(record.book_id)
    book.available_copies += 1
    record.return_date = datetime.utcnow()
    record.status = 'returned'

    if record.due_date and datetime.utcnow() > record.due_date:
        days_overdue = (datetime.utcnow() - record.due_date).days
        fine = days_overdue * 1
        flash(f'还书成功！超期 {days_overdue} 天，罚款 {fine} 元', 'warning')
    else:
        flash('还书成功！', 'success')

    db.session.commit()
    return redirect(url_for('my_books'))

# 我的借阅
@app.route('/my-books')
@login_required
def my_books():
    records = BorrowRecord.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_books.html', records=records, timedelta=timedelta, datetime=datetime)

# 个人中心
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        user = User.query.get(session['user_id'])
        if check_password(old_password, user.password):
            user.password = hash_password(new_password)
            db.session.commit()
            flash('密码修改成功！', 'success')
        else:
            flash('原密码错误！', 'error')

    user = User.query.get(session['user_id'])
    borrowed_count = BorrowRecord.query.filter_by(
        user_id=session['user_id'], status='borrowed'
    ).count()
    history_count = BorrowRecord.query.filter_by(
        user_id=session['user_id'], status='returned'
    ).count()

    return render_template('profile.html', user=user,
                          borrowed_count=borrowed_count,
                          history_count=history_count)

# 管理员：仪表盘
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_books = Book.query.count()
    total_borrowed = BorrowRecord.query.filter_by(status='borrowed').count()
    overdue_count = BorrowRecord.query.filter(
        BorrowRecord.status == 'borrowed',
        BorrowRecord.due_date < datetime.utcnow()
    ).count()

    recent_borrows = BorrowRecord.query.order_by(
        BorrowRecord.borrow_date.desc()
    ).limit(10).all()

    categories_stats = db.session.query(
        Book.category, db.func.count(Book.id)
    ).group_by(Book.category).all()

    monthly_stats = []
    for i in range(5, -1, -1):
        month = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        count = BorrowRecord.query.filter(
            db.extract('year', BorrowRecord.borrow_date) == month.year,
            db.extract('month', BorrowRecord.borrow_date) == month.month
        ).count()
        monthly_stats.append({'month': month.strftime('%Y-%m'), 'count': count})

    return render_template('admin_dashboard.html',
                          total_users=total_users, total_books=total_books,
                          total_borrowed=total_borrowed, overdue_count=overdue_count,
                          recent_borrows=recent_borrows,
                          categories_stats=categories_stats, monthly_stats=monthly_stats)

# 管理员：用户管理
@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# 管理员：重置密码
@app.route('/admin/reset-password/<int:user_id>')
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    user.password = hash_password('123456')
    db.session.commit()
    flash(f'用户 {user.username} 的密码已重置为 123456', 'success')
    return redirect(url_for('admin_users'))

# 管理员：切换用户状态
@app.route('/admin/toggle-user-status/<int:user_id>')
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.status = 'frozen' if user.status == 'normal' else 'normal'
    flash(f'用户 {user.username} 已{"冻结" if user.status == "frozen" else "解封"}', 'success')
    db.session.commit()
    return redirect(url_for('admin_users'))

# 管理员：排行榜
@app.route('/admin/ranking')
@admin_required
def ranking():
    hot_books = Book.query.order_by(Book.borrow_count.desc()).limit(10).all()
    active_users = db.session.query(
        User, db.func.count(BorrowRecord.id).label('borrow_count')
    ).join(BorrowRecord, User.id == BorrowRecord.user_id)\
     .group_by(User.id)\
     .order_by(db.text('borrow_count DESC'))\
     .limit(10).all()
    return render_template('admin_ranking.html', hot_books=hot_books, active_users=active_users)

# 管理员：添加图书
@app.route('/admin/add-book', methods=['GET', 'POST'])
@admin_required
def add_book():
    if request.method == 'POST':
        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            isbn=request.form['isbn'],
            category=request.form['category'],
            total_copies=int(request.form['copies']),
            available_copies=int(request.form['copies'])
        )
        db.session.add(book)
        db.session.commit()
        flash('图书添加成功！', 'success')
        return redirect(url_for('index'))

    categories = ['文学', '科技', '历史', '艺术', '教育', '其他']
    return render_template('add_book.html', categories=categories)

# 管理员：编辑图书
@app.route('/admin/edit-book/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.isbn = request.form['isbn']
        book.category = request.form['category']
        new_total = int(request.form['total_copies'])
        diff = new_total - book.total_copies
        book.total_copies = new_total
        book.available_copies += diff
        db.session.commit()
        flash('图书信息更新成功！', 'success')
        return redirect(url_for('index'))

    categories = ['文学', '科技', '历史', '艺术', '教育', '其他']
    return render_template('edit_book.html', book=book, categories=categories)

# 管理员：删除图书
@app.route('/admin/delete-book/<int:book_id>')
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    active_borrows = BorrowRecord.query.filter_by(book_id=book_id, status='borrowed').first()
    if active_borrows:
        flash('该书还有未归还的借阅，无法删除！', 'error')
        return redirect(url_for('index'))

    db.session.delete(book)
    db.session.commit()
    flash('图书删除成功！', 'success')
    return redirect(url_for('index'))

# 管理员：查看所有借阅记录
@app.route('/admin/borrows')
@admin_required
def admin_borrows():
    records = BorrowRecord.query.order_by(BorrowRecord.borrow_date.desc()).all()
    return render_template('admin_borrows.html', records=records, timedelta=timedelta, datetime=datetime)

# API: 获取图书列表
@app.route('/api/books')
def api_books():
    books = Book.query.all()
    return jsonify([{
        'id': b.id,
        'title': b.title,
        'author': b.author,
        'category': b.category,
        'available': b.available_copies,
        'total': b.total_copies,
        'borrow_count': b.borrow_count
    } for b in books])

# 初始化数据库（保留原函数，方便本地开发）
def init_db():
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=hash_password('admin123'),
                        role='admin', status='normal')
            db.session.add(admin)
            print("管理员账户: admin / admin123")

        if Book.query.count() == 0:
            sample_books = [
                Book(title='三体', author='刘慈欣', category='文学', total_copies=3, available_copies=3),
                Book(title='Python编程', author='Eric Matthes', category='科技', total_copies=3, available_copies=3),
                Book(title='明朝那些事儿', author='当年明月', category='历史', total_copies=2, available_copies=2),
            ]
            for book in sample_books:
                db.session.add(book)
            print(f"已添加 {len(sample_books)} 本示例图书")

        db.session.commit()

# ========== [Railway部署关键] 生产环境下 Gunicorn 启动时自动建表 ==========
# 这行代码确保在 Railway 上（不执行 __main__）也能初始化数据库
init_db()
# ====================================================================

if __name__ == '__main__':
    # 本地开发时使用（因为上面已经调用过 init_db()，这里可注释，但保留也无妨）
    # init_db()   # 如果不想重复调用可以注释掉，但重复调用也没副作用
    print("\n" + "="*50)
    print("🚀 图书管理系统已启动！")
    print("📱 访问地址: http://localhost:5000")
    print("👤 管理员: admin / admin123")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)