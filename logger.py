def color(string: str, color: str) -> str:
    if not color:
        return string
    c = {
        "r": "31",
        "y": "33",
        "g": "32",
    }.get(color[0].lower(), "0")
    return f"\033[{c}m{string}\033[0m"

class Logger:
    def info(self, msg: str, *args, **kwargs):
        print(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        print(color(msg, 'yellow'), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        print(color(msg, "red"), *args, **kwargs)
