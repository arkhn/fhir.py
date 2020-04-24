import copy

from .apply_element import apply_diff_element_on_list
from .composite_attribute import CompositeAttribute
from .errors import GenerationError
from .helper import *


class Slice(CompositeAttribute):
    """
    Abstraction to represent a group of fhir Elementdefinitions that are
    part of a slice.
    For instance, in a Structuredefinition having Elementdefinitions with ids
        ...
        Observation.code.coding
        Observation.code.coding:BodyWeightCode
        Observation.code.coding:BodyWeightCode.system
        Observation.code.coding:BodyWeightCode.code
        ...
    a Slice will be built for the elements with ids starting with
    Observation.code.coding:BodyWeightCode.
    """

    def __init__(self, snapshot_root, diff_el, slice_type, base_id):
        diff_el = copy.deepcopy(diff_el)
        self.root_path = diff_el["path"]
        self.root_id = diff_el["id"]
        self.base_id = base_id

        self.root_base_elements = fetch_structure_definition(id_=slice_type)["snapshot"]["element"]
        self.root_base_elements[0] = self.replace_element(
            self.root_base_elements[0],
            snapshot_root,
            keys_to_remove=["condition", "extension", "slicing"],
        )

        self.replace_element_ids_and_paths(self.root_base_elements)

        # Apply the diff element
        apply_diff_element_on_list(self.root_base_elements, diff_el)
        self.definition_elements = [self.root_base_elements[0]]

    def replace_element_ids_and_paths(self, elements):
        # We change ids and paths so that they are coherent with the ones from
        # the snapshot to build
        for element in elements:
            element["id"] = prepend_root(self.root_id, element["id"])
            element["path"] = prepend_root(self.root_path, element["path"])
