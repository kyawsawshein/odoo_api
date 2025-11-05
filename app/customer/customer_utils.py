import re

NRC_REGEX = r"^(\d{1,2})/(.+)(\(|\[)(.+)(\)|\])(\d{6})"

ENG_REGEX = r"^[A-Za-z0-9]+$"

number_list = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉']

class NumberValidationError(Exception):
    ...

def number_to_eng(number_str: str) -> str:
    if not number_str.isnumeric():
        raise NumberValidationError(f"{number_str} is not numeric")
    return "".join(str(number_list.index(num)) if num in number_list else num for num in number_str)

def number_to_mm(number_str: str) -> str:
    if not number_str.isnumeric():
        raise NumberValidationError(f"{number_str} is not numeric")
    return "".join(num if num in number_list else number_list[int(num)] for num in number_str)

def is_eng(input_str: str) -> bool:
    return bool(re.match(ENG_REGEX, input_str))
