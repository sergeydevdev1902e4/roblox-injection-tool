import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Generator

from roblox_injector.models import InstanceNode

# Roblox parser requires exact tag order for Properties and child Items,
# and fails hard if ProtectedString elements lose CDATA block formatting.


class PlaceTree:
    """Wrapper around parsed Roblox XML place (.rbxlx) or model (.rbxmx) files."""

    def __init__(self, root: ET.Element, raw_header: str = ""):
        self.root = root
        self.raw_header = raw_header

    @classmethod
    def from_file(cls, path: Path) -> "PlaceTree":
        # Studio place files can be hundreds of megabytes, but we need in-memory
        # DOM to safely insert nested scripts without breaking parent links.
        content = path.read_text(encoding="utf-8", errors="replace")
        
        header_lines = []
        for line in content.splitlines()[:5]:
            if line.startswith("<?xml") or line.startswith("<roblox"):
                header_lines.append(line)

        root = ET.fromstring(content)
        return cls(root, "\n".join(header_lines))

    def find_service(self, service_name: str) -> Optional[ET.Element]:
        for item in self.root.findall("./Item"):
            props = item.find("Properties")
            if props is not None:
                name_el = props.find("string[@name='Name']")
                if name_el is not None and name_el.text == service_name:
                    return item
            if item.attrib.get("class") == service_name:
                return item
        return None

    def get_services(self) -> List[InstanceNode]:
        services = []
        for item in self.root.findall("./Item"):
            class_name = item.attrib.get("class", "Folder")
            props = item.find("Properties")
            name = class_name
            if props is not None:
                name_el = props.find("string[@name='Name']")
                if name_el is not None and name_el.text:
                    name = name_el.text
            services.append(InstanceNode(name=name, class_name=class_name, element=item, depth=0))
        return services

    def walk_children(self, parent_node: InstanceNode) -> Generator[InstanceNode, None, None]:
        for child in parent_node.element.findall("./Item"):
            c_name = child.attrib.get("class", "Unknown")
            props = child.find("Properties")
            if props is not None:
                name_el = props.find("string[@name='Name']")
                if name_el is not None and name_el.text:
                    c_name = name_el.text
            node = InstanceNode(
                name=c_name,
                class_name=child.attrib.get("class", "Instance"),
                element=child,
                depth=parent_node.depth + 1,
            )
            yield node
            yield from self.walk_children(node)

    def write(self, dest: Path):
        # Custom serialization because default ElementTree wraps CDATA entities
        # as escaped &lt;![CDATA[ which Studio refuses to load as source code.
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        raw_xml = ET.tostring(self.root, encoding="utf-8")
        
        # Studio prefers pretty indentation on top-level elements.
        # ET.indent was added in 3.9; fallback is ok for older runtimes.
        try:
            ET.indent(self.root, space="  ", level=0)
            raw_xml = ET.tostring(self.root, encoding="utf-8")
        except AttributeError:
            pass

        header = b'<?xml version="1.0" encoding="utf-8"?>\n'
        dest_path.write_bytes(header + raw_xml)
