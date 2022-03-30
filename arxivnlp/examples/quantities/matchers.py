import unicodedata
from typing import Union, Tuple

from arxivnlp import xml_match as xm
from arxivnlp.examples.quantities.center import Scalars, ScalarNotation
from arxivnlp.examples.quantities.quantity_kb import Notation, UnitNotation
from arxivnlp.xml_match import LabelTree


class UndesirableMatchException(Exception):
    """
        A match cannot be processed or is rejected, even though it should be a valid match according to the matcher.
        You could say it's a logical error, not a syntax error.
    """
    pass


# ***************
# * BASIC NODES *
# ***************

mrow = xm.tag('mrow')
mo = xm.tag('mo')
mn = xm.tag('mn')
mtext = xm.tag('mtext')
msup = xm.tag('msup')

relational_mo = mo.with_text(
    '[' + ''.join({'=', '≈', '<', '>', '≪', '≫', '≥', '⩾', '≤', '⩽', '∼', '≲', '≳'}) + ']')
empty_tag = xm.any_tag.with_text('^$')
space = mtext.with_text(r'\s*')
base = xm.tag('math') / xm.tag('semantics')


# ***********************
# * NUMBERS AND SCALARS *
# ***********************

def mn_to_number(mn_text: str) -> Union[float, int]:
    reduced = ''
    for c in mn_text:
        if c.isnumeric():
            reduced += c
        elif c == '.':
            reduced += c
        elif c.isspace():
            continue
        else:
            print(f'Can\'t convert mn {repr(mn_text)}')
    return float(reduced) if '.' in reduced else int(reduced)


simple_number = (
                        mn ** 'numeral' |
                        mrow / xm.seq(mo.with_text(r'[-–]') ** 'negative', mn ** 'numeral')
                ) ** 'simplenumber'
power_of_10 = (msup / xm.seq(mn.with_text('^10$'), simple_number ** 'exponent')) ** 'powerof10'
scientific_number = (mrow / xm.seq(simple_number ** 'factor', mtext.with_text('[×]'),
                                   power_of_10)) ** 'scientific'


def tree_to_number(lt: LabelTree) -> Tuple[Union[int, float], str]:
    if lt.label == 'simplenumber':
        sign = -1 if lt.has_child('negative') else 1
        return sign * mn_to_number(lt['numeral'].node.text), 'simple'
    elif lt.label == 'scientific':
        return tree_to_number(lt['factor'])[0] * tree_to_number(lt['powerof10'])[0], 'scientific'
    elif lt.label == 'powerof10':
        return 10 ** tree_to_number(lt['exponent'])[0], 'powerof10'
    elif len(lt.children) == 1:
        return tree_to_number(lt.children[0])
    raise Exception(f'Unsupported tree: {lt}')


scalar = (simple_number | scientific_number | power_of_10 |
          (mrow / xm.seq(empty_tag, mo.with_text(f'^{unicodedata.lookup("INVISIBLE TIMES")}$'),
                         power_of_10))  # presumably this happens when using siunitx and leaving the factor empty
          ) ** 'scalar'

def scalar_to_scalars(lt: LabelTree) -> Scalars:
    number, type_ = tree_to_number(lt)
    scalar_notation = ScalarNotation(0)
    if type(number) == int:
        scalar_notation |= ScalarNotation.IS_INT
    if type_ == 'scientific':
        scalar_notation |= ScalarNotation.SCIENTIFIC
    return Scalars(float(number), scalar_notation=scalar_notation)

# *********
# * UNITS *
# *********

simple_unit = (xm.tag('mi') |
               xm.tag('mo')  # e.g. for "%"
               ) ** 'simpleunit'  # TODO: expand this

def simple_unit_to_notation(lt: LabelTree) -> Notation:
    assert lt.label == 'simpleunit'
    # TODO: This will get much more complex
    node = lt.node
    attr = {'val': node.text}
    if node.tag == 'mi' and node.text and len(node.text) == 1 and node.get('mathvariant') != 'normal':
        attr['isitalic'] = True
    return Notation('i', attr, [])


unit_power = (xm.tag('msup') / xm.seq(simple_unit, simple_number ** 'exponent')) ** 'unitpower'
unit_times2 = (mrow / xm.seq(simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power)) ** 'unittimes'
unit_times3 = (mrow / xm.seq(simple_unit | unit_power, xm.maybe(space), simple_unit | unit_power, xm.maybe(space),
                             simple_unit | unit_power)) ** 'unittimes'
unit = (simple_unit | unit_power | unit_times2 | unit_times3) ** 'unit'


def unit_to_unit_notation(lt: LabelTree) -> UnitNotation:
    if lt.label == 'unit':
        assert len(lt.children) == 1
        return unit_to_unit_notation(lt.children[0])
    elif lt.label == 'simpleunit':
        notation = simple_unit_to_notation(lt)
        return UnitNotation([(notation, 1)])
    elif lt.label == 'unitpower':
        notation = simple_unit_to_notation(lt['simpleunit'])
        exponent = tree_to_number(lt['exponent'])[0]
        if exponent not in range(-10, 10):
            raise UndesirableMatchException(f'Bad exponent for a unit: {exponent}')
        return UnitNotation([(notation, exponent)])
    elif lt.label == 'unittimes':
        parts = []
        for subunit in lt.children:
            parts += unit_to_unit_notation(subunit).parts
        return UnitNotation(parts)
    raise Exception(f'Unsupported node: {lt.label}')


# **************
# * QUANTITIES *
# **************

quantity = mrow / xm.seq(scalar, xm.maybe(space), unit)
quantity_in_rel = mrow / xm.seq(xm.maybe(xm.any_tag), relational_mo, quantity)
