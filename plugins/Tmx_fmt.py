"""
llm_jsoni18.formats.tmx_fmt
~~~~~~~~~~~~~~~~~~~~~~~~~~~
TMX ↔ Unit round-trip.
Reads/writes Translation Memory eXchange (TMX 1.4b).

Requires no extra deps — uses stdlib xml.etree only.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import Iterable, Iterator
from ..core import Unit


def tmx_to_units(path_or_fp, *, lang_src: str = "en", lang_tgt: str = "") -> Iterator[Unit]:
    tree = ET.parse(path_or_fp)
    root = tree.getroot()
    body = root.find("body")
    for tu in body.findall("tu"):
        uid   = tu.get("tuid", "")
        note_el = tu.find("note")
        note  = note_el.text if note_el is not None else ""
        tuvs  = {tuv.get("{http://www.w3.org/XML/1998/namespace}lang", "").lower(): tuv
                 for tuv in tu.findall("tuv")}
        src_tuv = tuvs.get(lang_src.lower())
        tgt_tuv = tuvs.get(lang_tgt.lower()) if lang_tgt else None
        if src_tuv is None:
            # fall back to first tuv as source
            src_tuv = next(iter(tuvs.values()), None)
        source = (src_tuv.findtext("seg") or "") if src_tuv else ""
        target = (tgt_tuv.findtext("seg") or "") if tgt_tuv else ""
        yield Unit(id=uid or source[:40], source=source, target=target,
                   note=note, lang_src=lang_src, lang_tgt=lang_tgt)


def units_to_tmx(units: Iterable[Unit], *, src_lang: str = "en", tgt_lang: str = "xx") -> str:
    """Return a TMX 1.4b XML string."""
    root = ET.Element("tmx", version="1.4")
    header = ET.SubElement(root, "header",
        creationtool="llm-jsoni18", creationtoolversion="0.1",
        datatype="plaintext", segtype="sentence",
        adminlang="en-US", srclang=src_lang, o_tmf="llm-jsoni18",
    )
    body = ET.SubElement(root, "body")
    for u in units:
        tu = ET.SubElement(body, "tu", tuid=u["id"])
        if u.get("note"):
            note_el = ET.SubElement(tu, "note")
            note_el.text = u["note"]
        for lang, text in [(src_lang, u["source"]), (tgt_lang, u.get("target", ""))]:
            tuv = ET.SubElement(tu, "tuv", **{"xml:lang": lang})
            seg = ET.SubElement(tuv, "seg")
            seg.text = text
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
