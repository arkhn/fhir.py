import copy
import re

from .apply_element import apply_diff_element_on_list
from .composite_attribute import CompositeAttribute
from .errors import GenerationError
from .helper import *


class ChoiceTypeElement(CompositeAttribute):
    def __init__(self, snapshot_root, diff_element, choice_root, choice_type):
        diff_element = copy.deepcopy(diff_element)
        self.root_id = diff_element["id"]
        self.choice_root = choice_root
        self.choice_type = choice_type
        # TODO clean here
        self.definition_elements = [get_root_element(fetch_structure_definition(id_=choice_type))]
        self.replace_root_element(
            snapshot_root,
            keys_to_remove=["extension", "slicing"],
            sliceName=self.build_slice_name(choice_root, choice_type),
            new_type=choice_type,
        )
        diff_element["id"] = diff_element["id"].replace(self.root_id, self.choice_type)
        diff_element["path"] = diff_element["path"].replace(self.root_id, self.choice_type)
        apply_diff_element_on_list(self.definition_elements, diff_element)

    def add_diff_element(self, diff_element):
        diff_element["id"] = diff_element["id"].replace(self.root_id, self.choice_type)
        diff_element["path"] = diff_element["path"].replace(self.root_id, self.choice_type)
        ok = apply_diff_element_on_list(self.definition_elements, diff_element)
        if not ok:
            self.expand_element(diff_element["id"].rsplit(".", 1)[0])
            ok = apply_diff_element_on_list(self.definition_elements, diff_element)
            if not ok:
                raise GenerationError(f"Could not apply differential element: {diff_element}")

    def normalize_ids_and_paths(self):
        for element in self.definition_elements:
            element["id"] = self.build_multitype_id(self.choice_root, element["id"])
            element["path"] = self.build_multitype_path(self.choice_root, element["path"])

    @staticmethod
    def build_slice_name(root, type_):
        root_attr = re.search(r"\.([a-zA-Z]+)\[x\]$", root).group(1)
        return f"{root_attr}{uppercase_first_letter(type_)}"

    @staticmethod
    def build_multitype_id(root, val):
        multitype_attr = re.search(r"\.([a-zA-Z]+)\[x\]$", root).group(1)
        return f"{root}:{multitype_attr}{uppercase_first_letter(val)}"

    @staticmethod
    def build_multitype_path(root, val):
        multitype_attr = re.search(r"\.([a-zA-Z]+)\[x\]$", root).group(1)
        end = val.split(".", 1)
        if len(end) == 1:
            return root
        else:
            return f"{root}.{end[1]}"
