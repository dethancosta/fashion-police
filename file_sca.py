import ast
import os.path
import re
from typing import List, Callable, Tuple


class AstVisitor(ast.NodeVisitor):
    def __init__(self):
        self.vars: dict = {}
        self.arguments: dict = {}
        self.mut_defaults: set = set()

    def visit_FunctionDef(self, node):
        for arg in node.args.args:
            self.arguments[node.lineno] = arg.arg
        for arg in node.args.defaults:
            if not isinstance(arg, ast.Constant):
                self.mut_defaults.add(arg.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        for arg in node.args.args:
            self.arguments[node.lineno] = arg.arg
        for arg in node.args.defaults:
            if not isinstance(arg, ast.Constant):
                self.mut_defaults.add(arg.lineno)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.vars[node.lineno] = node.id
        self.generic_visit(node)


class StyleChecker:
    def __init__(self, check_fn: Callable[[str], bool], code: int, msg: str):
        self.check_fn = check_fn
        self.code = code
        self.msg = msg

    def check(self, line: str) -> bool:
        return self.check_fn(line)

    @classmethod
    def length_checker(cls):
        return StyleChecker(lambda x: len(x) <= 79, 1, 'Too long')

    @classmethod
    def indent_checker(cls):
        return StyleChecker(lambda x: (len(x) - len(x.lstrip())) % 4 == 0, 2, 'Indentation is not a multiple of four')

    @classmethod
    def semicolon_checker(cls):
        def check(line: str) -> bool:
            line = line.split('#')[0]
            line = line.rstrip()
            if len(line) == 0:
                return True
            return not (line[-1] == ';' and
                        (line.lstrip()[0] != '#' or
                         len(line.lstrip()) > 3 and line[:3] != "'''" and line[:3] != '"""'))
        return StyleChecker(check, 3, 'Unnecessary semicolon')

    @classmethod
    def comment_spaces_checker(cls):
        def check(line: str) -> bool:
            sides = line.split('#', 2)
            if len(sides) < 2:
                return True
            left_side = sides[0]
            left_side = left_side.lstrip()
            if len(left_side) == 0:
                return True
            return len(left_side) >= 2 and len(left_side) - len(left_side.rstrip()) >= 2
        return StyleChecker(check, 4, 'At least two spaces required before inline comment')

    @classmethod
    def todo_checker(cls):
        def check(line: str) -> bool:
            idx = line.find('#')
            if idx == -1:
                return True
            comment = line[idx:].lower()
            return not comment.find('todo') > -1
        return StyleChecker(check, 5, 'TODO found')

    @classmethod
    def blank_lines_checker(cls, blank_fn: Callable[[], int]):
        class BlankLines(StyleChecker):
            def __init__(self):
                def check(line: str) -> bool:
                    length = len(line.strip())
                    if length == 0:
                        return True
                    return blank_fn() <= 2
                super().__init__(check, 6, 'More than two blank lines found before this line')
        return BlankLines()

    @classmethod
    def def_spaces_checker(cls):
        def check(line: str) -> bool:
            regex = re.compile('def {2,}[a-zA-Z_]')
            return len(regex.findall(line)) == 0
        return StyleChecker(check, 7, 'Too many spaces after \'def\'')

    @classmethod
    def class_spaces_checker(cls):
        def check(line: str) -> bool:
            regex = re.compile('class {2,}[a-zA-Z_]')
            return len(regex.findall(line)) == 0
        return StyleChecker(check, 7, 'Too many spaces after \'class\'')

    @classmethod
    def camelcase_checker(cls):
        class Camelcase(StyleChecker):
            def __init__(self):
                self.msg: str = ''

                def check(line: str) -> bool:
                    class_match = re.search('class \\w*\\s*:', line)
                    if not class_match:
                        return True
                    result = re.match('class [A-Z]+([a-z0-9]|([A-Z0-9][a-z0-9]+))*([A-Z])?\\s*:',
                                    class_match.group())
                    if result is None:
                        self.msg = f'Class name \'{class_match.group()[6:-1].strip()}\' should use CamelCase'
                        return False
                    return True

                super().__init__(check, 8, self.msg)
        return Camelcase()

    @classmethod
    def snakecase_checker(cls):
        class Snakecase(StyleChecker):
            def __init__(self):
                self.msg: str = ''

                def check(line: str) -> bool:
                    fn_match = re.search('def \\w*\\s*', line)
                    if not fn_match:
                        return True
                    result = re.match('def ([a-z_]+(_[a-zA-Z]+)*|__[a-z]+(_[a-zA-Z]+)*__)', fn_match.group())
                    if result is None:
                        self.msg = f'Function name \'{fn_match.group()[4:-1].strip()}\' should use snake_case'
                        return False
                    return True

                super().__init__(check, 9, self.msg)
        return Snakecase()


def is_snakecase(value: str) -> bool:
    return re.match('([a-z]+(_[a-zA-Z]+)*|__[a-z]+(_[a-zA-Z]+)*__)', value) is not None


def is_camelcase(value: str) -> bool:
    return re.match('[A-Z]+([a-z0-9]|([A-Z0-9][a-z0-9]+))*([A-Z])?', value) is not None

class FileSCA:
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError(f'{filename} does not exist')
        if not os.path.isfile(filename):
            raise Exception(f'{filename} is not a file')

        self.blank_count = 0
        self.file_name = filename
        # self.in_multiline_comment = False
        self.errors: List[Tuple[int, str]] = []
        self.checkers: List[StyleChecker] = [
            StyleChecker.length_checker(),
            StyleChecker.indent_checker(),
            StyleChecker.semicolon_checker(),
            StyleChecker.comment_spaces_checker(),
            StyleChecker.todo_checker(),
            StyleChecker.blank_lines_checker(lambda: self.blank_count),
            StyleChecker.def_spaces_checker(),
            StyleChecker.class_spaces_checker(),
            StyleChecker.camelcase_checker(),
            StyleChecker.snakecase_checker()
        ]

    def analyze(self):
        line_count = 0
        with open(self.file_name) as f:
            lines = [line for line in f]
            f.seek(0)
            tree = ast.parse(f.read())

            ast_visitor = AstVisitor()
            ast_visitor.visit(tree)
            for line_num, var in ast_visitor.vars.items():
                if not is_snakecase(var):
                    msg = f'{self.file_name}: Line {line_num}: S011 Variable \'{var}\' in function should be snake_case'
                    self.errors.append((line_num, msg))
            for line_num, arg in ast_visitor.arguments.items():
                if not is_snakecase(arg):
                    msg = f'{self.file_name}: Line {line_num}: S010 Argument name \'{arg}\' should be snake_case'
                    self.errors.append((line_num, msg))
            for line_num in ast_visitor.mut_defaults:
                msg = f'{self.file_name}: Line {line_num}: S012 Default argument value is mutable'
                self.errors.append((line_num, msg))

            for line in lines:
                line_count += 1
                if len(line.strip()) == 0:
                    self.blank_count += 1
                    continue
                for checker in self.checkers:
                    if not checker.check(line):
                        msg = ': '.join([self.file_name, f'Line {line_count}', f"S{checker.code:03d} " + checker.msg])
                        self.errors.append((line_count, msg))

                self.blank_count = 0
        self.errors.sort(key=lambda x: x[0])

