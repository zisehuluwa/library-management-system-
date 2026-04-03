import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as application

# Vercel Python runtime handler
def handler(request):
    """处理HTTP请求"""
    # 使用Flask的test_client处理请求
    with application.test_client() as client:
        # 获取请求路径和方法
        path = request.path if hasattr(request, 'path') else '/'
        method = request.method if hasattr(request, 'method') else 'GET'

        # 处理请求
        if method == 'GET':
            response = client.get(path, query_string=request.query_string)
        elif method == 'POST':
            response = client.post(path, data=request.get_data())
        else:
            response = client.get(path)

        return response

# 保持向后兼容
app = application
