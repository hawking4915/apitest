# coding: utf-8

# -------------------------------------------------------------------------------
# Name:         loader.py
# Description:
# Author:       kira
# EMAIL:        262667641@qq.com
# Date:         2019/11/18 17:32
# -------------------------------------------------------------------------------
import types

from common.http_client.http_client import Pyt
from common.validation import comparators
from common.validation import logger


class Loaders(Pyt):
	def __init__(self):
		super().__init__()
	
	@logger.log_decorator()
	def load_built_in_functions(self, model):
		"""
		加载bif_functions包中的内建方法
		Returns:
		"""
		built_in_functions = {}
		for name, item in vars(model).items():
			if isinstance(item, types.FunctionType):
				built_in_functions[name] = item
		return built_in_functions
	
	@staticmethod
	@logger.log_decorator()
	def load_built_in_comparators() -> object:
		"""
		加载包中的内建比较器
		Returns:
	
		"""
		built_in_comparators = {}
		for name, item in vars(comparators).items():
			if isinstance(item, types.FunctionType):
				built_in_comparators[name] = item
		
		return built_in_comparators
	
	@logger.log_decorator()
	def set_bif_fun(self, model):
		"""
		将所有内置方法加载到依赖表中
		Returns:
	
		"""
		for k, v in self.load_built_in_functions(model).items():
			self.update_environments(f"{k}()", v)


if __name__ == '__main__':
	from common.bif_functions import random_tools
	import extensions
	
	print()
	loaders = Loaders()
	loaders.load_built_in_comparators()
	loaders.set_bif_fun(random_tools)
	print(loaders.get_environments())
	
	loaders.set_bif_fun(extensions)
	print(loaders.get_environments())
