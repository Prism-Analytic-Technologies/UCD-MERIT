from datetime import datetime
import json

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

############################################################################
# title case enum
############################################################################
def pretty_print_enum(enum_str):
    if not enum_str:
        return ""
    return enum_str.replace("_", " ").title()

############################################################################
# title case array of enums
############################################################################
def pretty_print_enums(enum_strs):
    return list(map(pretty_print_enum, enum_strs))

############################################################################
# get date from iso string
############################################################################
def get_date_from_str(date_str):
    return datetime.strptime(date_str, DATE_FORMAT)

############################################################################
# get year string from date string
############################################################################
def get_year(date_str):
    date = get_date_from_str(date_str)
    if not date:
        return 0
    return date.year

############################################################################
# find object in array based on key match
############################################################################
def get_by_key_value(array, name, key="name"):
    matches = list(filter(lambda elem: elem[key] == name, array))
    return matches[0] if len(matches) > 0 else None

############################################################################
# see if any of a list is contained within a string
############################################################################
def list_contains(string, a_list):
    return any(filter(lambda value: contains_by_case(string, value), a_list))

############################################################
# Map value by keywords
############################################################
def map_by_keywords(string, value_keyword_map, default_value=None):
    values = []

    for entry in value_keyword_map:
        # see if any of the keywords for this value match
        _matches = contains(string, entry.get("keywords"))
        if _matches:
            values.append(entry["value"])

    # return default value if no other matches
    if len(values) == 0 and default_value:
        return [default_value]

    return values

############################################################
# Contains that respects acronyms (e.g. PRO)
############################################################
def case_aware_contains(string, word):
    if word == word.lower():
        return word in string.lower()
    return word in string

def contains(string, phrases):
    return list(filter(lambda phrase: case_aware_contains(string, phrase), phrases))
