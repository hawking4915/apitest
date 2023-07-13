# -*- coding: utf-8 -*-
import json
import mimetypes
import re
import sys

import requests
import urllib3

sys.path.append("../")
sys.path.append("./common")

from common.http_client import logger
from common.validation.load_modules_from_folder import LoadModulesFromFolder
from common.file_handling.file_utils import FileUtils


class Pyt(LoadModulesFromFolder):
    # 类属性，保存一个会话对象，防止每次都创建一个新的会话，节省资源
    session = requests.Session()
    file_utils = FileUtils()
    
    def __init__(self):
        super().__init__()
        self.request = None
        self.response = None
    
    def log_decorator(msg="请求异常"):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    print(f"发送请求的参数： {kwargs}")
                    response = func(*args, **kwargs)
                    print(f"请求地址 --> {response.request.url}")
                    print(f"请求头 --> {response.request.headers}")
                    print(f"请求 body --> {response.request.body}")
                    print(f"接口状态--> {response.status_code}")
                    print(f"接口耗时--> {response.elapsed}")
                    print(f"接口响应--> {response.text}")
                    return response
                except Exception as e:
                    logger.error(f"发送请求失败: {e}")
                    return
            
            return wrapper
        
        return decorator
    
    # def pre_script(self,name):
    # 	def decorator(func):
    # 		self.variables = func
    # 	return decorator
    
    @log_decorator()
    def http_client(self, host, url, method, **kwargs):
        """
        发送 http 请求
        @param host: 域名
        @param url: 接口 __url
        @param method: http 请求方法
        @param kwargs: 接受 requests 原生的关键字参数
        @return: 响应对象
        """
        # 关闭 https 警告信息
        urllib3.disable_warnings()
        
        if not url:
            raise ValueError("URL cannot be None")
        __url = f'{host}{url}' if not re.match(r"https?", url) else url
        
        # 增加兼容
        # 处理 headers 参数为字符串类型的情况
        if 'headers' in kwargs and isinstance(kwargs['headers'], str):
            kwargs['headers'] = json.loads(kwargs['headers'])
        
        # 处理 json 参数为字符串类型的情况
        if 'json' in kwargs and isinstance(kwargs['json'], str):
            kwargs['json'] = json.loads(kwargs['json'])
        
        # 处理 files 参数的情况
        if 'files' in kwargs:
            file_paths = kwargs['files']
            if isinstance(file_paths, str):
                file_paths = json.loads(file_paths)
            files = []
            fs = []
            for i, file_path in enumerate(file_paths):
                file_type = mimetypes.guess_type(file_path)[0]
                file_path_completion = self.file_utils.get_file_path(file_path)
                f = open(file_path_completion, 'rb')
                fs.append(f)
                files.append(
                    ('file', (f'{file_path}', f, file_type))
                )
            kwargs['files'] = files
            print(kwargs)
        
        # 发送请求
        self.request = requests.Request(method, __url, **kwargs)
        self.response = self.session.send(self.request.prepare(), timeout=30, verify=True)
        [i.close() for i in fs if len(fs) > 0]
        return self.response


if __name__ == '__main__':
    hst = 'https://bimdc.bzlrobot.com'
    url = '/bsp/test/user/ugs/ibs/api/ibs-file/file-upload/upload-image'
    method = 'post'
    kwargs = {
        'headers': {},
        'data': {},
        'files': ['test.txt']
    }
    pyt = Pyt()
    pyt.http_client(hst, url, method, **kwargs)
