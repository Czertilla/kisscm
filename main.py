from typing import Callable
from zipfile import ZipFile, ZipInfo
from time import time, localtime
import sys
from logger import Logger, color


logger = Logger()
ROOT_PATH = "root:"


class Emulator (ZipFile):
    curr_path: str
    COMMANDS: dict

    def __init__(self, target: str, *args, **kwargs) -> None:
        self.COMMANDS = {
            "ls": self.list,
            "cd": self.change_dir,
            "tail": self.tail,
            "touch": self.touch,
            "mv": self.move
        }
        super().__init__(target, *args, **kwargs)
        self.curr_path = ""

    def polling(self):
        command = ""
        while command != "exit":
            command = input(
                ROOT_PATH + ("/" if not self.curr_path else self.curr_path) + "> ")
            command_line = command.split()
            if not command_line or command == "exit":
                continue
            self.COMMANDS.get(
                command_line.pop(0), 
                self.unknow_command
            )(*command_line)
            

    def cut_root(self, path: str = None) -> str | None:
        if path is None:
            target = self.curr_path
        else:
            target = path
        if target and target[0] == "/":
            target = target[1:]
        if target and target[-1] == '/':
            target = target[:-1]
        if path is None:
            self.curr_path = target
        else:
            return target

    @classmethod
    def unknow_command(self, *args) -> None:
        logger.error("Unknow command")

    @classmethod
    def invalid_command(self, *args) -> None:
        logger.error("Invalid command")

    @classmethod
    def invalid_path(self, *args) -> None:
        logger.error("The path does not exist")

    def remove(self, filepath: ZipInfo) -> None:
        self.filelist.remove(file:=self.NameToInfo.pop(filepath.filename))
        del file

    def get_path(self, target_path: str) -> str:
        target_path = target_path[:-1:] if target_path[-1] == "/" else target_path
        if c:=target_path.count('..'):
            path = "/".join(self.curr_path.split('/')[:-c])
            target_path = "/".join(filter(lambda p: p != "..", target_path.split('/')))
        else:
            path = self.curr_path
        if "root:" in target_path:
            path = target_path[len("root:"):]
        else:
            path += "/" + target_path
        return self.cut_root(path)

    def list(self, *args) -> None:
        self.cut_root()
        for file in self.filelist:
            if self.curr_path in file.filename:
                file_names = file.filename[len(self.curr_path):].split("/")
                file_names = list(filter(None, file_names))
                if len(file_names) > 1 or not file_names:
                    continue
                logger.warning(file_names[0])

    def change_dir(self, *args) -> None:
        try:
            target_path = str(args[0])
        except IndexError:
            self.curr_path = ''
            return
        except:
            return self.invalid_command()
        
        path = self.get_path(target_path)

        if any(i:=iter(path + '/' == file.filename for file in self.filelist)):
            self.curr_path = "/" + path
            return
        if not path:
            self.curr_path = ""
            return
        return self.invalid_path()

    def tail(self, *args) -> None:
        try:
            target_path = str(args[-1])
        except:
            return self.invalid_command()
        if "-n" in args:
            try:
                n = int(args[args.index("-n")+1])
            except Exception as e:
                return self.invalid_command(e)
        else:
            n = 10

        path = self.get_path(target_path)

        for file in self.filelist:
            if path == file.filename:
                with self.open(path, 'r') as file:
                    n = min(len(lines:= file.readlines()), n)
                    for line in lines[-n:]:
                        print(line.decode('utf8').strip())
                break
        else:
            logger.error("Can`t open this file")

    def touch(self, *args) -> None:
        try:
            target_path = str(args[0])
        except:
            return self.invalid_command()
        
        path = self.get_path(target_path)
        
        s = 0
        for i in range(path.count('/')+1):
            s = path.find('/', s) + 1
            ipath = path[:s] if s else path
            if ipath not in (self.namelist()):
                self.writestr(ipath, "")
        else:
            self.filelist[self.namelist().index(path)].date_time = localtime(time())

    def move(self, *args) -> None:
        try:
            target_path = str(args[-2])
            destin_path = str(args[-1])
        except:
            return self.invalid_command()
        
        n, u, b = "-n" in args, "-u" in args, "-b" in args
        filt: Callable[[str], list[ZipInfo]] = lambda path: list(
            filter(lambda x: x.filename.startswith(path), self.filelist))
        target_path = "root:"+self.curr_path+'/' if target_path == "." else target_path
        destin_path = "root:"+self.curr_path+'/' if destin_path == "." else destin_path
        if target_path.endswith('/'):
            if not destin_path.endswith('/'):
                self.invalid_command()
            destin_path = self.get_path(destin_path)
            target_path = self.get_path(target_path)
            target_files = filt(target_path)
            destin_files = filt(destin_path)
            for file in target_files:
                name = file.filename.replace(target_path, "")
                if name == "/": continue
                if n and (l:=list(
                            filter(
                                lambda x: x.filename.replace(
                                    destin_path, "") == name, destin_files)
                        )) or u and l[0].date_time > file.date_time:
                    continue
                # with self.open(file, 'r') as buffer:
                #     self.writestr(destin_path+"/"+name, buffer.read().decode())
                self.touch("root:"+destin_path+name)
                idestin_files = filt(destin_path+name)
                if idestin_files:
                    self.remove(idestin_files[0])
                self.writestr(destin_path+name, self.read(file.filename))
                if not b:
                    self.remove(file)
        else:
            target_path = self.get_path(target_path)
            destin_path = self.get_path(destin_path) + (
                "/" + target_path.split('/')[-1] if destin_path.endswith('/') else '')
            target_file = filt(target_path)[0]
            if n and destin_path in self.namelist() or u and list(
                filter(
                    lambda x: x.filename == destin_path and x.date_time > target_file.date_time, 
                    self.filelist
                    )
                ):
                return
            self.touch("root:"+destin_path+name)
            destin_files = filt(destin_path)
            if destin_files:
                self.remove(destin_files[0])
            self.writestr(destin_path, self.read(target_file.filename))
            if not b:
                self.remove(target_file)

                    


if __name__ == '__main__':
    try:
        target = sys.argv[1]
    except IndexError:
        logger.error(f"no args given")
        exit(1)
    with Emulator(target, mode="a") as emulator:
        emulator.polling()
        logger.info(emulator.namelist())