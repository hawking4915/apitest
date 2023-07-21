import time
import unittest
from ddt import ddt, data
from functools import partial

from common import bif_functions
from common.action import Action
from common.config import Config
from common.database.mysql_client import MysqlClient
from common.file_handling.do_excel import DoExcel
from common.utils.mylogger import MyLogger
from extensions import dynamic_scaling_methods

test_file = Config.test_case  # 获取 excel 文件路径
excel = DoExcel(test_file)
init_data, test_case = excel.get_excel_init_and_cases()

databases = init_data.get('databases')  # 获取数据库配置信息

logger = MyLogger()
initialize_data = eval(init_data.get("initialize_data"))
host = init_data.get('host', "") + init_data.get("path", "")


@ddt
class TestProjectApi(unittest.TestCase):
	maxDiff = None
	action = Action(initialize_data, bif_functions, databases)
	
	@classmethod
	def setUpClass(cls) -> None:
		pass
	
	def setUp(self) -> None:
		self.action.set_bif_fun(dynamic_scaling_methods)
	
	@data(*test_case)
	def test_api(self, item):
		sheet, iid, condition, st, name, desc, h_crypto, r_crypto, method, expected = self.__base_info(item)
		if self.__is_run(condition):
			self.skipTest("这个测试用例听说泡面比较好吃，所以放弃执行了！！")
		regex, keys, deps, jp_dict, ex_request_data = self.__extractor_info(item)
		setup_script, teardown_script = self.script(item)
		self.__pause_execution(st)
		
		# 首执行 sql
		self.__exc_sql(item)
		if method.upper() == 'SQL':
			self.skipTest("这条测试用例被 SQL 吃了，所以放弃执行了！！")
		
		# 执行动态代码
		item = self.action.execute_dynamic_code(item, setup_script)
		
		# prepost_script = f"prepost_script_{sheet}_{iid}.py"
		# item = self.action.load_and_execute_script(Config.SCRIPTS_DIR, prepost_script, "setup", item)
		
		# 修正参数
		item = self.action.replace_dependent_parameter(item)
		url, query_str, request_data, headers, request_data_type = self.__request_info(item)
		
		# 分析请求参数信息
		headers, request_data = self.action.analysis_request(request_data, h_crypto, headers, r_crypto, ex_request_data)
		result_tp = None
		result = "PASS"
		
		# 执行请求操作
		kwargs = {request_data_type: request_data, 'headers': headers, "params": query_str}
		response = self.action.send_request(host, url, method, teardown_script, **kwargs)
		
		try:
			# 提取响应
			self.action.substitute_data(response.json(), regex=regex, keys=keys, deps=deps, jp_dict=jp_dict)
		except Exception as err:
			logger.error(f"提取响应失败：{sheet}_{iid}_{name}_{desc}"
			             f"\nregex={regex};"
			             f" \nkeys={keys};"
			             f"\ndeps={deps};"
			             f"\njp_dict={jp_dict}"
			             f"\n{err}")
		
		# 修正断言
		expected = self.action.replace_dependent_parameter(expected)
		try:
			print(f"期望结果--> {expected}")
			# 执行断言 返回结果元组
			result_tp = self.action.run_validate(expected, response.json())
			self.assertNotIn("FAIL", result_tp, "FAIL 存在结果元组中")
		except Exception as e:
			result = "FAIL"
			logger.error(f'异常用例: **{sheet}_{iid}_{name}_{desc}**\n{e}')
			raise e
		finally:
			response = response.text if response is not None else str(response)
			# 响应结果及测试结果回写 excel
			excel.write_back(sheet_name=sheet, i=iid, response=response, test_result=result, assert_log=str(result_tp))
	
	@classmethod
	def tearDownClass(cls) -> None:
		excel.close_excel()
		logger.info(f"所有用例执行完毕")
	
	@staticmethod
	def __base_info(item):
		"""
		获取基础信息
		"""
		sheet = item.pop("sheet")
		item_id = item.pop("Id")
		condition = item.pop("Run")
		sleep_time = item.pop("Time")
		name = item.pop("Name")
		desc = item.pop("Description")
		headers_crypto = item.pop("Headers Crypto")
		request_data_crypto = item.pop("Request Data Crypto")
		method = item.pop("Method")
		expected = item.pop("Expected")
		return sheet, item_id, condition, sleep_time, name, desc, headers_crypto, request_data_crypto, method, expected
	
	@staticmethod
	def __sql_info(item):
		sql = item.pop("SQL")
		sql_params_dict = item.pop("Sql Params Dict")
		return sql, sql_params_dict
	
	@staticmethod
	def __extractor_info(item):
		"""
		获取提取参数的基本字段信息
		Args:
			item:
	
		Returns:
	
		"""
		regex = item.pop("Regex")
		keys = item.pop("Regex Params List")
		deps = item.pop("Retrieve Value")
		jp_dict = item.pop("Jsonpath")
		extract_request_data = item.pop("Extract Request Data")
		return regex, keys, deps, jp_dict, extract_request_data
	
	@staticmethod
	def __request_info(item):
		"""
		请求数据
		"""
		url = item.pop("Url")
		query_str = item.pop("Query Str")
		request_data = item.pop("Request Data")
		headers = item.pop("Headers")
		request_data_type = item.pop("Request Data Type") if item.get("Request Data Type") else 'params'
		
		return url, query_str, request_data, headers, request_data_type
	
	@staticmethod
	def script(item):
		setup_script = item.pop("Setup Script")
		teardown_script = item.pop("Teardown Script")
		return setup_script, teardown_script
	
	@staticmethod
	def __is_run(condition):
		is_run = condition
		if not is_run or is_run.upper() != "YES":
			return True
	
	@staticmethod
	def __pause_execution(sleep_time):
		if sleep_time:
			try:
				time.sleep(sleep_time)
			except Exception as e:
				logger.error("暂时时间必须是数字")
				raise e
	
	def __exc_sql(self, item):
		sql, sql_params_dict = self.__sql_info(item)
		sql = self.action.replace_dependent_parameter(sql)
		if sql:
			try:
				execute_sql_results = self.action.execute_sql(sql)
				if execute_sql_results and sql_params_dict:
					self.action.substitute_data(execute_sql_results, jp_dict=sql_params_dict)
			except Exception as e:
				logger.error(f'执行 sql 失败:{sql},异常信息:{e}')
				raise e


if __name__ == '__main__':
	unittest.main()
