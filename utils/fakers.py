'''
Functions for create fake test data
'''
import random
import string


def get_random_fake_line(filename):
    '''
    Function to get one random line from a file
    All data in the file must be written on a new line

    :param filename: the name of the file from which to get the line
    '''
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.read() # Read full file
        data = lines.split("\n") # Convert to list
        result = random.choice(data) # Get random line
    return result


def generate_fake_phone_number():
    '''
    Function to generate fake russian phone number
    '''
    result = "+7"
    for i in range(10):
        result += str(random.randint(0, 9))
    return result


def generate_fake_email(length=9):
    '''
    :param length: number of characters before @mail, default is 9
    '''
    result = ""

    # Form a list with all English symbols and numbers
    all_symbols = string.ascii_letters + string.digits

    # Generate random symbols
    result = "".join(random.choice(all_symbols) for _ in range(length))

    # Add @gmail.com to result
    result += "@gmail.com"

    return result
