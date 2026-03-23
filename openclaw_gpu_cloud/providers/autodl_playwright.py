"""
AutoDL Playwright 提供者
使用浏览器自动化模拟 AutoDL 操作（登录、租用、释放）
"""

import os
import time
import json
from typing import Optional, List, Dict
from playwright.sync_api import sync_playwright, Page, Browser
from ..scheduler import CloudInstance
from ..estimator import ResourceEstimate


class AutoDLPlaywrightProvider:
    """
    AutoDL Playwright 自动化提供者
    
    通过模拟浏览器操作实现 AutoDL 实例管理
    """
    
    BASE_URL = "https://www.autodl.com"
    CONSOLE_URL = "https://www.autodl.com/console"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        初始化提供者
        
        Args:
            username: AutoDL 用户名（或手机号/邮箱）
            password: AutoDL 密码
        """
        self.username = username or os.environ.get("AUTODL_USERNAME")
        self.password = password or os.environ.get("AUTODL_PASSWORD")
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
    
    def _get_browser(self, headless: bool = True) -> Browser:
        """获取浏览器实例"""
        if self.browser is None:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                ]
            )
        return self.browser
    
    def _get_page(self, headless: bool = True) -> Page:
        """获取页面实例"""
        if self.page is None or self.page.is_closed():
            browser = self._get_browser(headless)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self.page = context.new_page()
        return self.page
    
    def login(self, headless: bool = False, timeout: int = 120) -> bool:
        """
        登录 AutoDL
        
        Args:
            headless: 是否无头模式（登录时建议 False，方便验证码）
            timeout: 超时时间（秒）
        
        Returns:
            是否登录成功
        """
        if self.is_logged_in:
            return True
        
        if not self.username or not self.password:
            raise ValueError("请设置 AUTODL_USERNAME 和 AUTODL_PASSWORD 环境变量")
        
        page = self._get_page(headless)
        
        # 打开登录页
        page.goto(f"{self.BASE_URL}/login", timeout=timeout * 1000)
        
        # 等待登录表单
        page.wait_for_selector('input[name="username"], input[placeholder*="手机号"]', 
                               timeout=timeout * 1000)
        
        # 填写用户名和密码
        username_selector = 'input[name="username"], input[placeholder*="手机号"]'
        password_selector = 'input[name="password"], input[placeholder*="密码"]'
        
        page.fill(username_selector, self.username)
        page.fill(password_selector, self.password)
        
        # 点击登录按钮
        login_button = page.locator('button:has-text("登录")').first
        login_button.click()
        
        # 等待跳转到控制台
        try:
            page.wait_for_url(f"{self.CONSOLE_URL}**", timeout=timeout * 1000)
            self.is_logged_in = True
            print("✓ AutoDL 登录成功")
            return True
        except:
            print("✗ AutoDL 登录失败，请检查账号密码或手动验证码")
            return False
    
    def list_instances(self, headless: bool = True) -> List[Dict]:
        """
        获取当前所有实例
        
        Returns:
            实例列表
        """
        if not self.is_logged_in:
            if not self.login(headless):
                return []
        
        page = self._get_page(headless)
        page.goto(f"{self.CONSOLE_URL}/instances", timeout=30000)
        
        # 等待实例列表加载
        time.sleep(2)
        
        instances = []
        
        # 解析实例列表（需要根据实际页面结构调整）
        try:
            instance_rows = page.locator('table tr, .instance-card, .instance-item')
            
            for i, row in enumerate(instance_rows.all()):
                if i == 0:  # 跳过表头
                    continue
                
                try:
                    name = row.locator('.name, .instance-name').first.inner_text()
                    status = row.locator('.status, .instance-status').first.inner_text()
                    gpu = row.locator('.gpu, .instance-gpu').first.inner_text()
                    ip = row.locator('.ip, .instance-ip').first.inner_text()
                    
                    instances.append({
                        "name": name,
                        "status": status,
                        "gpu": gpu,
                        "ip": ip,
                    })
                except:
                    continue
        except Exception as e:
            print(f"解析实例列表失败: {e}")
        
        return instances
    
    def create_instance(
        self,
        requirements: ResourceEstimate,
        image_name: Optional[str] = None,
        auto_stop: bool = True
    ) -> CloudInstance:
        """
        创建 GPU 实例
        
        Args:
            requirements: 资源需求
            image_name: 镜像名称（默认使用 Ubuntu 20.04）
            auto_stop: 是否自动停止
        
        Returns:
            云实例对象
        """
        if not self.is_logged_in:
            if not self.login():
                raise RuntimeError("登录失败")
        
        page = self._get_page(headless=True)
        page.goto(f"{self.CONSOLE_URL}/create", timeout=30000)
        
        # 选择 GPU 型号
        gpu_selector = requirements.gpu_type.replace(" ", "").lower()
        page.click(f'[data-gpu*="{gpu_selector}"], .gpu-card:has-text("{requirements.gpu_type}")')
        
        # 选择镜像
        if image_name:
            page.fill('input[placeholder*="镜像"], .search-image', image_name)
        else:
            page.click('.image-card:has-text("Ubuntu"), .image-card:has-text("20.04")')
        
        # 点击创建
        page.click('button:has-text("创建"), button:has-text("立即租用")')
        
        # 等待实例创建
        page.wait_for_selector('.instance-created, .instance-card', timeout=120000)
        
        # 获取实例信息
        instance_id = page.locator('.instance-id, [data-instance-id]').first.inner_text()
        ip = page.locator('.instance-ip, .ip-address').first.inner_text()
        
        # 保存 Cookie 以便后续使用
        cookies = page.context.cookies()
        self._save_cookies(cookies)
        
        return CloudInstance(
            instance_id=instance_id,
            platform="autodl",
            gpu_type=requirements.gpu_type,
            ip=ip,
            ssh_user="root",
            ssh_key_path=None,  # AutoDL 通常使用密码
        )
    
    def destroy_instance(self, instance_id: str) -> bool:
        """
        销毁实例
        
        Args:
            instance_id: 实例 ID
        
        Returns:
            是否成功
        """
        if not self.is_logged_in:
            if not self.login():
                return False
        
        page = self._get_page(headless=True)
        page.goto(f"{self.CONSOLE_URL}/instances", timeout=30000)
        
        # 找到对应实例并点击释放
        try:
            instance_row = page.locator(f'[data-instance-id="{instance_id}"]').first
            
            # 点击停止
            instance_row.locator('button:has-text("停止"), button:has-text("关机")').click()
            time.sleep(2)
            
            # 点击释放
            instance_row.locator('button:has-text("释放"), button:has-text("删除")').click()
            
            # 确认释放
            page.click('button:has-text("确认"), button:has-text("是")')
            
            print(f"✓ 实例 {instance_id} 已释放")
            return True
        except Exception as e:
            print(f"✗ 释放实例 {instance_id} 失败: {e}")
            return False
    
    def _save_cookies(self, cookies: List[Dict]):
        """保存 Cookie 到本地"""
        cookies_path = os.path.expanduser("~/.autodl_cookies.json")
        with open(cookies_path, "w") as f:
            json.dump(cookies, f, indent=2)
    
    def _load_cookies(self) -> List[Dict]:
        """加载 Cookie"""
        cookies_path = os.path.expanduser("~/.autodl_cookies.json")
        if os.path.exists(cookies_path):
            with open(cookies_path, "r") as f:
                return json.load(f)
        return []
    
    def close(self):
        """关闭浏览器"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
            sync_playwright().stop()
    
    def __enter__(self):
        """上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """关闭浏览器"""
        self.close()


# 使用示例
if __name__ == "__main__":
    with AutoDLPlaywrightProvider() as provider:
        # 登录
        if provider.login(headless=False):
            # 列出实例
            instances = provider.list_instances()
            print(f"当前实例: {len(instances)} 个")
            for inst in instances:
                print(f"  - {inst['name']}: {inst['status']} ({inst['ip']})")
