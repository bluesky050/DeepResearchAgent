"""Sample Python file for testing code review system."""

def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b


def process_data(data):
    """Process data with potential issues for review."""
    # Security issue: hardcoded password
    password = "admin123"

    # Performance issue: inefficient loop
    result = []
    for i in range(len(data)):
        for j in range(len(data)):
            if data[i] == data[j]:
                result.append(data[i])

    # Code quality issue: long line
    very_long_variable_name_that_exceeds_recommended_line_length = "This is a very long string that should trigger a line length warning from linters"

    return result


class DataProcessor:
    """Data processor class."""

    def __init__(self):
        self.data = []

    def add_item(self, item):
        """Add item to data."""
        self.data.append(item)
