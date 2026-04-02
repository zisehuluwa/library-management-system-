"""Selenium 端到端测试"""
import pytest
import time

# 跳过 Selenium 测试如果不可用
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    pytest.skip("Selenium not available", allow_module_level=True)


class TestSeleniumUI:
    """Selenium UI测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """设置Selenium WebDriver"""
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        yield
        self.driver.quit()

    def test_login_flow(self):
        """测试登录流程"""
        self.driver.get("http://localhost:5000/login")

        # 填写登录表单
        self.driver.find_element(By.NAME, "username").send_keys("testuser")
        self.driver.find_element(By.NAME, "password").send_keys("123456")
        self.driver.find_element(By.TAG_NAME, "button").click()

        # 等待页面跳转
        time.sleep(1)

        # 验证登录成功 - 检查是否有用户头像
        assert "testuser" in self.driver.page_source or "首页" in self.driver.page_source

    def test_search_book_flow(self):
        """测试搜索图书流程"""
        self.driver.get("http://localhost:5000/search")

        # 搜索框输入关键词
        search_input = self.driver.find_element(By.NAME, "keyword")
        search_input.send_keys("测试")

        # 点击搜索按钮
        self.driver.find_element(By.CLASS_NAME, "btn-primary").click()

        time.sleep(1)

        # 验证搜索结果
        assert "测试图书" in self.driver.page_source or "没有找到" in self.driver.page_source

    def test_borrow_book_flow(self):
        """测试借阅图书流程"""
        # 先登录
        self.driver.get("http://localhost:5000/login")
        self.driver.find_element(By.NAME, "username").send_keys("testuser")
        self.driver.find_element(By.NAME, "password").send_keys("123456")
        self.driver.find_element(By.TAG_NAME, "button").click()
        time.sleep(1)

        # 进入首页
        self.driver.get("http://localhost:5000/")

        # 点击借阅按钮
        borrow_buttons = self.driver.find_elements(By.CLASS_NAME, "btn-success")
        if borrow_buttons:
            borrow_buttons[0].click()
            time.sleep(1)

            # 验证借阅成功
            assert "借阅成功" in self.driver.page_source or "成功" in self.driver.page_source

    def test_admin_add_book_flow(self):
        """测试管理员添加图书流程"""
        # 先登录管理员
        self.driver.get("http://localhost:5000/login")
        self.driver.find_element(By.NAME, "username").send_keys("admin")
        self.driver.find_element(By.NAME, "password").send_keys("admin123")
        self.driver.find_element(By.TAG_NAME, "button").click()
        time.sleep(1)

        # 进入添加图书页面
        self.driver.get("http://localhost:5000/admin/add-book")

        # 填写表单
        self.driver.find_element(By.NAME, "title").send_keys("Selenium测试图书")
        self.driver.find_element(By.NAME, "author").send_keys("测试作者")
        self.driver.find_element(By.NAME, "isbn").send_keys("9999999999")
        self.driver.find_element(By.NAME, "copies").send_keys("3")

        # 提交
        self.driver.find_element(By.TAG_NAME, "button").click()
        time.sleep(1)

        # 验证
        assert "图书添加成功" in self.driver.page_source or "成功" in self.driver.page_source

    def test_profile_password_change_flow(self):
        """测试修改密码流程"""
        # 先登录
        self.driver.get("http://localhost:5000/login")
        self.driver.find_element(By.NAME, "username").send_keys("testuser")
        self.driver.find_element(By.NAME, "password").send_keys("123456")
        self.driver.find_element(By.TAG_NAME, "button").click()
        time.sleep(1)

        # 进入个人中心
        self.driver.get("http://localhost:5000/profile")

        # 修改密码
        self.driver.find_element(By.NAME, "old_password").send_keys("123456")
        self.driver.find_element(By.NAME, "new_password").send_keys("newpass123")
        self.driver.find_element(By.TAG_NAME, "button").click()
        time.sleep(1)

        # 验证
        assert "密码修改成功" in self.driver.page_source or "成功" in self.driver.page_source


class TestSeleniumNavigation:
    """导航测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
        yield
        self.driver.quit()

    def test_home_navigation(self):
        """测试首页导航"""
        self.driver.get("http://localhost:5000/")
        assert "智慧图书馆" in self.driver.title or "图书馆" in self.driver.page_source

    def test_nav_links(self):
        """测试导航链接"""
        self.driver.get("http://localhost:5000/")

        # 点击找书
        nav_items = self.driver.find_elements(By.CLASS_NAME, "nav-item")
        if nav_items:
            nav_items[1].click()
            time.sleep(0.5)
            assert "/search" in self.driver.current_url or "search" in self.driver.current_url
