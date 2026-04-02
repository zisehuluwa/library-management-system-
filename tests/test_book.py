"""图书模块测试"""
from datetime import datetime, timedelta

class TestBookManagement:
    """图书管理测试"""

    def test_index_page(self, client):
        """测试首页显示图书"""
        response = client.get('/')
        assert response.status_code == 200
        assert '测试图书'.encode() in response.data
        assert '测试作者'.encode() in response.data

    def test_search_by_title(self, client):
        """测试按书名搜索"""
        response = client.get('/search?keyword=测试图书')
        assert response.status_code == 200
        assert '测试图书'.encode() in response.data

    def test_search_by_author(self, client):
        """测试按作者搜索"""
        response = client.get('/search?keyword=测试作者')
        assert response.status_code == 200
        assert '测试图书'.encode() in response.data

    def test_search_by_isbn(self, client):
        """测试按ISBN搜索"""
        response = client.get('/search?keyword=1234567890')
        assert response.status_code == 200
        assert '测试图书'.encode() in response.data

    def test_search_no_results(self, client):
        """测试搜索无结果"""
        response = client.get('/search?keyword=不存在')
        assert response.status_code == 200
        assert '测试图书'.encode() not in response.data

    def test_filter_by_category(self, client):
        """测试按分类筛选"""
        response = client.get('/search?category=科技')
        assert response.status_code == 200
        assert '测试图书'.encode() in response.data

class TestBorrow:
    """借阅功能测试"""

    def test_borrow_book(self, auth_client):
        """测试借阅图书"""
        response = auth_client.get('/borrow/1', follow_redirects=True)
        assert response.status_code == 200
        # 验证借书成功消息
        response_text = response.data.decode('utf-8', errors='ignore')
        assert '借书成功' in response_text

    def test_borrow_without_login(self, client):
        """测试未登录借阅"""
        response = client.get('/borrow/1', follow_redirects=True)
        assert response.status_code == 200
        # 应该重定向到登录相关页面
        assert '登录'.encode() in response.data or '首页'.encode() in response.data

    def test_my_books_page(self, auth_client):
        """测试我的借阅页面"""
        # 先借阅
        auth_client.get('/borrow/1')

        # 访问我的借阅页面
        response = auth_client.get('/my-books')
        assert response.status_code == 200
        assert '测试图书'.encode() in response.data

class TestBookAdmin:
    """管理员图书操作测试"""

    def test_add_book_page_access(self, admin_client):
        """测试添加图书页面访问"""
        response = admin_client.get('/admin/add-book')
        assert response.status_code == 200
        assert '添加图书'.encode() in response.data

    def test_add_book_success(self, admin_client):
        """测试成功添加图书"""
        response = admin_client.post('/admin/add-book', data={
            'title': '新书测试',
            'author': '新作者',
            'isbn': '9876543210',
            'category': '文学',
            'copies': 5
        }, follow_redirects=True)

        assert response.status_code == 200
        assert '图书添加成功'.encode() in response.data

        # 验证数据库
        from app import Book
        book = Book.query.filter_by(title='新书测试').first()
        assert book is not None
        assert book.author == '新作者'
        assert book.total_copies == 5
        assert book.available_copies == 5

    def test_edit_book(self, admin_client):
        """测试编辑图书"""
        from app import Book
        book = Book.query.first()

        response = admin_client.post(f'/admin/edit-book/{book.id}', data={
            'title': '修改后的标题',
            'author': '修改后的作者',
            'isbn': '1111111111',
            'category': '历史',
            'total_copies': 10
        }, follow_redirects=True)

        assert '图书信息更新成功'.encode() in response.data

        # 验证更新
        updated_book = Book.query.get(book.id)
        assert updated_book.title == '修改后的标题'
        assert updated_book.author == '修改后的作者'
        assert updated_book.category == '历史'
        assert updated_book.total_copies == 10

    def test_delete_book(self, admin_client):
        """测试删除图书"""
        from app import db, Book
        # 先添加一本可删除的书
        book = Book(
            title='待删除',
            author='作者',
            total_copies=1,
            available_copies=1
        )
        db.session.add(book)
        db.session.commit()

        response = admin_client.get(f'/admin/delete-book/{book.id}', follow_redirects=True)
        assert '图书删除成功'.encode() in response.data

        # 验证已删除
        deleted_book = Book.query.get(book.id)
        assert deleted_book is None

    def test_delete_book_with_borrows(self, admin_client):
        """测试删除有借阅记录的图书"""
        from app import db, Book, BorrowRecord, User

        # 获取现有的用户和图书
        user = User.query.filter_by(username='testuser').first()
        book = Book.query.first()

        # 创建借阅记录
        borrow = BorrowRecord(
            user_id=user.id,
            book_id=book.id,
            borrow_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            status='borrowed'
        )
        db.session.add(borrow)
        db.session.commit()

        # 尝试删除
        response = admin_client.get(f'/admin/delete-book/{book.id}', follow_redirects=True)

        # 应该看到不能删除的提示
        assert response.status_code == 200
        # 检查是否有相关错误消息
        response_text = response.data.decode('utf-8', errors='ignore')
        assert '还有未归还' in response_text or '无法删除' in response_text
