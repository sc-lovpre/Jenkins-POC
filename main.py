# This is a sample python code for unit testing POC of jenkins.

def is_even(number: int) -> bool:
    """
    Determines if a number is even.

    Args:
        number (int): The number to check.

    Returns:
        bool: True if the number is even, False otherwise
    """
    return number % 2 == 0


def is_palindrome(s: str) -> bool:
    """
    Checks if a given string is a palindrome.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a palindrome, False otherwise.
    """
    s = s.lower().replace(" ", "")
    return s == s[::-1]


# test comment