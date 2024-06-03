from typing import Union, List, Iterable, Optional, Mapping, Sequence, Any, Tuple
import re
from bs4 import BeautifulSoup, NavigableString

from boba_python_utils.string_utils import string_check

HTML_STYLE_STRING_REGEX = re.compile(r'^<([a-zA-Z][a-zA-Z0-9]*)[^>]*>.*?</\1>$', re.DOTALL)


def is_html_style_string(s: str) -> bool:
    """Check if a string is enclosed by any HTML tag.

    This function uses a regular expression to determine if a given string
    is enclosed by a matching pair of HTML tags.

    Args:
        s: The input string to check.

    Returns:
        True if the string is enclosed by a matching HTML tag, False otherwise.

    Examples:
        >>> is_html_style_string("<p>This is a paragraph.</p>")
        True
        >>> is_html_style_string("<div><p>This is a paragraph.</p></div>")
        True
        >>> is_html_style_string("<span>Some text</span>")
        True
        >>> is_html_style_string("<a href='example.com'>Link</a>")
        True
        >>> is_html_style_string("<p>Nested <span>text</span></p>")
        True
        >>> is_html_style_string("<div>\\n<p>Text on\\nmultiple lines</p>\\n</div>")
        True
        >>> is_html_style_string("<div>\\n<p>Text on\\nmultiple lines</p>\\n</span>")
        False
        >>> is_html_style_string("Just a plain text")
        False
    """
    match = HTML_STYLE_STRING_REGEX.fullmatch(s)
    return match is not None


def get_tag_text_and_attributes_from_element_html(
        element_html: str
) -> Tuple[Optional[str], Optional[str], Mapping[str, str]]:
    """
    Parses an HTML snippet to extract the tag name, combined text content of the element and its descendants,
    and all attributes of the element.

    Args:
        element_html (str): A string containing the HTML snippet of a single element.

    Returns:
        tuple: Returns a tuple containing:
            - tag (str): The tag name of the HTML element.
            - text (str): All text content combined from the element and its descendants, stripped of leading/trailing whitespace.
            - attributes (dict): A dictionary of all attributes of the element.

    Examples:
        >>> html_snippet = '<div class="example" id="test"><p>Hello</p><p>World</p></div>'
        >>> get_tag_text_and_attributes_from_element_html(html_snippet)
        ('div', 'HelloWorld', {'class': ['example'], 'id': 'test'})

        >>> html_snippet = '<input type="text" value="Sample" disabled>'
        >>> get_tag_text_and_attributes_from_element_html(html_snippet)
        ('input', '', {'type': 'text', 'value': 'Sample', 'disabled': ''})

        >>> html_snippet = '<a href="#" title="Link">Click here</a>'
        >>> get_tag_text_and_attributes_from_element_html(html_snippet)
        ('a', 'Click here', {'href': '#', 'title': 'Link'})
    """
    soup = BeautifulSoup(element_html, 'html.parser')
    # Access the first element that is not the document itself, usually the first child of the soup object.
    element = soup.find()
    if element:
        tag_name: Optional[str] = element.name
        text: Optional[str] = element.get_text(strip=True)
        attributes: Mapping[str, str] = element.attrs
    else:
        tag_name, text, attributes = None, None, {}

    return tag_name, text, attributes


def has_immediate_text(element):
    return any(isinstance(child, NavigableString) and child.strip() for child in element.children)


def remove_immediate_text(element):
    for child in element.children:
        if isinstance(child, NavigableString):
            child.extract()


def get_attribute_names_by_pattern(element, attribute_pattern: Union[str, Iterable[str]]) -> List[str]:
    """
    Get attribute names of an element that match the specified pattern(s).

    Args:
        element: The BeautifulSoup element.
        attribute_pattern: A single pattern or a list of patterns to match attribute names.

    Returns:
        A list of attribute names that match the pattern(s), or None if no matches.

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> html_content = '<div id="content" class="container" data-value="example">Hello, world!</div>'
        >>> soup = BeautifulSoup(html_content, 'html.parser')
        >>> element = soup.div
        >>> get_attribute_names_by_pattern(element, '^d')
        ['data-value']
        >>> get_attribute_names_by_pattern(element, '*')
        ['id', 'class', 'data-value']
        >>> get_attribute_names_by_pattern(element, ['id', 'class'])
        ['id', 'class']
        >>> get_attribute_names_by_pattern(element, ['id', '$e'])
        ['id', 'data-value']
        >>> get_attribute_names_by_pattern(element, ['!d', 'at'])
        ['id', 'class', 'data-value']
        >>> get_attribute_names_by_pattern(element, ['!^data-'])
        ['id', 'class']
    """
    if attribute_pattern == '*':
        return list(element.attrs.keys())
    elif not attribute_pattern:
        return []
    elif isinstance(attribute_pattern, str):
        return [
            attr for attr in element.attrs
            if string_check(attr, attribute_pattern)
        ]
    else:
        return [
            attr for attr in element.attrs
            if any(
                string_check(attr, _attr_pattern)
                for _attr_pattern in attribute_pattern
            )
        ]


def get_attribute_names_excluding_pattern(element, attribute_pattern: Union[str, Iterable[str]]) -> List[str]:
    """
    Get attribute names of an element excluding those that match the specified pattern(s).

    Args:
        element: The BeautifulSoup element.
        attribute_pattern: A single pattern or a list of patterns to exclude attribute names.

    Returns:
        Optional[List[str]]: A list of attribute names that do not match the pattern(s), or None if no exclusions.

    Examples:
        >>> html_content = '<div id="content" class="container" data-value="example">Hello, world!</div>'
        >>> soup = BeautifulSoup(html_content, 'html.parser')
        >>> element = soup.div
        >>> get_attribute_names_excluding_pattern(element, '*')
        []
        >>> get_attribute_names_excluding_pattern(element, ['id', 'class'])
        ['data-value']
        >>> get_attribute_names_excluding_pattern(element, '^d')
        ['id', 'class']
        >>> get_attribute_names_excluding_pattern(element, ['id', '$e'])
        ['class']
        >>> get_attribute_names_excluding_pattern(element, ['!d', 'at'])
        []
        >>> get_attribute_names_excluding_pattern(element, ['!^data-'])
        ['data-value']
    """
    if attribute_pattern == '*':
        return []
    elif not attribute_pattern:
        return list(element.attrs.keys())
    elif isinstance(attribute_pattern, str):
        return [
            attr for attr in element.attrs
            if not string_check(attr, attribute_pattern)
        ]
    else:
        return [
            attr for attr in element.attrs
            if not any(
                string_check(attr, attr_pattern)
                for attr_pattern in attribute_pattern
            )
        ]


def keep_specified_attributes(element, attributes_to_keep: Union[str, Iterable[str]]):
    """
    Keep specified attributes of an element and remove the rest.

    Args:
        element: The BeautifulSoup element.
        attributes_to_keep: A single attribute or a list of attributes to keep.

    Examples:
        >>> from copy import deepcopy
        >>> html_content = '<div id="content" class="container" data-value="example">Hello, world!</div>'
        >>> soup = BeautifulSoup(html_content, 'html.parser')
        >>> element = deepcopy(soup.div)
        >>> keep_specified_attributes(element, 'id')
        >>> str(element)
        '<div id="content">Hello, world!</div>'
        >>> element = deepcopy(soup.div)
        >>> keep_specified_attributes(element, ['class', 'data-value'])
        >>> str(element)
        '<div class="container" data-value="example">Hello, world!</div>'
        >>> element = deepcopy(soup.div)
        >>> keep_specified_attributes(element, '*')
        >>> str(element)
        '<div class="container" data-value="example" id="content">Hello, world!</div>'
        >>> element = deepcopy(soup.div)
        >>> keep_specified_attributes(element, '')
        >>> str(element)
        '<div>Hello, world!</div>'
    """
    attrs_to_remove = get_attribute_names_excluding_pattern(element, attribute_pattern=attributes_to_keep)
    if attrs_to_remove:
        for attr in attrs_to_remove:
            del element[attr]


def find_element_by_attribute(html_content: str, attribute_name: str, attribute_value: str) -> str:
    """
    Finds the HTML element with the specified attribute and value.

    Args:
        html_content: A string containing HTML content to be searched.
        attribute_name: The name of the attribute to search for.
        attribute_value: The value of the attribute to match.

    Returns:
        The HTML representation of the found element, or an empty string if not found.

    Examples:
        >>> sample_html = '''
        ... <div __id__="123">Hello, world!</div>
        ... <div __id__="456">Another div</div>
        ... <span __id__="123">Span with matching id</span>
        ... '''
        >>> found_element = find_element_by_attribute(sample_html, '__id__', '123')
        >>> str(found_element)
        '<div __id__="123">Hello, world!</div>'

        This example demonstrates finding an element with the specified attribute and value ('__id__="123"') within a more complex HTML structure.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    found_element = soup.find(attrs={attribute_name: attribute_value})
    return found_element


def find_element_by_any_attribute(html_content: str, attributes: Mapping[str, str]) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    for attribute_name, attribute_value in attributes.items():
        found_element = soup.find(attrs={attribute_name: attribute_value})
        if found_element:
            return found_element


def get_xpath(
        tag_name: Optional[str] = '*',
        attributes: Mapping[str, Any] = None,
        text: str = None,
        immediate_text: str = None
) -> str:
    """
    Generate an XPath expression based on an optional tag name, attribute key-value pairs, and optional text content.

    Args:
        tag_name (str, optional): The tag name of the element. Defaults to '*' which matches any tag.
        attributes (dict, optional): A dictionary containing attribute key-value pairs.
        text (str, optional): The text content to search for within the element and its descendants.
        immediate_text (str, optional): The immediate text content to search for within the element.

    Returns:
        str: The generated XPath expression.

    Example:
        >>> get_xpath('a', {'class': ['uitk-tab-anchor'], 'href': '/Flights'})
        '//a[contains(@class, "uitk-tab-anchor") and @href="/Flights"]'
        >>> get_xpath('a', {'class': ['uitk-tab-anchor'], 'href': '/Flights'}, "Book Now")
        '//a[contains(@class, "uitk-tab-anchor") and @href="/Flights" and contains(., "Book Now")]'
        >>> get_xpath(attributes={'class': ['button'], 'type': 'submit'}, text="Click Here")
        '//*[contains(@class, "button") and @type="submit" and contains(., "Click Here")]'

        >>> from lxml import etree
        >>> from lxml.html import fromstring
        >>> html_doc = '''
        ... <div class="container">
        ...     <h1>Welcome to My Site</h1>
        ...     <p class="description">Learn more about our services.</p>
        ...     <div class="button-container">
        ...         <button type="submit" class="btn primary large" onclick="submitForm()">Submit</button>
        ...         <button type="button" class="btn secondary">Cancel</button>
        ...     </div>
        ...     <a href="/contact" class="link" title="Contact Us">Contact us today!</a>
        ...     <div class="footer">
        ...         <p class="info">Visit our blog for more information.</p>
        ...         <p class="info">Follow us on <a href="/social" class="link social">social media</a></p>
        ...     </div>
        ... </div>
        ... '''
        >>> tree = fromstring(html_doc)
        >>> xpath_submit_button = get_xpath('button', attributes={'type': 'submit', 'class': ['btn', 'primary', 'large']}, immediate_text='Submit')
        >>> submit_button = tree.xpath(xpath_submit_button)
        >>> submit_button[0].text.strip() if submit_button else 'No Button Found'
        'Submit'
    """
    if not tag_name:
        tag_name = '*'
    xpath_parts = [f"//{tag_name}"]
    conditions = []
    if attributes:
        if not isinstance(attributes, Mapping):
            raise TypeError(f"'attributes' must be a key/value mapping; got '{attributes}' of type '{type(attributes)}'")
        for key, value in attributes.items():
            if isinstance(value, str):
                conditions.append(f'@{key}="{value}"')
            elif isinstance(value, Sequence):  # Handling attributes with multiple possible values
                conditions.extend([f'contains(@{key}, "{v}")' for v in value])
            else:
                conditions.append(f'@{key}="{value}"')

    if text:
        conditions.append(f'contains(., "{text}")')

    if immediate_text:
        conditions.append(f'contains(text(), "{immediate_text}")')

    if conditions:
        xpath_parts.append('[' + ' and '.join(conditions) + ']')
    return ''.join(xpath_parts)


def extract_attributes(html_content: str, tag: str, attributes: list) -> dict:
    """
    Extracts specified attributes of an HTML element and returns them as a dictionary.

    Args:
        html_content (str): A string containing HTML content to be searched.
        tag (str): The name of the HTML tag to search for.
        attributes (list): A list of attribute names to extract from the element.

    Returns:
        dict: A dictionary containing the specified attributes and their values.

    Examples:
        >>> sample_html = '<div id="123" class="container" data-value="example">Hello, world!</div>'
        >>> extracted_attributes = extract_attributes(sample_html, 'div', ['id', 'class', 'data-value'])
        >>> print(extracted_attributes)
        {'id': '123', 'class': 'container', 'data-value': 'example'}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    element = soup.find(tag)
    if element:
        return {attr: element.get(attr) for attr in attributes if element.get(attr) is not None}
    else:
        return {}


def add_unique_index_to_html(html_content: str, index_name: str = '__index__') -> str:
    """
    Adds a unique index to each HTML tag in the provided HTML content using a specified attribute name.

    Args:
        html_content (str): A string containing HTML content to be processed.
        index_name (str): The attribute name to use for the index. Defaults to '__index__'.

    Returns:
        str: Modified HTML content with unique index attributes added to each tag.

    Examples:
        >>> sample_html = "<div><p>Hello</p><p>World</p></div>"
        >>> modified_html = add_unique_index_to_html(sample_html)
        >>> print(modified_html)
        <div __index__="0"><p __index__="1">Hello</p><p __index__="2">World</p></div>

        This example demonstrates how each tag in the HTML string is assigned a unique index based on the order it appears,
        using the default index name '__index__'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    index = 0  # Initialize a counter
    for element in soup.descendants:
        if element.name is not None:  # Check if it is a tag and not a string
            element[index_name] = str(index)
            index += 1

    return str(soup)


DEFAULT_HTML_CLEAN_TAGS_TO_KEEP = (
    'a', 'button', 'input', 'ul', 'ol', 'li'
)

DFAULT_HTML_CLEAN_TAGS_TO_REMOVE = ('script',)

DEFAULT_HTML_CLEAN_ATTRIBUTE_TO_KEEP = ('class', 'href', '*name', '*label')


def clean_html(html_content, tags_to_keep=DEFAULT_HTML_CLEAN_TAGS_TO_KEEP, tags_to_remove=DFAULT_HTML_CLEAN_TAGS_TO_REMOVE, attributes_to_keep: Union[str, Iterable[str]] = DEFAULT_HTML_CLEAN_ATTRIBUTE_TO_KEEP, keep_elements_with_immediate_text=True):
    """
    Cleans HTML content by selectively preserving and removing specified elements and attributes,
    and can conditionally keep direct text of non-kept elements.

    Args:
        html_content (str): The HTML content to clean.
        tags_to_keep (list of str): Tags that should be preserved in the HTML.
        tags_to_remove (list of str): Tags that should be removed from the HTML.
        attributes_to_keep (list of str): Attributes that should be preserved on the retained tags.
        keep_elements_with_immediate_text (bool): If True, elements not in `tags_to_keep` will be
            removed but their direct text will be kept. If False, such elements will be completely removed.

    Returns:
        str: The cleaned HTML content as a string.

    Examples:
        >>> example_html = "<div><a href='http://example.com'>Link</a><script>alert('Hi');</script></div>"
        >>> clean_html(example_html, ['a'], ['script'], ['href'], True)
        '<a href="http://example.com">Link</a>'

        >>> example_html = "<div>Hello <span>World</span><script>Code()</script></div>"
        >>> clean_html(example_html, [], ['script'], [], True)
        '<div>Hello <span>World</span></div>'

        >>> example_html = "<div><span>More text</span></div>"
        >>> clean_html(example_html, [], [], [], False)
        ''

        >>> complex_html = "<article>" + \\
        ...     "<header>" + \\
        ...     "<h1>Blog Title</h1>" + \\
        ...     "<p>Published on <time datetime='2023-10-01'>October 1, 2023</time></p>" + \\
        ...     "</header>" + \\
        ...     "<section>" + \\
        ...     "<h2>Introduction</h2>" + \\
        ...     "<p>This is a <strong>great</strong> article about <a href='http://example.com'>example topics</a>.</p>" + \\
        ...     "</section>" + \\
        ...     "<aside>" + \\
        ...     "<h3>About the Author</h3>" + \\
        ...     "<p>Author Name is a renowned writer in areas such as technology and science.</p>" + \\
        ...     "</aside>" + \\
        ...     "<footer>" + \\
        ...     "<p>Contact information: <a href='mailto:info@example.com'>info@example.com</a></p>" + \\
        ...     "<ul>" + \\
        ...     "<li>Privacy Policy</li>" + \\
        ...     "<li>Terms of Use</li>" + \\
        ...     "</ul>" + \\
        ...     "</footer>" + \\
        ...     "</article>"
        >>> clean_html(complex_html, ['a', 'h1', 'h2'], [], ['href'], True)
        '<h1>Blog Title</h1><p>Published on <time>October 1, 2023</time></p><h2>Introduction</h2><p>This is a <strong>great</strong> article about <a href="http://example.com">example topics</a>.</p><h3>About the Author</h3><p>Author Name is a renowned writer in areas such as technology and science.</p><p>Contact information: <a href="mailto:info@example.com">info@example.com</a></p><li>Privacy Policy</li><li>Terms of Use</li>'


    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove explicitly unwanted tags
    for tag in tags_to_remove:
        [element.decompose() for element in soup.find_all(tag)]

    # Process all elements
    for element in list(soup.find_all()):
        if element.name in tags_to_keep:
            keep_specified_attributes(element, attributes_to_keep)
        elif has_immediate_text(element):
            if keep_elements_with_immediate_text:
                keep_specified_attributes(element, attributes_to_keep)
            else:
                remove_immediate_text(element)
                element.unwrap()
        else:
            element.unwrap()

    return str(soup)
