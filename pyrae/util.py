from typing import Any, Sequence


def nested_dictionary_set(dictionary: dict,
                          keys: Sequence,
                          value: Any,
                          create_missing: bool = True,
                          update_if_dicts: bool = True):
    """ Set the value of a dictionary traversing it using a sequence of keys.

    :param dictionary: A dictionary.
    :param keys: A list of keys to traverse the dictionary.
    :param value: The value to set to the last key.
    :param create_missing: Creates entries for keys that do not exist in the dictionary.
    :param update_if_dicts: If the last key already exists and its value is a dictionary and the given value is also a
                            dictionary, merges both dictionaries instead of setting the value to the new dictionary.
    :return: The modified dictionary reference.
    """
    d = dictionary
    for key in keys[:-1]:
        if key in d:
            d = d[key]
        elif create_missing:
            d = d.setdefault(key, {})
        else:
            return dictionary
    if keys[-1] in d:
        if isinstance(d[keys[-1]], dict) and isinstance(value, dict) and update_if_dicts:
            d[keys[-1]].update(value)
        else:
            d[keys[-1]] = value
    elif create_missing:
        d[keys[-1]] = value
    return dictionary
