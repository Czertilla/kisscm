import pytest
import main

def setup_module(module):
    pass

def teardown_module(module):
    pass

def test_parse_line():
    parser = main.Parser()
    parser.parse_line("let A = 2;")
    parser.parse_line("let B = '123';")
    parser.parse_line("let C = @{ A = A; B = B }")
    parser.parse_line("let d = 'invalid key")
    assert not parser.current_dict
    assert parser.variables == {
        "A": 2, 
        "B": '123', 
        "C": {
            "A": 2, 
            "B": '123',
        }
    }
    parser.parse_line("@{")
    parser.parse_line("let D = $* A 123$;")
    parser.parse_line("DA = D;")
    parser.parse_line("ASD = '1232';")
    parser.parse_line("ASD = 'dublicate key';")
    parser.parse_line("ASS = @{ S = D }")
    assert parser.current_dict == {
        "DA": 246,
        "ASD": '1232',
        "ASS": {
            "S": 246
        }
    }