import unittest
from unittest import skip

from lxml import etree

from arxivnlp import xml_match as xm


class TestDnm(unittest.TestCase):
    formula_1 = etree.XML(r'''
        <math id="p1.1.m1.1" class="ltx_Math" alttext="x\in X" display="inline">
          <semantics id="p1.1.m1.1a">
            <mrow id="p1.1.m1.1.1" xref="p1.1.m1.1.1.cmml">
              <mi id="p1.1.m1.1.1.2" xref="p1.1.m1.1.1.2.cmml">x</mi>
              <mo id="p1.1.m1.1.1.1" xref="p1.1.m1.1.1.1.cmml">&#x2208;</mo>
              <mi id="p1.1.m1.1.1.3" xref="p1.1.m1.1.1.3.cmml">X</mi>
            </mrow>
            <annotation-xml encoding="MathML-Content" id="p1.1.m1.1b">
              <apply id="p1.1.m1.1.1.cmml" xref="p1.1.m1.1.1">
                <in id="p1.1.m1.1.1.1.cmml" xref="p1.1.m1.1.1.1"/>
                <ci id="p1.1.m1.1.1.2.cmml" xref="p1.1.m1.1.1.2">&#x1D465;</ci>
                <ci id="p1.1.m1.1.1.3.cmml" xref="p1.1.m1.1.1.3">&#x1D44B;</ci>
              </apply>
            </annotation-xml>
            <annotation encoding="application/x-tex" id="p1.1.m1.1c">x\in X</annotation>
            <annotation encoding="application/x-llamapun" id="p1.1.m1.1d">italic_x &#x2208; italic_X</annotation>
          </semantics>
        </math>''')

    formula_2 = etree.XML('''
<math id="S5.SS1.p2.8.m8.1" class="ltx_Math" alttext="\\sim 10\\%" display="inline">
  <semantics id="S5.SS1.p2.8.m8.1a">
    <mrow id="S5.SS1.p2.8.m8.1.1" xref="S5.SS1.p2.8.m8.1.1.cmml">
      <mi id="S5.SS1.p2.8.m8.1.1.2" xref="S5.SS1.p2.8.m8.1.1.2.cmml"/>
      <mo id="S5.SS1.p2.8.m8.1.1.1" xref="S5.SS1.p2.8.m8.1.1.1.cmml">&#x223C;</mo>
      <mrow id="S5.SS1.p2.8.m8.1.1.3" xref="S5.SS1.p2.8.m8.1.1.3.cmml">
        <mn id="S5.SS1.p2.8.m8.1.1.3.2" xref="S5.SS1.p2.8.m8.1.1.3.2.cmml">10</mn>
        <mo id="S5.SS1.p2.8.m8.1.1.3.1" xref="S5.SS1.p2.8.m8.1.1.3.1.cmml">%</mo>
      </mrow>
    </mrow>
  </semantics>
</math>
    ''')

    def test_simple(self):
        base_matcher = xm.tag('math') / xm.tag('semantics')

        matcher = base_matcher / xm.tag('mrow') / xm.seq(xm.tag('mi') ** 'lhs', xm.tag('mo'), xm.tag('mi') ** 'rhs')
        matches = list(matcher.match(self.formula_1))
        self.assertEqual(len(matches), 1)
        tree = matches[0].to_label_tree()
        self.assertEqual(tree['lhs'].node.text, 'x')
        self.assertEqual(tree['rhs'].node.text, 'X')
        self.assertEqual(len(tree.children), 2)

        matcher = base_matcher / xm.tag('annotation-xml') / xm.tag('apply') / xm.tag('ci') ** 'identifier'
        matches = list(matcher.match(self.formula_1))
        self.assertEqual(len(matches), 2)

        matcher = base_matcher / (xm.tag('annotation-xml') | xm.tag('mrow')) / \
                  (xm.tag('apply') / xm.tag('ci') ** 'identifier_ci' | xm.tag('mi') ** 'identifier_mi')
        matches = list(matcher.match(self.formula_1))
        self.assertEqual(len(matches), 4)

    def test_seq_or(self):
        matcher = xm.seq(xm.empty_seq | xm.empty_seq, xm.tag('math'))
        matches = list(matcher.match([self.formula_1]))
        self.assertGreaterEqual(len(matches), 1)
