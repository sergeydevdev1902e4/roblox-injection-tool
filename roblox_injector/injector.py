import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional

from roblox_injector.parser import PlaceTree
from roblox_injector.referent import generate_referent
from roblox_injector.sanitize import normalize_script_source


class RobloxInjector:
    """Traverses Roblox XML tree and mounts Luau scripts into specified instances."""

    def __init__(self, tree: PlaceTree):
        self.tree = tree

    def _find_or_create_child_folder(self, parent: ET.Element, name: str) -> ET.Element:
        for child in parent.findall("./Item"):
            props = child.find("Properties")
            if props is not None:
                name_el = props.find("string[@name='Name']")
                if name_el is not None and name_el.text == name:
                    return child

        folder = ET.SubElement(parent, "Item", {
            "class": "Folder",
            "referent": generate_referent(),
        })
        props = ET.SubElement(folder, "Properties")
        name_prop = ET.SubElement(props, "string", {"name": "Name"})
        name_prop.text = name
        return folder

    def _build_script_node(self, name: str, class_name: str, source: str) -> ET.Element:
        item = ET.Element("Item", {
            "class": class_name,
            "referent": generate_referent(),
        })
        props = ET.SubElement(item, "Properties")
        
        name_el = ET.SubElement(props, "string", {"name": "Name"})
        name_el.text = name

        # Roblox requires Disabled flag for normal Script/LocalScript instances
        if class_name in ("Script", "LocalScript"):
            disabled_el = ET.SubElement(props, "bool", {"name": "Disabled"})
            disabled_el.text = "false"

        src_el = ET.SubElement(props, "ProtectedString", {"name": "Source"})
        src_el.text = normalize_script_source(source)
        
        return item

    def inject_script(self, hierarchy_path: str, source: str, class_name: str = "ModuleScript", overwrite: bool = True) -> ET.Element:
        # hierarchy_path format: 'ReplicatedStorage/Telemetry/Logger' or 'ServerScriptService.Bootstrap'
        normalized = hierarchy_path.replace(".", "/").strip("/")
        parts = [p for p in normalized.split("/") if p]
        if not parts:
            raise ValueError(f"Invalid empty hierarchy path: {hierarchy_path}")

        service_name = parts[0]
        service_elem = self.tree.find_service(service_name)

        if service_elem is None:
            service_elem = ET.SubElement(self.tree.root, "Item", {
                "class": service_name,
                "referent": generate_referent(),
            })
            props = ET.SubElement(service_elem, "Properties")
            n_el = ET.SubElement(props, "string", {"name": "Name"})
            n_el.text = service_name

        parent = service_elem
        for part in parts[1:-1]:
            parent = self._find_or_create_child_folder(parent, part)

        script_name = parts[-1]
        
        # check if script exists at destination
        for child in list(parent.findall("./Item")):
            c_props = child.find("Properties")
            if c_props is not None:
                name_el = c_props.find("string[@name='Name']")
                if name_el is not None and name_el.text == script_name:
                    if overwrite:
                        # print(f"DEBUG: removing existing node {script_name}")
                        parent.remove(child)
                    else:
                        # keep existing, update source in place
                        src_prop = c_props.find("ProtectedString[@name='Source']")
                        if src_prop is not None:
                            src_prop.text = normalize_script_source(source)
                            return child

        node = self._build_script_node(script_name, class_name, source)
        parent.append(node)
        # FIXME: handle Model instances that wrap scripts when importing rbxmx bundles
        return node


def inject_bundle(target_path: Path, out_path: Path, items: List[Dict[str, Any]]):
    tree = PlaceTree.from_file(target_path)
    injector = RobloxInjector(tree)
    for item in items:
        injector.inject_script(
            hierarchy_path=item["path"],
            source=item["source"],
            class_name=item.get("class", "ModuleScript"),
            overwrite=item.get("overwrite", True),
        )
    tree.write(out_path)
