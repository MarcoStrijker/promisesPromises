# This is nonsense code to test the pylinter

import os

def remove_file(file_name):

    if os.path.exists(file_name):
        os.remove(file_name)
    else:
        print("The file does not exist")

remove_file("test.txt")
remove_file("test2.txt")

test = 9 + 9
# Path: src/remove_test_file.py

import os
