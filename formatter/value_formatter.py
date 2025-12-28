import numbers

class ValueFormatter:
    @staticmethod
    def format(value):
        # Numeric types: ints as-is, floats (including numpy types) to 3 decimals
        if isinstance(value, numbers.Number):
            float_value = float(value)
            if float_value.is_integer():
                return str(int(float_value))
            return f"{float_value:.3f}"
        # Sequences: format each element recursively
        if isinstance(value, (list, tuple)):
            inner_values = ", ".join(ValueFormatter.format(element) for element in value)
            return f"({inner_values})"
        return str(value)
