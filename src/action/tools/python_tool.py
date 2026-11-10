"""A deliberately small, side-effect-free Python expression evaluator."""

import ast
import math
import operator

from src.action.action_result import ActionResult
from src.action.tools.base_tool import BaseTool


class PythonTool(BaseTool):
    """Evaluate one Python expression without imports, statements, or I/O."""

    MAX_SOURCE_LENGTH = 2_000
    MAX_NODES = 128
    MAX_OUTPUT_LENGTH = 4_000

    _BINARY = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg, ast.Not: operator.not_}
    _COMPARE = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }
    _FUNCTIONS = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "round": round,
        "len": len,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
    }
    _CONSTANTS = {"pi": math.pi, "e": math.e, "tau": math.tau}

    @property
    def name(self):
        return "python"

    def execute(self, command: str):
        source = str(command or "").strip()
        for prefix in ("파이썬으로", "파이썬", "python으로", "python", "코드 실행", "실행해줘"):
            if source.casefold().startswith(prefix.casefold()):
                source = source[len(prefix):].lstrip(" \t:：,，")
                break
        for suffix in ("실행해줘", "실행해", "계산해줘"):
            if source.casefold().endswith(suffix.casefold()):
                source = source[:-len(suffix)].rstrip(" \t:：,，")
                break
        if source.startswith("```") and source.endswith("```"):
            source = source.strip("`").strip()
            if source.lower().startswith("python"):
                source = source[6:].strip()
        if not source:
            return ActionResult(success=False, output="실행할 파이썬 표현식을 입력해 줘.")
        if len(source) > self.MAX_SOURCE_LENGTH:
            return ActionResult(success=False, output="표현식이 너무 길어. (최대 2,000자)")

        try:
            tree = ast.parse(source, mode="eval")
            if sum(1 for _ in ast.walk(tree)) > self.MAX_NODES:
                raise ValueError("표현식이 너무 복잡해.")
            result = self._evaluate(tree.body)
            rendered = repr(result)
            if len(rendered) > self.MAX_OUTPUT_LENGTH:
                raise ValueError("결과가 너무 커서 표시하지 않았어.")
            return ActionResult(success=True, output=rendered)
        except (
            SyntaxError,
            ValueError,
            TypeError,
            ZeroDivisionError,
            OverflowError,
            RecursionError,
        ) as error:
            return ActionResult(success=False, output=f"안전한 표현식으로 실행할 수 없어: {error}")

    def _evaluate(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str, bool, type(None))):
            return node.value
        if isinstance(node, ast.Name) and node.id in self._CONSTANTS:
            return self._CONSTANTS[node.id]
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            values = [self._evaluate(item) for item in node.elts]
            if isinstance(node, ast.List):
                return values
            if isinstance(node, ast.Tuple):
                return tuple(values)
            return set(values)
        if isinstance(node, ast.Dict):
            return {self._evaluate(key): self._evaluate(value) for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._UNARY:
            return self._bounded(self._UNARY[type(node.op)](self._evaluate(node.operand)))
        if isinstance(node, ast.BinOp) and type(node.op) in self._BINARY:
            left, right = self._evaluate(node.left), self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)) and abs(right) > 1_000:
                raise ValueError("거듭제곱 지수는 절댓값 1,000 이하만 허용해.")
            if isinstance(node.op, ast.Mult):
                if isinstance(right, int) and isinstance(left, (str, list, tuple)):
                    repetitions, sequence = right, left
                elif isinstance(left, int) and isinstance(right, (str, list, tuple)):
                    repetitions, sequence = left, right
                else:
                    repetitions, sequence = 0, ()
                if len(sequence) * max(0, repetitions) > 100_000:
                    raise ValueError("반복 결과가 너무 커.")
            return self._bounded(self._BINARY[type(node.op)](left, right))
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = None
                for value in node.values:
                    result = self._evaluate(value)
                    if not result:
                        return result
                return result
            result = None
            for value in node.values:
                result = self._evaluate(value)
                if result:
                    return result
            return result
        if isinstance(node, ast.Compare):
            left = self._evaluate(node.left)
            for operation, comparator in zip(node.ops, node.comparators):
                if type(operation) not in self._COMPARE:
                    raise ValueError("지원하지 않는 비교 연산자야.")
                right = self._evaluate(comparator)
                if not self._COMPARE[type(operation)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self._evaluate(node.body if self._evaluate(node.test) else node.orelse)
        if isinstance(node, ast.Subscript):
            value, index = self._evaluate(node.value), self._evaluate(node.slice)
            if not isinstance(value, (list, tuple, str, dict)) or not isinstance(index, (int, str, slice)):
                raise ValueError("허용된 자료형의 인덱싱만 지원해.")
            return value[index]
        if isinstance(node, ast.Slice):
            return slice(
                self._evaluate(node.lower) if node.lower else None,
                self._evaluate(node.upper) if node.upper else None,
                self._evaluate(node.step) if node.step else None,
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in self._FUNCTIONS:
            if node.keywords:
                raise ValueError("키워드 인수는 지원하지 않아.")
            return self._bounded(self._FUNCTIONS[node.func.id](*(self._evaluate(arg) for arg in node.args)))
        raise ValueError("수식, 기본 자료형, 그리고 허용된 수학 함수만 지원해. import·파일·네트워크·명령 실행은 막혀 있어.")

    @staticmethod
    def _bounded(value):
        if isinstance(value, int) and value.bit_length() > 16_384:
            raise ValueError("정수 결과가 너무 커.")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("유한한 숫자 결과만 허용해.")
        if isinstance(value, (str, list, tuple, dict, set)) and len(value) > 100_000:
            raise ValueError("결과가 너무 커.")
        return value
