"""Calculator tool for mathematical operations."""

import ast
import math
import operator
from typing import Any

from .base import Tool, ToolResult, ToolSchema, tool_registry
from .schemas import CALCULATOR_SCHEMA


class SafeEvaluator(ast.NodeVisitor):
    """
    Safe mathematical expression evaluator using AST.
    Prevents code injection by only allowing specific operations.
    """

    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "floor": math.floor,
        "ceil": math.ceil,
        "pi": math.pi,
        "e": math.e,
    }

    def visit_BinOp(self, node: ast.BinOp) -> float:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type not in self.ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return self.ALLOWED_OPERATORS[op_type](left, right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type not in self.ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return self.ALLOWED_OPERATORS[op_type](operand)

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")

    def visit_Name(self, node: ast.Name) -> float:
        name = node.id.lower()
        if name in self.ALLOWED_FUNCTIONS:
            value = self.ALLOWED_FUNCTIONS[name]
            if isinstance(value, (int, float)):
                return value
        raise ValueError(f"Unknown variable: {node.id}")

    def visit_Call(self, node: ast.Call) -> float:
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")

        func_name = node.func.id.lower()
        if func_name not in self.ALLOWED_FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name}")

        func = self.ALLOWED_FUNCTIONS[func_name]
        if not callable(func):
            raise ValueError(f"{func_name} is not a function")

        args = [self.visit(arg) for arg in node.args]
        return func(*args)

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def generic_visit(self, node: ast.AST) -> None:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def safe_eval(expression: str) -> float:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression string

    Returns:
        Evaluated result

    Raises:
        ValueError: If expression is invalid or contains unsupported operations
    """
    try:
        tree = ast.parse(expression, mode="eval")
        evaluator = SafeEvaluator()
        return evaluator.visit(tree)
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")


class CalculatorTool(Tool):
    """Tool for performing mathematical calculations."""

    name = "calculator"
    description = "Perform mathematical calculations. Supports basic arithmetic (+, -, *, /, **, %), and functions like sqrt, sin, cos, tan, log, exp, floor, ceil. Also supports constants pi and e."

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=CALCULATOR_SCHEMA,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        expression = kwargs.get("expression", "")

        if not expression:
            return ToolResult(success=False, error="No expression provided")

        try:
            result = safe_eval(expression)
            # Format result nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return ToolResult(
                success=True,
                data=f"{expression} = {result}",
            )
        except ValueError as e:
            return ToolResult(success=False, error=str(e))
        except ZeroDivisionError:
            return ToolResult(success=False, error="Division by zero")
        except Exception as e:
            return ToolResult(success=False, error=f"Calculation error: {e}")


# Register the tool
tool_registry.register(CalculatorTool())
