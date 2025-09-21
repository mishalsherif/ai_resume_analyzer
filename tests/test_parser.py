from utils import parser


def test_extract_txt():
    b = b"Hello\nWorld"
    assert "Hello" in parser.extract_text_from_txt(b)


def test_extract_text_detect_by_filename():
    b = b"John Doe\nExperience: Python"
    assert "Experience" in parser.extract_text(b, filename="resume.txt")
