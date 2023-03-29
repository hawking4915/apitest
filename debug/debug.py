#!/usr/bin/env python
# encoding: utf-8
"""
@author: kira
@contact: 262667641@qq.com
@file: debug.py
@time: 2023/3/29 11:40
@desc:
"""
import re
from common.dependence import Dependence
from common.comparator import loaders

lo = loaders.set_bif_fun()
pa = Dependence.PATTERN
di = Dependence.get_dep()
patten = re.compile(r"\{\{(\w+\(\))\}\}")
jst = '{{get_current_time()}}'
ret = patten.search(jst)
print(ret)
if ret:
    if jst in di.keys():
        print(di.get(jst))
        jst = jst.replace(jst, di.get(jst)())
print(jst)
