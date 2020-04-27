import copy

from .apply_element import apply_diff_element_on_list
from .elementdefinitions_container import ElementDefinitionsContainer
from .helper import fetch_structure_definition, prepend_root


class Slice(ElementDefinitionsContainer):
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

    def __init__(self, snapshot_root, diff_element, slice_type, base_id, api_url):
        diff_element = copy.deepcopy(diff_element)
        self.root_path = diff_element["path"]
        self.root_id = diff_element["id"]
        self.base_id = base_id

        self.api_url = api_url

        self.root_base_elements = fetch_structure_definition(api_url=self.api_url, id_=slice_type)[
            "snapshot"
        ]["element"]
        self.root_base_elements[0] = self.replace_element(
            self.root_base_elements[0],
            snapshot_root,
            keys_to_remove=["condition", "extension", "slicing"],
        )

        self.replace_element_ids_and_paths(self.root_base_elements)

        # Apply the diff element
        apply_diff_element_on_list(self.root_base_elements, diff_element)
        self._snapshot_elements = [self.root_base_elements[0]]

    @property
    def snapshot_elements(self):
        return self._snapshot_elements

    @snapshot_elements.setter
    def snapshot_elements(self, value):
        self._snapshot_elements = value

    def replace_element_ids_and_paths(self, elements):
        # We change ids and paths so that they are coherent with the ones from
        # the snapshot to build
        for element in elements:
            element["id"] = prepend_root(self.root_id, element["id"])
            element["path"] = prepend_root(self.root_path, element["path"])
