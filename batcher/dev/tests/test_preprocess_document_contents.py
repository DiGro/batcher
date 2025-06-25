import unittest
import unittest.mock as mock

import parameterized

from config import CONFIG
from dev import preprocess_document_contents


class TestParseArgs(unittest.TestCase):
  
  @parameterized.parameterized.expand([
    ['single_arg',
     'README.md',
     {'args': ['README.md'], 'optional_args': {}}],
    ['single_arg_with_quotes',
     "'README.md'",
     {'args': ['README.md'], 'optional_args': {}}],
    ['single_arg_with_spaces_with_quotes',
     "'My README.md'",
     {'args': ['My README.md'], 'optional_args': {}}],
    ['multiple_args',
     'README.md CHANGELOG.md',
     {'args': ['README.md', 'CHANGELOG.md'], 'optional_args': {}}],
    ['multiple_args_with_spaces_with_quotes',
     "'My README.md' CHANGELOG.md",
     {'args': ['My README.md', 'CHANGELOG.md'], 'optional_args': {}}],
    ['multiple_args_with_multiple_spaces_with_quotes',
     "'My README.md'  CHANGELOG.md",
     {'args': ['My README.md', 'CHANGELOG.md'], 'optional_args': {}}],
    ['multiple_args_with_spaces_with_quotes_as_second_arg',
     "CHANGELOG.md 'My README.md'",
     {'args': ['CHANGELOG.md', 'My README.md'], 'optional_args': {}}],
    ['single_optional_arg',
     'section=Features',
     {'args': [], 'optional_args': {'section': 'Features'}}],
    ['single_optional_arg_with_spaces_and_quotes',
     "section='Known Issues'",
     {'args': [], 'optional_args': {'section': 'Known Issues'}}],
    ['single_arg_single_optional_arg',
     'README.md section=Features',
     {'args': ['README.md'], 'optional_args': {'section': 'Features'}}],
    ['single_arg_single_optional_arg_with_spaces_and_quotes',
     "README.md section='Known Issues'",
     {'args': ['README.md'], 'optional_args': {'section': 'Known Issues'}}],
    ['single_arg_multiple_optional_args',
     'README.md section=Features sentences=0',
     {'args': ['README.md'], 'optional_args': {'section': 'Features', 'sentences': '0'}}],
    ['single_arg_multiple_optional_args_with_spaces_and_quotes',
     "README.md section='Known Issues' sentences=0",
     {'args': ['README.md'],
      'optional_args': {'section': 'Known Issues', 'sentences': '0'}}],
    ['multiple_args_multiple_optional_args_with_spaces_and_quotes',
     "README.md CHANGELOG.md section='Known Issues' sentences=0",
     {'args': ['README.md', 'CHANGELOG.md'],
      'optional_args': {'section': 'Known Issues', 'sentences': '0'}}],
    ['multiple_args_with_spaces_and_quotes_multiple_optional_args_with_quotes',
     "'My README.md' CHANGELOG.md section='Known Issues' sentences=0",
     {'args': ['My README.md', 'CHANGELOG.md'],
      'optional_args': {'section': 'Known Issues', 'sentences': '0'}}],
  ])
  def test_parse_args(self, _test_case_suffix, args_str, expected_parsed_args):
    parsed_args = preprocess_document_contents.parse_args(args_str)
    self.assertDictEqual(parsed_args, expected_parsed_args)


class TestIncludeSectionTag(unittest.TestCase):
  
  _TEST_SECTION_HEADERS = {
    'translations': """## Translations""",
    'known_issues': """## Known Issues""",
  }
  
  _TEST_SECTION_CONTENTS = {
    'translations': """If you would like to provide translations, see
[TRANSLATIONS](TRANSLATIONS.md) for instructions.""",
    'known_issues': [
      """Sometimes, after you hit the Export button, it may seem as though
nothing happens.""",
      """In that case, the file format dialog may be displayed behind GIMP.""",
      """If so, simply select the dialog to bring it up.""",
      """Several users reported crashes on Windows and macOS when clicking on the
menu entries.""",
      """If the crashes occur to you, try reinstalling GIMP."""],
  }
  
  _TEST_FILE_INTRO = """This is an awesome [GIMP](https://www.gimp.org/)
plug-in."""
  
  _TEST_FILE_CONTENTS = """{}

{}

{}

{}

{}

{}
""".format(
      _TEST_FILE_INTRO,
      _TEST_SECTION_HEADERS['translations'],
      _TEST_SECTION_CONTENTS['translations'],
      _TEST_SECTION_HEADERS['known_issues'],
      ' '.join(_TEST_SECTION_CONTENTS['known_issues'][:2]),
      ' '.join(_TEST_SECTION_CONTENTS['known_issues'][2:]))
  
  _TEST_SOURCE_FILEPATH = 'test_filepath'
  _TEST_MATCHING_REGEX = r'( *)(\{% include-section (.*?) %\})'
  
  _TEST_FILEPATH_WITH_SECTIONS = 'sections/README.md'
  
  @parameterized.parameterized.expand([
    ['no_optional_args', {}, _TEST_FILE_CONTENTS],
    ['no_header_False', {'no-header': 'False'}, _TEST_FILE_CONTENTS],
    ['no_header_True',
     {'no-header': 'True'},
     """
{}

{}

{}

{}""".format(
      _TEST_SECTION_CONTENTS['translations'],
      _TEST_SECTION_HEADERS['known_issues'],
      ' '.join(_TEST_SECTION_CONTENTS['known_issues'][:2]),
      ' '.join(_TEST_SECTION_CONTENTS['known_issues'][2:]))],
    ['no_header_invalid', {'no-header': 'something'}, _TEST_FILE_CONTENTS],
    ['section_with_header',
     {'section': 'Translations', 'no-header': 'False'},
     _TEST_SECTION_HEADERS['translations']
     + '\n\n' + _TEST_SECTION_CONTENTS['translations']],
    ['section_without_header',
     {'section': 'Translations', 'no-header': 'True'},
     '\n' + _TEST_SECTION_CONTENTS['translations']],
    ['section_with_single_sentence_first',
     {'section': 'Known Issues', 'sentences': '0'},
     _TEST_SECTION_HEADERS['known_issues']
     + '\n' + _TEST_SECTION_CONTENTS['known_issues'][0]],
    ['section_with_single_sentence_middle',
     {'section': 'Known Issues', 'sentences': '2'},
     _TEST_SECTION_HEADERS['known_issues']
     + '\n' + _TEST_SECTION_CONTENTS['known_issues'][2]],
    ['section_with_single_sentence_last',
     {'section': 'Known Issues', 'sentences': '-1'},
     _TEST_SECTION_HEADERS['known_issues']
     + '\n' + _TEST_SECTION_CONTENTS['known_issues'][-1]],
    ['section_with_multiple_sentences_from_beginning',
     {'section': 'Known Issues', 'sentences': '0:2'},
     _TEST_SECTION_HEADERS['known_issues']
     + '\n' + ' '.join(_TEST_SECTION_CONTENTS['known_issues'][0:2])],
    ['section_with_multiple_sentences_in_middle',
     {'section': 'Known Issues', 'sentences': '1:3'},
     _TEST_SECTION_HEADERS['known_issues']
     + '\n' + ' '.join(_TEST_SECTION_CONTENTS['known_issues'][1:3])],
  ])
  @mock.patch('dev.preprocess_document_contents.os.path.isfile')
  @mock.patch('dev.preprocess_document_contents.open')
  def test_include_section(
        self,
        _test_case_suffix,
        optional_args,
        expected_contents,
        mock_open,
        mock_os_path_isfile):
    mock_os_path_isfile.return_value = True
    
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.read.side_effect = lambda: self._TEST_FILE_CONTENTS
    
    tag = preprocess_document_contents.IncludeSectionTag(
      self._TEST_SOURCE_FILEPATH, self._TEST_MATCHING_REGEX)
    
    tag.process_args([self._TEST_FILEPATH_WITH_SECTIONS], optional_args)
    
    self.assertEqual(tag.get_contents(), expected_contents)


class TestIncludeConfigTag(unittest.TestCase):
  
  _TEST_SOURCE_FILEPATH = 'test_filepath'
  _TEST_MATCHING_REGEX = r'(\{% include-config (.*?) %\})'
  
  @parameterized.parameterized.expand([
    ['no_argument', [], ''],
    ['valid_config_entry', ['PLUGIN_VERSION'], '1.0'],
    ['invalid_config_entry', ['ENTRY_THAT_DOES_NOT_EXIST'], ''],
  ])
  def test_include_config(self, _test_case_suffix, args, expected_contents):
    if args and hasattr(CONFIG, args[0]):
      setattr(CONFIG, args[0], expected_contents)

    tag = preprocess_document_contents.IncludeConfigTag(
      self._TEST_SOURCE_FILEPATH, self._TEST_MATCHING_REGEX)
    
    tag.process_args(args, {})
    
    self.assertEqual(tag.get_contents(), expected_contents)
