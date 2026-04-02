"""API 接口测试 - 需要实现 API 路由"""
import pytest
import json

# 这些测试需要先实现 API 路由，暂时跳过
pytestmark = pytest.mark.skip(reason="API routes not yet implemented")

class TestBookAPI:
    """图书相关API测试"""

    def test_api_books_list(self, client):
        """测试获取图书列表API"""
        response = client.get('/api/books')
        assert response.status_code == 200

    def test_api_search_books(self, client):
        """测试搜索图书API"""
        response = client.get('/api/books/search?keyword=测试')
        assert response.status_code == 200

    def test_api_book_detail(self, client):
        """测试获取图书详情API"""
        response = client.get('/api/books/1')
        assert response.status_code in [200, 404]

class TestUserAPI:
    """用户相关API测试"""

    def test_api_user_profile(self, auth_client):
        """测试获取用户信息API"""
        response = auth_client.get('/api/user/profile')
        assert response.status_code == 200

    def test_api_user_borrows(self, auth_client):
        """测试获取用户借阅记录API"""
        response = auth_client.get('/api/user/borrows')
        assert response.status_code == 200
