from .errors import GenerationError
from .helper import *


def assert_same(base_val, diff_val):
    if isinstance(base_val, str):
        assert base_val.lower() == diff_val.lower()
    else:
        assert base_val == diff_val
    return base_val


def assert_new(base_val, diff_val):
    """ Elements I'm not sure about are treated with this
    function.
    """
    assert base_val is None
    return diff_val


def override_base(base_val, diff_val):
    # add the checks here?
    return diff_val


def override_or_cat_string(base_val, diff_val):
    # sanity check
    assert isinstance(diff_val, str)
    if diff_val.startswith("..."):
        assert isinstance(base_val, str)
        return f"{base_val}{diff_val[3:]}"
    return diff_val


def aggregate(base_val, diff_val):
    if base_val is None:
        return diff_val
    # hope we have lists here
    return base_val + [d for d in diff_val if d not in base_val]


def merge_type(base_val, diff_val):
    # TODO Do we want to check that diff types are valid constraints for
    # at least one type in base?
    return diff_val


def merge_binding(base_val, diff_val):
    # TODO Do we want to check that rule on binding
    # are satisfied?
    return diff_val


def merge_slicing(base_val, diff_val):
    # TODO Not what we want to do
    return diff_val


# Find by name, path
# RULES check min, max minValue[x], maxValue[x], maxLength restrict
key2func = {
    "id": assert_same,
    "path": assert_same,
    "name": assert_same,
    "extension": assert_new,
    "contentReference": override_base,  # Not sure
    "label": override_base,
    "short": override_base,
    "min": override_base,
    "max": override_base,
    "fixed": override_base,
    "pattern": override_base,
    "example": override_base,
    "minValue[x]": override_base,
    "maxValue[x]": override_base,
    "maxLength": override_base,
    "mustSupport": override_base,
    "isSummary": override_base,
    "sliceName": override_base,
    "fixedUri": override_base,
    "fixedCode": override_base,
    "definition": override_or_cat_string,
    "comment": override_or_cat_string,
    "requirements": override_or_cat_string,
    "condition": aggregate,
    "code": aggregate,
    "alias": aggregate,
    "constraint": aggregate,
    "mapping": aggregate,
    "type": merge_type,
    "binding": merge_binding,
    "slicing": merge_slicing,
}


def apply_diff_element_on_list(base_elements, diff_element):
    """ Try to apply the diff element to one element in base_elements.

    Returns:
        - True if modif applied else False
    """
    for ind_el, el in enumerate(base_elements):
        # Double for loop, could be avoided if sure that diff elements
        # are in the same order as snap elements. But I think it's ok.
        if el["id"].lower() == diff_element["id"].lower():
            apply_diff_element(el, diff_element)
            return True
    return False


def apply_diff_element(base_element, diff_element):
    for key_diff, val_diff in diff_element.items():
        try:
            func = key2func[key_diff]
            base_element[key_diff] = func(base_element.get(key_diff), val_diff)
        except KeyError as e:
            print(key_diff, val_diff)
            print(diff_element)
            diff_type = diff_element["type"][0]["code"]
            if key_diff == f"fixed{uppercase_first_letter(diff_type)}":
                base_element[key_diff] = val_diff
            else:
                raise GenerationError(e)