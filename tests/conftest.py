import sys
import os
import tempfile
import hashlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 在导入 app 之前设置 TESTING 模式
# 这样 app.py 会使用内存数据库
os.environ['TESTING'] = 'true'

@pytest.fixture(scope='function')
def app():
    """创建测试应用"""
    # 创建临时数据库文件用于测试（内存数据库会创建在内存中，但我们需要持久化以便共享）
    # 实际上对于每个测试，我们使用独立的内存数据库连接

    print(f"\n[FIXTURE] Setting up test app")

    # 导入 app - 此时 app.config['TESTING'] 应该已经是 True
    from app import app, db, User, Book, BorrowRecord

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        print(f"[FIXTURE] DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"[FIXTURE] Engine URL: {db.engine.url}")

        # 清空并重建数据库
        print(f"[FIXTURE] Dropping all tables...")
        db.drop_all()
        print(f"[FIXTURE] Creating tables...")
        db.create_all()

        # 创建测试数据
        admin = User(
            username='admin',
            password=hash_password('admin123'),
            role='admin',
            status='normal'
        )
        user = User(
            username='testuser',
            password=hash_password('123456'),
            role='user',
            status='normal'
        )
        book = Book(
            title='测试图书',
            author='测试作者',
            isbn='1234567890',
            category='科技',
            total_copies=3,
            available_copies=3,
            borrow_count=0
        )
        db.session.add_all([admin, user, book])
        db.session.commit()

        users = User.query.all()
        print(f"[FIXTURE] Users after setup: {len(users)} - {[u.username for u in users]}")

        yield app

        print(f"[FIXTURE] Cleaning up...")
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """测试客户端"""
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_client(client):
    """已认证的测试客户端"""
    with client.session_transaction() as sess:
        sess['user_id'] = 2  # testuser
        sess['username'] = 'testuser'
        sess['role'] = 'user'
    return client

@pytest.fixture
def admin_client(client):
    """管理员测试客户端"""
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # admin
        sess['username'] = 'admin'
        sess['role'] = 'admin'
    return client
