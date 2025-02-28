from .tree_calc import CalculateTree
from ...base import BaseParser
from lark import Lark, Tree
from pathlib import Path
from .chord import Chord
from rich import print

__all__ = ("ListParser", "Pat")

class ParserError(Exception):
    pass

grammar_path = Path(__file__).parent
grammar = grammar_path / "sardine.lark"


class ListParser(BaseParser):
    def __init__(
        self,
        parser_type: str = "sardine",
        debug: bool = False,
    ):

        """
        ListParser is the main interface to the basic patterning langauge used in a very
        basic Sardine setup. ListParser is a programming language capable of handling 
        notes, names, samples, OSC addresses, etc... It can be used for some basic
        patterning.
        """

        super().__init__()
        self.debug = debug
        self.parser_type = parser_type

    def __repr__(self) -> str:
        return f"<{type(self).__name__} debug={self.debug} type={self.parser_type!r}>"

    def setup(self):
        parsers = {
            "sardine": {
                "raw": Lark.open(
                    grammar,
                    rel_to=__file__,
                    parser="lalr",
                    start="start",
                    cache=True,
                    lexer="contextual",
                ),
                "full": Lark.open(
                    grammar,
                    rel_to=__file__,
                    parser="lalr",
                    start="start",
                    cache=True,
                    lexer="contextual",
                    transformer=CalculateTree(
                        self.env.clock, self.env.iterators, self.env.variables
                    ),
                ),
            },
        }

        try:
            self._result_parser = parsers[self.parser_type]["full"]
            self._printing_parser = parsers[self.parser_type]["raw"]
        except KeyError:
            ParserError(f"Invalid Parser grammar, {self.parser_type} is not a grammar.")

    def __flatten_result(self, pat):
        """Flatten a nested list, for usage after parsing a pattern. Will flatten deeply
        nested lists and return a one dimensional array.

        Args:
            pat (list): A potentially nested list

        Returns:
            list: A flat list (one-dimensional)
        """
        from collections.abc import Iterable

        for x in pat:
            if isinstance(x, Iterable) and not isinstance(x, (str, bytes, Chord)):
                yield from self._flatten_result(x)
            else:
                yield x

    def _flatten_result(self, pat):
        result = list(self.__flatten_result(pat))
        return result

    def pretty_print(self, expression: str):
        """Pretty print an expression coming from the parser. Works for any
        parser and will print three things on stdout if successful:
        - the expression itself
        - the syntax tree generated by the parser for this expression
        - the result of parsing that syntax tree

        Args:
            expression (str): An expression to pretty print
        """
        print(f"EXPR: {expression}")
        print(Tree.pretty(self._printing_parser.parse(expression)))
        result = self._result_parser.parse(expression)
        print(f"RESULT: {result}")
        print(f"USER RESULT: {self._flatten_result(result)}")

    def print_tree_only(self, expression: str):
        """Print the syntax tree using Lark.Tree

        Args:
            expression (str): An expression to print
        """
        print(Tree.pretty(self._printing_parser.parse(expression)))

    def parse(self, *args):
        """Main method to parse a pattern. Parses 'pattern' and returns
        a flattened list to index on to extract individual values. Note
        that this function is temporary. Support for stacked values is
        planned.

        Args:
            pattern (str): A pattern to parse

        Raises:
            ParserError: Raised if the pattern is invalid

        Returns:
            list: The parsed pattern as a list of values
        """
        pattern = args[0]
        final_pattern = []
        try:
            final_pattern = self._result_parser.parse(pattern)
        except Exception as e:
            raise ParserError(f"Non valid token: {pattern}: {e}")

        if self.debug:
            print(f"Pat: {self._flatten_result(final_pattern)}")
        return self._flatten_result(final_pattern)

    def _parse_debug(self, pattern: str):
        """Parses a whole pattern in debug mode. 'Debug mode' refers to
        a mode where both the initial expression, the syntax tree and the
        pattern result are printed directly on stdout. This allows to study
        the construction of a result by looking at the syntax tree.

        Args:
            pattern (str): A pattern to be parse.
        """
        try:
            self.pretty_print(expression=pattern)
        except Exception as e:
            import traceback

            print(f"Error: {e}: {traceback.format_exc()}")


def Pat(pattern: str, i: int = 0):
    """Generates a pattern

    Args:
        pattern (str): A pattern to be parsed
        i (int, optional): Index for iterators. Defaults to 0.

    Returns:
        int: The ith element from the resulting pattern
    """
    parser = ListParser(clock=c, parser_type="sardine")
    result = parser.parse(pattern)
    return result[i % len(result)]
