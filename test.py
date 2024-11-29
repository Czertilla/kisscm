import pytest
import shutil
from main import Emulator
from logger import color
import sys
class ListStream:
    def __init__(self):
        self.data = []
    def write(self, s):
        self.data.append(s)


for i in range(2):
    print ('i = ', i)


TARGET = "test.zip"

def setup_module(module):
    shutil.copy(TARGET, TARGET+".backup")
    with open(TARGET, 'wb') as f:
        pass


def teardown_module(module):
    shutil.copy(TARGET+".backup", TARGET)
    print('AAAA')
    with open(TARGET+".backup", 'wb') as f:
        pass


def test_touch():
    with Emulator(TARGET, mode="a") as emulator:
        emulator.touch("file")
        emulator.mkdir("abba")
        emulator.change_dir("abba")
        emulator.touch("file")
        emulator.change_dir("..")
        emulator.touch("abba/other")
        emulator.touch("bobba/file")
        emulator.change_dir("notexists")
        emulator.touch("file")
        assert emulator.namelist() == ["file", "abba/", "abba/file", "abba/other", "bobba/", "bobba/file"]
    

def test_tail():
    stdout = sys.stdout
    sys.stdout = x = ListStream()
    with Emulator(TARGET, mode="a") as emulator:
        emulator.writestr("newfile", "123\n456\n789")
        emulator.tail("newfile")
        emulator.tail("not?exits")
    sys.stdout = stdout
    assert x.data == ["123", '\n', "456", "\n", "789", "\n", color("Can`t open this file", "r"), "\n"]


def test_mv():
    with Emulator(TARGET, mode="a") as emulator:
        emulator.move("")
        assert emulator.namelist() == ["file", "abba/", "abba/file", "abba/other", "bobba/", "bobba/file", "newfile"]