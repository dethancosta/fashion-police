# fashion-police
A static code analyzer that checks the code style of a given Python file against a subset of PEP8.

It checks for the following, with the accompanying code:
- S001: The length of a line should be less than 80 characters
- S002: Indentations should be a multiple of 4 
- S003: Semicolons at the end of lines are unnecessary
- S004: Inline comments should be preceded by at least two spaces
- S005: TODO comments are detected
- S006: There should be no more than 2 blank lines in a row
- S007: There should be no more than 1 space after the 'def' or 'class' keywords
- S008: Class names should be in CamelCase
- S009: Function names should be in snake_case
- S010: Function arguments should be in snake_case
- S011: Variables declared inside functions should be in snake_case
- S012: Default arguments in functions should not be mutable objects

![fashionpolice](https://media.giphy.com/media/0cGzPNCpWWtGk5f1l8/giphy.gif)

If something is caught, a line will be printed to stdout with the path of the file, the line number, and the style code with an appropriate message.

## Instructions
After cloning this repo, navigate to the directory where the code is located, and run `python3 main.py <to-check>`, where `to-check` is any directory or Python file that you want to check the style of.
