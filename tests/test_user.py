import pytest

class TestUserRegistration:
    """用户注册测试"""

    def test_register_success(self, client):
        """测试成功注册"""
        response = client.post('/register', data={
            'username': 'newuser',
            'password': 'password123'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert '注册成功'.encode() in response.data

        # 验证数据库
        from app import db, User
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.role == 'user'
        assert user.status == 'normal'

    def test_register_duplicate_username(self, client):
        """测试重复用户名"""
        # 第一次注册
        client.post('/register', data={
            'username': 'duplicate',
            'password': 'pass123'
        })

        # 第二次注册相同用户名
        response = client.post('/register', data={
            'username': 'duplicate',
            'password': 'pass456'
        }, follow_redirects=True)

        assert '用户名已存在'.encode() in response.data

    def test_register_missing_fields(self, client):
        """测试缺少必填字段"""
        response = client.post('/register', data={
            'username': 'test',
            'password': ''
        }, follow_redirects=True)

        # 应该停留在注册页面
        assert '注册'.encode() in response.data

class TestUserLogin:
    """用户登录测试"""

    def test_login_success(self, client):
        """测试成功登录"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': '123456'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert '登录成功'.encode() in response.data

    def test_login_wrong_password(self, client):
        """测试错误密码"""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpass'
        }, follow_redirects=True)

        assert '用户名或密码错误'.encode() in response.data

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': '123456'
        }, follow_redirects=True)

        assert '用户名或密码错误'.encode() in response.data

    def test_login_frozen_user(self, client):
        """测试冻结用户登录"""
        from app import db, User
        # 冻结用户
        user = User.query.filter_by(username='testuser').first()
        user.status = 'frozen'
        db.session.commit()

        response = client.post('/login', data={
            'username': 'testuser',
            'password': '123456'
        }, follow_redirects=True)

        assert '账号已被冻结'.encode() in response.data

class TestUserProfile:
    """个人中心测试"""

    def test_profile_page_access(self, auth_client):
        """测试个人中心页面访问"""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert '个人中心'.encode() in response.data

    def test_change_password_success(self, auth_client):
        """测试成功修改密码"""
        response = auth_client.post('/profile', data={
            'old_password': '123456',
            'new_password': 'newpass123'
        }, follow_redirects=True)

        assert '密码修改成功'.encode() in response.data

        # 验证新密码登录
        login_response = auth_client.post('/login', data={
            'username': 'testuser',
            'password': 'newpass123'
        }, follow_redirects=True)
        assert '登录成功'.encode() in login_response.data

    def test_change_password_wrong_old(self, auth_client):
        """测试错误原密码"""
        response = auth_client.post('/profile', data={
            'old_password': 'wrongpass',
            'new_password': 'newpass123'
        }, follow_redirects=True)

        assert '原密码错误'.encode() in response.data

    def test_profile_requires_login(self, client):
        """测试未登录访问个人中心"""
        response = client.get('/profile', follow_redirects=True)
        assert '请先登录'.encode() in response.data
