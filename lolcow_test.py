#!/usr/bin/env python3
# coding: utf-8

from src.valid_jargs_class import ValidJargs
from src.wrapper_class import Wrapper

param_json = "lolcow_test.json"

Jargs = ValidJargs(param_json)

Test = Wrapper(Jargs)

def test_run_stage_pass():

    assert Test.run_stage("lolcow")

def test_run_stage_fail():
    
    assert not Test.run_stage("dockerfail")
