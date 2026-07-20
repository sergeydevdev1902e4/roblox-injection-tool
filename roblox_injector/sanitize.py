import re

# XML 1.0 valid chars: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
# Strip low ASCII control chars except tab, newline, cr
_ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def sanitize_luau_source(source: str) -> str:
    # print(f"sanitizing {len(source)} bytes")
    src = source.replace("\r\n", "\n").replace("\r", "\n")
    # Roblox Studio fails silently on weird control chars injected via XML
    src = _ILLEGAL_XML_CHARS.sub("", src)
    return src


def wrap_cdata(source: str) -> str:
    cleaned = sanitize_luau_source(source)
    
    # Roblox parser chokes if CDATA end tag appears inside source (e.g. comments or multiline strings)
    if "]]>" in cleaned:
        cleaned = cleaned.replace("]]>", "]]]]><![CDATA[>")
        
    return f"<![CDATA[{cleaned}]]>"


def escape_property_string(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
