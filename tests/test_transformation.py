import pytest
from main import transform_georgian_text


TEST_CASES = [
    # Original, Transformed
    (
        "გაფუჭებული ტელეფონი",
        "განბუნჯენბული დელენბონი",
    ),
    (
        "კომპიუტერული მოწყობილობა",
        "გომნბიუნდერული მონძღონბილონბა",
    ),
    (
        "მასწავლებელი კლასში შევიდა და სწავლის პროცესი დაიწყო",
        "მანზნძანვლენბელი გლანზნჟი ჟენვინდა და ზნძანვლინზ ბრონძენზი დაინძღო",
    ),
]


@pytest.mark.parametrize("original, transformed", TEST_CASES)
def test_transformations(original: str, transformed: str) -> None:
    """
    Test the transformation of Georgian text based on the provided test cases.
    Each test case consists of an original string and its expected transformed version.
    """
    result = transform_georgian_text(original)

    assert result == transformed, (
        f"Expected '{transformed}', but got '{result}' for '{original}'"
    )
