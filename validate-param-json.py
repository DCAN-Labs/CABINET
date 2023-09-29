#!/usr/bin/env python3
# coding: utf-8

"""
Script for validating cabinet input parameter jsons without running the whole pipeline
"""
from src.valid_jargs_class import ValidJargs

def main():
    # Get and validate command-line arguments and parameters from .JSON file
    Jargs = ValidJargs()

if __name__ == "__main__":
    main()