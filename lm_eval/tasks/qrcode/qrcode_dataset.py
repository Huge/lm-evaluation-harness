import json
import datasets
from datasets import DatasetInfo, Features, Value

_DESCRIPTION = """
QR Code generation evaluation dataset. Tests if a language model can generate valid QR codes in SVG format.
"""

_CITATION = """
"""

_TEST_INPUTS = [
    "Hello World",
    "https://example.com",
    "12345",
    "Lorem ipsum dolor sit amet",
    "https://github.com/EleutherAI/lm-evaluation-harness",
    "QR Code Test",
    "OpenAI GPT-4",
    "Cascade AI Assistant",
    "user@example.com",
    "Tel: +1-123-456-7890"
]

class QRCodeDataset(datasets.GeneratorBasedBuilder):
    """QR Code generation evaluation dataset."""

    VERSION = datasets.Version("1.0.0")

    def _info(self):
        return DatasetInfo(
            description=_DESCRIPTION,
            features=Features({
                "input_text": Value("string"),
                "svg_output": Value("string"),
            }),
            supervised_keys=None,
            homepage="",
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        return [
            datasets.SplitGenerator(
                name=datasets.Split.VALIDATION,
                gen_kwargs={
                    "inputs": _TEST_INPUTS,
                }
            ),
        ]

    def _generate_examples(self, inputs):
        for i, input_text in enumerate(inputs):
            yield i, {
                "input_text": input_text,
                "svg_output": "",  # Empty placeholder for model output
            }
