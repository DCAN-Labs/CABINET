#!/usr/bin/env python3
# coding: utf-8

from src.valid_jargs_class import ValidJargs

param_json = "invalid-example.json"

Jargs = ValidJargs(param_json)

assert not Jargs.validate_cabinet_options()