"""Tests for the calculator tool."""

import pytest

from src.tools.calculator import CalculatorTool, safe_eval


class TestSafeEval:
    """Test the safe_eval function."""

    def test_basic_arithmetic(self):
        assert safe_eval("2 + 2") == 4
        assert safe_eval("10 - 3") == 7
        assert safe_eval("5 * 4") == 20
        assert safe_eval("20 / 4") == 5

    def test_complex_expressions(self):
        assert safe_eval("2 + 3 * 4") == 14
        assert safe_eval("(2 + 3) * 4") == 20
        assert safe_eval("10 ** 2") == 100

    def test_functions(self):
        assert safe_eval("sqrt(16)") == 4
        assert safe_eval("abs(-5)") == 5
        assert safe_eval("round(3.7)") == 4

    def test_constants(self):
        import math
        assert safe_eval("pi") == math.pi
        assert safe_eval("e") == math.e

    def test_invalid_expressions(self):
        with pytest.raises(ValueError):
            safe_eval("import os")

        with pytest.raises(ValueError):
            safe_eval("__import__('os')")

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            safe_eval("1/0")


class TestCalculatorTool:
    """Test the CalculatorTool class."""

    @pytest.fixture
    def calculator(self):
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_execute_success(self, calculator):
        result = await calculator.execute(expression="2 + 2")
        assert result.success
        assert "4" in result.data

    @pytest.mark.asyncio
    async def test_execute_no_expression(self, calculator):
        result = await calculator.execute()
        assert not result.success
        assert "No expression" in result.error

    @pytest.mark.asyncio
    async def test_execute_invalid_expression(self, calculator):
        result = await calculator.execute(expression="invalid")
        assert not result.success
