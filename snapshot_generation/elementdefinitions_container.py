from abc import ABC, abstractproperty

from .apply_element import apply_diff_element_on_list
from .errors import GenerationError
from .helper import fetch_structure_definition, prepend_root


class ElementDefinitionsContainer(ABC):
    """
    This abstract class provides useful functions to process attributes being
    a list
    """

    @abstractproperty
    def snapshot_elements(self):
        raise NotImplementedError

    @staticmethod
    def replace_element(
        element,
        new_element,
        keys_to_skip=["id", "path", "name"],
        keys_to_remove=[],
        sliceName=None,
        new_type=None,
    ):
        # TODO check in place uses
        for k, v in new_element.items():
            if k in keys_to_skip:
                continue
            element[k] = v
        element = {k: v for k, v in element.items() if k not in keys_to_remove}

        if sliceName is not None:
            element["sliceName"] = sliceName

        if new_type is not None:
            element["type"] = [{"code": new_type}]

        return element

    def expand_element(self, element_id):
        for ind, element in enumerate(self.snapshot_elements):
            if element["id"] == element_id:
                assert (
                    len(element["type"]) == 1
                ), "Oops, several types found when trying to expand slice element"
                type_to_fetch = element["type"][0]["code"]
                fetch_def = fetch_structure_definition(api_url=self.api_url, id_=type_to_fetch)
                for new_el in fetch_def["snapshot"]["element"]:
                    if len(new_el["id"].split(".")) == 1:
                        # skip root
                        continue
                    ind += 1
                    new_el["id"] = prepend_root(element["id"], new_el["id"])
                    new_el["path"] = prepend_root(element["path"], new_el["path"])
                    self.snapshot_elements.insert(ind, new_el)
                return True
        return False

    def add_diff_element(self, diff_element):
        ok = apply_diff_element_on_list(self.snapshot_elements, diff_element)
        if not ok:
            if len(self.snapshot_elements) == 1:
                # If we only have the root in self.snapshot_elements
                # we get the other element that were cached
                self.snapshot_elements = self.root_base_elements
            else:
                # Else, we need to expand another element
                self.expand_element(diff_element["id"].rsplit(".", 1)[0])
            ok = apply_diff_element_on_list(self.snapshot_elements, diff_element)
            if not ok:
                raise GenerationError(f"Could not apply differential element: {diff_element}")
