import pytest
from roblox_injector.parser import parse_place_file
from roblox_injector.injector import inject_node, resolve_path_or_create, write_place_file
from roblox_injector.models import InjectionTarget, ScriptType

MINIMAL_PLACE = """<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4">
  <Item class="ReplicatedStorage" referent="RBX1">
    <Properties>
      <string name="Name">ReplicatedStorage</string>
    </Properties>
  </Item>
  <Item class="ServerScriptService" referent="RBX2">
    <Properties>
      <string name="Name">ServerScriptService</string>
    </Properties>
  </Item>
</roblox>"""

def test_inject_simple_module(tmp_path):
    p = tmp_path / "target.rbxlx"
    p.write_text(MINIMAL_PLACE, encoding="utf-8")
    tree = parse_place_file(p)

    target = InjectionTarget(
        name="Telemetry",
        script_type=ScriptType.MODULE_SCRIPT,
        parent_path="ReplicatedStorage",
        source="return { count = 0 }",
    )
    node = inject_node(tree, target)
    assert node.attrib["class"] == "ModuleScript"
    
    name_elem = node.find("./Properties/string[@name='Name']")
    assert name_elem is not None and name_elem.text == "Telemetry"

def test_inject_into_nested_nonexistent_folder(tmp_path):
    p = tmp_path / "target.rbxlx"
    p.write_text(MINIMAL_PLACE, encoding="utf-8")
    tree = parse_place_file(p)

    parent = resolve_path_or_create(tree, "ReplicatedStorage/Packages/Shims")
    assert parent.attrib["class"] == "Folder"
    assert parent.find("./Properties/string[@name='Name']").text == "Shims"

def test_overwrite_existing_script(tmp_path):
    p = tmp_path / "target.rbxlx"
    p.write_text(MINIMAL_PLACE, encoding="utf-8")
    tree = parse_place_file(p)

    t1 = InjectionTarget(
        name="Harness",
        script_type=ScriptType.SERVER_SCRIPT,
        parent_path="ServerScriptService",
        source="print('v1')",
    )
    inject_node(tree, t1, overwrite=True)

    t2 = InjectionTarget(
        name="Harness",
        script_type=ScriptType.SERVER_SCRIPT,
        parent_path="ServerScriptService",
        source="print('v2')",
    )
    inject_node(tree, t2, overwrite=True)

    sss = tree.root.find("./Item[@class='ServerScriptService']")
    matches = [c for c in sss.findall("Item") if c.find("./Properties/string[@name='Name']").text == "Harness"]
    assert len(matches) == 1
    src = matches[0].find("./Properties/ProtectedString[@name='Source']").text
    assert "print('v2')" in src

def test_roundtrip_save_and_reparse(tmp_path):
    src_path = tmp_path / "place.rbxlx"
    dst_path = tmp_path / "out.rbxlx"
    src_path.write_text(MINIMAL_PLACE, encoding="utf-8")
    
    tree = parse_place_file(src_path)
    target = InjectionTarget(
        name="Bootstrap",
        script_type=ScriptType.LOCAL_SCRIPT,
        parent_path="ReplicatedStorage",
        source="local x = 1\nreturn x",
        disabled=True
    )
    inject_node(tree, target)
    write_place_file(tree, dst_path)

    reloaded = parse_place_file(dst_path)
    rep = reloaded.root.find("./Item[@class='ReplicatedStorage']")
    script_node = rep.find("./Item[@class='LocalScript']")
    assert script_node is not None
    
    dis = script_node.find("./Properties/bool[@name='Disabled']")
    assert dis is not None and dis.text.lower() == "true"
