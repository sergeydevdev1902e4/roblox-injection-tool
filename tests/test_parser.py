import pytest
from roblox_injector.parser import parse_place_file, find_service, RobloxTreeError, extract_script_source

SAMPLE_RBXLX = """<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4">
  <Item class="Workspace" referent="RBX0">
    <Properties>
      <string name="Name">Workspace</string>
      <bool name="FilteringEnabled">true</bool>
    </Properties>
    <Item class="Part" referent="RBX1">
      <Properties>
        <string name="Name">Baseplate</string>
      </Properties>
    </Item>
  </Item>
  <Item class="ReplicatedStorage" referent="RBX2">
    <Properties>
      <string name="Name">ReplicatedStorage</string>
    </Properties>
    <Item class="ModuleScript" referent="RBX_MOD">
      <Properties>
        <string name="Name">Config</string>
        <ProtectedString name="Source"><![CDATA[return { debug = true }]]></ProtectedString>
      </Properties>
    </Item>
  </Item>
</roblox>"""

def test_parse_valid_place(tmp_path):
    p = tmp_path / "place.rbxlx"
    p.write_text(SAMPLE_RBXLX, encoding="utf-8")

    tree = parse_place_file(p)
    assert tree.root.tag == "roblox"

    ws = find_service(tree, "Workspace")
    assert ws is not None
    assert ws.attrib["referent"] == "RBX0"

    rep = find_service(tree, "ReplicatedStorage")
    assert rep is not None

def test_find_missing_service(tmp_path):
    p = tmp_path / "place.rbxlx"
    p.write_text(SAMPLE_RBXLX, encoding="utf-8")
    tree = parse_place_file(p)
    assert find_service(tree, "ServerScriptService") is None

def test_malformed_xml(tmp_path):
    p = tmp_path / "broken.rbxlx"
    p.write_text("<roblox><Item class='Workspace'>", encoding="utf-8")
    with pytest.raises(RobloxTreeError):
        parse_place_file(p)

def test_extract_script_source(tmp_path):
    p = tmp_path / "place.rbxlx"
    p.write_text(SAMPLE_RBXLX, encoding="utf-8")
    tree = parse_place_file(p)
    rep = find_service(tree, "ReplicatedStorage")
    mod = rep.find("./Item[@class='ModuleScript']")
    
    source = extract_script_source(mod)
    assert source == "return { debug = true }"

def test_empty_file(tmp_path):
    p = tmp_path / "empty.rbxlx"
    p.write_text("", encoding="utf-8")
    with pytest.raises(RobloxTreeError):
        parse_place_file(p)
