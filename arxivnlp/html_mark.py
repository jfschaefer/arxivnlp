from typing import Optional

from lxml import etree
from arxivnlp.data.dnm import DnmStr


def highlight_dnmstring(dnmstring: DnmStr, color: str = 'red', fontscale: float = 1.0, tag: Optional[str] = None):
    if tag is not None:
        dnmstring.dnm.add_node(node=etree.XML(f'<sup style="color:blue">{tag}</sup>'),
                               pos=dnmstring.backrefs[-1], after=True)
    dnmstring.dnm.add_node(node=etree.XML(f'<span style="color:{color}; font-size:{fontscale * 100}%">[</span>'),
                           pos=dnmstring.backrefs[0])
    dnmstring.dnm.add_node(node=etree.XML(f'<span style="color:{color}; font-size:{fontscale * 100}%">]</span>'),
                           pos=dnmstring.backrefs[-1], after=True)

