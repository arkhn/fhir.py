import copy
import re

from .apply_element import apply_diff_element_on_list
from .composite_attribute import CompositeAttribute
from .errors import GenerationError
from .helper import *


class ChoiceTypeElement(CompositeAttribute):
    """
    Abstraction to represent a group of fhir Elementdefinitions that are constraints
    on a choice type.
    For instance, in a Structuredefinition having Elementdefinitions with ids
        ...
        root.Observation.valueQuantity,
        root.Observation.valueQuantity.id,
        root.Observation.valueQuantity.{...},
        root.Observation.valueCodeableConcept,
        root.Observation.valueCodeableConcept.id,
        root.Observation.valueCodeableConcept.{...},
        ...
    a ChoiceTypeElement will be built for the elements with ids starting
    with root.Observation.valueQuantity and another one for elements with ids starting
    with root.Observation.valueCodeableConcept.
    """

    def __init__(self, snapshot_root, diff_element, choice_root, choice_type):
        diff_element = copy.deepcopy(diff_element)
        self.root_id = diff_element["id"]
        self.choice_root = choice_root
        self.choice_type = choice_type

        self.root_base_elements = fetch_structure_definition(id_=choice_type)["snapshot"]["element"]
        self.root_base_elements[0] = self.replace_element(
            self.root_base_elements[0],
            snapshot_root,
            keys_to_remove=["extension", "slicing"],
            sliceName=self.build_slice_name(choice_root, choice_type),
            new_type=choice_type,
        )
        diff_element["id"] = diff_element["id"].replace(self.root_id, self.choice_type)
        diff_element["path"] = diff_element["path"].replace(self.root_id, self.choice_type)
        apply_diff_element_on_list(self.root_base_elements, diff_element)
        self.definition_elements = [self.root_base_elements[0]]

    def add_diff_element(self, diff_element):
        diff_element["id"] = diff_element["id"].replace(self.root_id, self.choice_type)
        diff_element["path"] = diff_element["path"].replace(self.root_id, self.choice_type)
        super().add_diff_element(diff_element)

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
