import re
import copy

class Parser:
    SEP = r"[ ;]+(?=(?:[^\$]*\$[^\$]*\$)*[^\$]*$)(?=(?:[^\']*\'[^\']*\')*[^\']*$)"
    NAME_RE = r"[A-Z]+"

    def __init__(self) -> None:
        self.backup = None
        self.variables = {}
        self.current_dict = None
        self.dict_stack = []
        self.buffer: list[str] = []
        self.end_dict_flag = False

    def dump(self):
        print(self.current_dict)
        print(self.variables)

    def error(self, line: str, message: str):
        print(f"{line}: {message}")
        self.reverte_from_backup()

    def reverte_from_backup(self):
        self.variables = self.backup.variables
        self.current_dict = self.backup.current_dict
        self.dict_stack = self.backup.dict_stack
        self.buffer = self.backup.buffer

    def validate_name(self, name: str) -> bool:
        if not re.fullmatch(self.NAME_RE, name):
            self.error(name, "unexpected name format")
            return False
        return True
    
    def get_value(self, key: str, line: str) -> str|dict|float|int|None:
        value = self.variables.get(
            key, 
            self.current_dict.get(
                key,
                None
            )
        )
        if value is None:
            return self.error(line, f"name {key} is not defined")
        return value
    
    def parse_expression(self, line: str) -> str|dict|float|int|None:
        if line.startswith("ord("):
            if not line.endswith(")"):
                return self.error(line, ") expected")
            arg = line[4:-1]
            if re.fullmatch(self.NAME_RE, arg):
                arg = self.get_value(arg, line)
                if arg is None:
                    return
            else:
                value = self.parse_value(arg)
                if value is None:
                    return
            if isinstance(value, str):
                return ord(value)
            return self.error(line, "ord() argument can be only string")
        signature = line.split()
        stack = []
        for i, I in enumerate(signature[::-1]):
            if I in "+-*":
                if len(stack) < 2:
                    return self.error(line, f"expected operand, but {I} given")
                try:
                    match I:
                        case '+':
                            if isinstance(stack[-1], dict) and isinstance(stack[-2], dict):
                                stack[-1].update(stack[-2])
                                result = stack[-1]
                            else:
                                result = stack[-1] + stack[-2]
                        case '-':
                            result = stack[-1] - stack[-2]
                        case '*':
                            result = stack[-1] * stack[-2]
                except Exception as e:
                    return self.error(line, f"expression raised exception: {e}")
                stack = stack[:-2] + [result]
            else:
                if re.fullmatch(self.NAME_RE, I):
                    value = self.get_value(I, line)
                else:
                    if (I.startswith("@{")):
                        return self.error(line, "no dicts in ")
                    value = self.parse_value(I)
                if value is None:
                    return
                stack.append(value)
        return stack[-1]
            

    def parse_value(self, value: str) -> str|None:
        if value.startswith("'") != value.endswith("'"):
            return self.error(value, "symbol ' missed - unclosed string")
        if value.startswith("'"):
            value = value[1:-1]
        elif value.startswith("@{"):
            value = self.new_dict
        elif value.isnumeric():
            value = int(value)
        else:
            value = float(value)
        return value

    def parse_line(self, line: str):
        self.end_dict_flag = not line.endswith(";") and not line.endswith("{")
        self.backup = copy.deepcopy(self)
        signature: list[str] = re.split(self.SEP, line)
        start = len(self.buffer)
        self.buffer += signature
        self.new_dict = {}
        for i in range(start, len(self.buffer)):
            I = self.buffer[i]
            if I.startswith("@{"):
                self.current_dict = self.new_dict
                self.new_dict = {}
                self.buffer[i] = I[2:]
                self.dict_stack.append(self.current_dict)
            elif I == "let":
                if i + 3 >= len(self.buffer):
                    return self.error(I, "expected constant value expression, but EOL given")
                var_name = self.buffer[i+1]
                if var_name in self.variables:
                    return self.error(I, f"{var_name=} constant already exists in this scope")
                if not self.validate_name(var_name):
                    return
                if self.buffer[i+2] != "=":
                    return self.error(self.buffer[i+2], "expected '=' symbol")
                expression = self.buffer[i+3]
                if expression.startswith("$") != expression.endswith("$"):
                    return self.error(expression, "symbol '$' missed - unclosed expression")
                if expression.startswith("$"):
                    value = self.parse_expression(expression[1:-1])
                    if value is None:
                        return
                else:
                    value = self.parse_value(expression)
                self.variables.update({var_name: value})
                for j in range(i, i+4):
                    self.buffer[j] = ""
            elif I == "=":
                if i < 1:
                    return self.error(I, "unexpected '=' symbol")
                if i >= 2 and self.buffer[i-2] == "let":
                    continue
                var_name = self.buffer[i-1]
                if var_name in self.current_dict:
                    return self.error(I, f"{var_name=} already exists in this scope")
                if not self.validate_name(var_name):
                    return
                if i + 1 >= len(self.buffer):
                    return self.error(I, "expected value, but EOL given")
                if re.fullmatch(self.NAME_RE, key:=self.buffer[i+1]):
                    value = self.get_value(key, key)
                else:
                    value = self.parse_value(key)
                if value is None:
                    return
                self.current_dict.update({var_name: value})
            elif I == "}":
                self.dict_stack.pop(-1)
                if not self.dict_stack:
                    self.dump()
                    exit()
                self.current_dict = self.dict_stack[-1]

parser = Parser()

if __name__ == "__main__":
    while True:
        parser.parse_line(input('\t'*(len(parser.dict_stack)-parser.end_dict_flag)))
