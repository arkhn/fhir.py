import copy

from .apply_element import apply_diff_element_on_list
from .composite_attribute import CompositeAttribute
from .errors import GenerationError
from .helper import *


class Slice(CompositeAttribute):
    def __init__(self, snapshot_root, diff_el, slice_type, base_id):
        diff_el = copy.deepcopy(diff_el)
        self.root_path = diff_el["path"]
        self.root_id = diff_el["id"]
        self.base_id = base_id
        self.definition_elements = fetch_structure_definition(id_=slice_type)["snapshot"]["element"]
        self.replace_root_element(
            snapshot_root, keys_to_remove=["condition", "extension", "slicing"],
        )
        # We change ids and paths so that they are coherent with the ones from
        # the snapshot to build
        for element in self.definition_elements:
            element["id"] = prepend_root(self.root_id, element["id"])
            element["path"] = prepend_root(self.root_path, element["path"])
        # Apply the diff element
        apply_diff_element_on_list(self.definition_elements, diff_el)

    def add_diff_element(self, diff_element):
        ok = apply_diff_element_on_list(self.definition_elements, diff_element)
        if not ok:
            self.expand_element(diff_element["id"].rsplit(".", 1)[0])
            ok = apply_diff_element_on_list(self.definition_elements, diff_element)
            if not ok:
                raise GenerationError(f"Could not apply differential element: {diff_element}")
