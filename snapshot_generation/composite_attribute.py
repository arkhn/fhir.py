from abc import ABC

from .helper import *

class CompositeAttribute(ABC):
    def replace_root_element(
        self,
        new_element,
        keys_to_skip=["id", "path", "name"],
        keys_to_remove=[],
        sliceName=None,
        new_type=None,
    ):
        # Replace root type snapshot by root base snapshot
        # NOTE not 100% sure why there are some keys to remove. More of an empirical
        # rule than anything else.
        for ind, el in enumerate(self.definition_elements):
            if len(el["id"].split(".")) == 1:
                for k, v in new_element.items():
                    if k in keys_to_skip:
                        continue
                    self.definition_elements[ind][k] = v
                self.definition_elements[ind] = {
                    k: v
                    for k, v in self.definition_elements[ind].items()
                    if k not in keys_to_remove
                }

                if sliceName is not None:
                    self.definition_elements[ind]["sliceName"] = sliceName

                if new_type is not None:
                    self.definition_elements[ind]["type"] = [{"code": new_type}]

                break

    def expand_element(self, element_id):
        for ind, element in enumerate(self.definition_elements):
            if element["id"] == element_id:
                assert (
                    len(element["type"]) == 1
                ), "Oops, several types found when trying to expand slice element"
                type_to_fetch = element["type"][0]["code"]
                fetch_def = fetch_structure_definition(id_=type_to_fetch)
                for new_el in fetch_def["snapshot"]["element"]:
                    if len(new_el["id"].split(".")) == 1:
                        # skip root
                        continue
                    ind += 1
                    new_el["id"] = prepend_root(element["id"], new_el["id"])
                    new_el["path"] = prepend_root(element["path"], new_el["path"])
                    self.definition_elements.insert(ind, new_el)
                break
