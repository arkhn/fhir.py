import copy
import json

from .apply_element import apply_diff_element_on_list
from .elementdefinitions_container import ElementDefinitionsContainer
from .helper import (
    fetch_structure_definition,
    get_root_element,
    prepend_root,
    uppercase_first_letter,
)
from .choice_type_element import ChoiceTypeElement
from .errors import GenerationError
from .slice import Slice


# This is a fhir containing all the possible case where we can have a choice element
with open("fhir_bundles/choice-elements.json", "r") as fp:
    all_choice_elements = json.load(fp)


class SnapshotGenerator(ElementDefinitionsContainer):
    def __init__(self, api_url):
        self.api_url = api_url

        self.slices = {}
        self.choice_type_elements = {}
        self._snapshot_elements = None

    @property
    def snapshot_elements(self):
        return self._snapshot_elements

    @snapshot_elements.setter
    def snapshot_elements(self, value):
        self._snapshot_elements = value

    def reset(self):
        self.slices = {}
        self.choice_type_elements = {}
        self.snapshot_elements = None

    def augment_with_snapshot(self, profile):
        self.reset()

        profile_diff = profile["differential"]
        base_definition = fetch_structure_definition(
            api_url=self.api_url, url=profile["baseDefinition"]
        )

        self.snapshot_elements = copy.deepcopy(base_definition["snapshot"]["element"])

        for diff_element in profile_diff["element"]:
            self.add_diff_element(diff_element)

        self.augment_with_slices()
        self.augment_with_choice_elements()

        profile["snapshot"] = {"element": self.snapshot_elements}
        return profile

    def add_diff_element(self, diff_element):
        el_present = apply_diff_element_on_list(self.snapshot_elements, diff_element)
        if not el_present:
            # TODO better check to be sure it's an extension
            if "sliceName" in diff_element and diff_element["path"].split(".")[-1] == "extension":
                self.handle_extension_slice(diff_element)

            elif "sliceName" in diff_element:
                self.create_new_slice(diff_element)

            elif ":" in diff_element["id"]:  # TODO better check to be sure it's to add in a Slice
                self.add_to_existing_slice(diff_element)

            elif self.is_renamed_choice_element(
                diff_element["id"]
            ):  # TODO can we have a non renamed element which is choice element?
                # TODO can I use the evaluation in the if?
                choice_root, choice_type = self.is_renamed_choice_element(diff_element["id"])
                self.create_new_choice_element(diff_element, choice_root, choice_type)

            elif any(
                diff_element["id"].startswith(choice_elem_root)
                for choice_elem_root in self.choice_type_elements
            ):
                self.add_to_existing_choice_element(diff_element)

            else:
                id_to_expand = diff_element["id"].rsplit(".", 1)[0]
                expanded = self.expand_element(id_to_expand)
                if not expanded:
                    raise GenerationError(f"Could not expand an element with id {id_to_expand}")
                el_present = apply_diff_element_on_list(self.snapshot_elements, diff_element)
                if not el_present:
                    raise GenerationError(f"Could not apply differential element: {diff_element}")

    def create_new_slice(self, diff_element):
        base_el, _ = self.find_element_by_id(
            self.snapshot_elements, diff_element["id"].split(":")[0]
        )

        # Find type for slice
        if "type" in diff_element and len(diff_element["type"]) == 1:
            slice_type = diff_element["type"][0]["code"]
        elif len(base_el["type"]) == 1:
            slice_type = base_el["type"][0]["code"]
        else:
            raise GenerationError(f"Could not infer slice type for diff element {diff_element}")

        # Create new slice for this conversion
        self.slices[diff_element["id"]] = Slice(
            snapshot_root=base_el,
            diff_element=diff_element,
            slice_type=slice_type,
            base_id=base_el["id"],
            api_url=self.api_url,
        )

    def add_to_existing_slice(self, diff_element):
        left, right = diff_element["id"].split(":", 1)
        root_id = left + ":" + right.split(".")[0]
        self.slices[root_id].add_diff_element(diff_element)

    def create_new_choice_element(self, diff_element, choice_root, choice_type):
        base_el, _ = self.find_element_by_id(self.snapshot_elements, choice_root)

        self.choice_type_elements[diff_element["id"]] = ChoiceTypeElement(
            snapshot_root=base_el,
            diff_element=diff_element,
            choice_root=choice_root,
            choice_type=choice_type,
            api_url=self.api_url,
        )

    def add_to_existing_choice_element(self, diff_element):
        # TODO this was already done in the if
        root_id = next(
            choice_elem_root
            for choice_elem_root in self.choice_type_elements
            if diff_element["id"].startswith(choice_elem_root)
        )
        self.choice_type_elements[root_id].add_diff_element(diff_element)

    def handle_extension_slice(self, diff_element):
        # TODO extensions are in reverse order
        # TODO can be quite slow, because of the api call?
        try:
            profile_url = diff_element["type"][0]["profile"]
        except KeyError:
            raise GenerationError("Couldn't find profile url in diff element.")
        extension_definition = fetch_structure_definition(api_url=self.api_url, url=profile_url)
        extension_root = get_root_element(extension_definition)
        for key_diff, val_diff in diff_element.items():
            # Replace keys in diff element
            # NOTE no need for checks, override everything
            extension_root[key_diff] = val_diff
        extension_element, insert_ind = self.find_element_by_id(
            self.snapshot_elements, extension_root["path"]
        )
        if "slicing" not in extension_element:
            # Add default slicing
            extension_element["slicing"] = {
                "discriminator": [{"type": "value", "path": "url"}],
                "ordered": False,
                "rules": "open",
            }
        # TODO function for that?
        self.snapshot_elements.insert(insert_ind + 1, extension_root)

    def augment_with_slices(self):
        for id_, slice_ in self.slices.items():
            # Find where to add
            _, insert_ind = self.find_element_by_id(
                self.snapshot_elements, slice_.root_id.split(":")[0]
            )
            insert_ind += 1
            for slice_element in slice_.snapshot_elements[::-1]:
                self.snapshot_elements.insert(insert_ind, slice_element)

    def augment_with_choice_elements(self):
        for id_, element in self.choice_type_elements.items():
            element.normalize_ids_and_paths()
            # Find where to add
            _, insert_ind = self.find_element_by_id(self.snapshot_elements, element.choice_root)
            insert_ind += 1
            for el in element.snapshot_elements[::-1]:
                self.snapshot_elements.insert(insert_ind, el)

    @staticmethod
    def is_renamed_choice_element(diff_el_id):
        root_id = diff_el_id.rsplit(".", 1)[0]
        for choice_root, choice_types in all_choice_elements["elements"].items():
            if not choice_root.startswith(root_id):
                continue
            for choice_type in choice_types:
                if diff_el_id == choice_root.replace("[x]", uppercase_first_letter(choice_type)):
                    return choice_root, choice_type

    @staticmethod
    def find_element_by_id(elements, id_):
        for ind, element in enumerate(elements):
            if element["id"] == id_:
                return element, ind
        return None, None
