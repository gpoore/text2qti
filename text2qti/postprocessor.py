import io
import re
import xml.etree.ElementTree as ET

class CopyPreClassToCode(object):
    def postprocess(self, xml_string: str) -> str:

        # Register all namespaces using start-ns events
        try:
            wrapped = xml_string
            for event, (prefix, uri) in ET.iterparse(io.StringIO(wrapped), events=["start-ns"]):
                ET.register_namespace(prefix, uri)
        except ET.ParseError as e:
            try:
                wrapped = f"<root>{xml_string}</root>"
                for event, (prefix, uri) in ET.iterparse(io.StringIO(wrapped), events=["start-ns"]):
                    ET.register_namespace(prefix, uri)
            except ET.ParseError as e:
                print("Startof Unable to parse #########")
                print(wrapped)
                print("Endof Unable to parse #########")
                raise

        root = ET.fromstring(wrapped)
        #import pdb; pdb.set_trace()
        for pre in root.iter("pre"):
            pre_class = pre.get("class")
            if pre_class is not None:
                pre.set("class", "d2l-code line-numbers " + pre_class)
                for code in pre.findall("code"):
                    code.set("class", pre_class)

        result = ET.tostring(root, encoding="unicode")
        mo = re.match(r"^<root[^>]*>", result)
        if mo:
            result = result[len(mo.group(0)):]
        if result.endswith("</root>"):
            result = result[:-len("</root>")]
        return result

if __name__ == '__main__':
    test_string1 = (
        r"""<p><math display="inline" xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mrow>"""
        r"""<msup><mi>μ</mi><mo>*</mo></msup><mo>=</mo><mo stretchy="false" form="prefix">(</mo><m"""
        r"""subsup><mi>Σ</mi><mn>1</mn><mrow><mo>−</mo><mn>1</mn></mrow></msubsup><msub><mi>μ</mi>"""
        r"""<mn>2</mn></msub><mo>+</mo><msubsup><mi>Σ</mi><mn>2</mn><mrow><mo>−</mo><mn>1</mn></mr"""
        r"""ow></msubsup><msub><mi>μ</mi><mn>1</mn></msub><msup><mo stretchy="false" form="postfix"""
        r"""">)</mo><mrow><mo>−</mo><mn>1</mn></mrow></msup><mo stretchy="false" form="prefix">(</"""
        r"""mo><msubsup><mi>Σ</mi><mn>1</mn><mrow><mo>−</mo><mn>1</mn></mrow></msubsup><msub><mi>μ"""
        r"""</mi><mn>2</mn></msub><mo>+</mo><msubsup><mi>Σ</mi><mn>2</mn><mrow><mo>−</mo><mn>1</mn"""
        r"""></mrow></msubsup><msub><mi>μ</mi><mn>1</mn></msub><mo stretchy="false" form="postfix" """
        r""">)</mo></mrow><annotation encoding="application/x-tex">\mu^* = (\Sigma_1^{-1}\mu_2 +   """
        r"""\Sigma_2^{-1}\mu_1)^{-1}(\Sigma_1^{-1}\mu_2 + \Sigma_2^{-1}\mu_1)</annotation></semanti"""
        r"""cs></math></p>""")
    print(test_string1)
    print("+++++++++++++++")
    print(CopyPreClassToCode().postprocess(test_string1))
    test_string2 = (
            r"""<p>What is the output of the following code?</p>"""
            r"""<pre class="language-python"><code>nums = list(range(5))"""
            r"""print(nums[4:2:-1])</code></pre>""")
    print(test_string2)
    print("+++++++++++++++")
    print(CopyPreClassToCode().postprocess(test_string2))
