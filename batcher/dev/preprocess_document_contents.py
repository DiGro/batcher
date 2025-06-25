#!/usr/bin/env python3

"""Pre-processing of documents (HTML pages, plain text files), replacing lines
containing a Liquid-style tag and its arguments with the corresponding content.

Usage:

    <script name> <source file paths> <destination file paths>

Each file from the list of source file paths must have a counterpart in the
destination file paths list. The length of the two lists thus must be identical.

The following tags can be specified in the documents:
* ``{% include-section <relative file path> <arguments>... %}``:
  Replace the entire line containing this expression with the contents of the
  specified file.
  
  Optional arguments to ``include-section``:
  * ``section=<section name>`` - Instead of the entire contents, insert only
    the contents from the section <section name>. A section is a valid
    Markdown section heading (underlining headers with ``'='`` or ``'-'``,
    or using leading ``'#'``s separated from headers by a single space).
  * ``sentences=<index number>`` or ``sentences=<start index:end index>`` - pick
    chosen sentence(s) from sections by indexes using the Python slice notation.
    Index starts from 0.
  * ``no-header=(True | False)`` - exclude section header. ``False`` by default.
    If no section is specified, the first section header is ignored.
  
  Examples:

      {% include-section 'docs/README.md' section=Features no-header=True %}
      {% include-section 'docs/README.md' section='Known Issues' %}
      {% include-section 'docs/README.md' section=License sentences=0 %}

* ``{% include-config <configuration entry> %}``:
  Replace the expression with the corresponding configuration entry in
  the ``config`` module. If no such entry is found, the expression is not
  replaced.
  
  Example: ``{% include-config 'PLUGIN_NAME' %}`` will insert a configuration
  entry titled ``'PLUGIN_NAME'``, e.g. ``'batcher'``.
"""

import abc
import os
import re
import sys

from src import utils

utils.initialize_i18n()

from config import CONFIG
from src import constants


def main(source_and_dest_filepaths):
  preprocess_contents(source_and_dest_filepaths)


def preprocess_contents(source_and_dest_filepaths):
  for source_filepath, dest_filepath in source_and_dest_filepaths:
    if not os.path.isfile(source_filepath):
      print(f'Warning: Input path "{source_filepath}" does not exist or is not a file')
      continue
    
    with open(source_filepath, 'r', encoding=constants.TEXT_FILE_ENCODING) as f:
      source_file_contents = f.read()
    
    preprocessed_contents = source_file_contents
    
    for tag_name, tag_class in _TAGS.items():
      tag = tag_class(source_filepath, _TAG_MATCHING_REGEXES[tag_name])
      try:
        preprocessed_contents = _preprocess_contents(tag, preprocessed_contents)
      except DocumentNotFoundError as e:
        print(str(e))
    
    with open(dest_filepath, 'w', encoding=constants.TEXT_FILE_ENCODING) as f:
      f.writelines(preprocessed_contents)


def _preprocess_contents(tag, file_contents):
  for match in list(re.finditer(tag.matching_regex, file_contents)):
    tag_args = parse_args(tag.get_args_from_match(match))
    tag.process_args(tag_args['args'], tag_args['optional_args'])
    
    new_contents = tag.get_contents()
    file_contents = file_contents.replace(
      tag.get_match_to_be_replaced(match), new_contents, 1)
  
  return file_contents


def parse_args(args_str):
  quote_char = "'"
  optional_arg_separator_char = '='
  
  def _parse_optional_arg(args_str_to_parse_, optional_arg_name_match_):
    optional_arg_name_ = args_str_to_parse_[:optional_arg_name_match_.end(1)]
    args_str_to_parse_ = args_str_to_parse_[optional_arg_name_match_.end(1) + 1:]
    
    optional_arg_value_with_quotes_match = (
      re.search(quote_char + r'(.+?)' + quote_char + r'(\s|$)', args_str_to_parse_))
    
    if optional_arg_value_with_quotes_match is not None:
      optional_arg_value_ = optional_arg_value_with_quotes_match.group(1)
      args_str_to_parse_ = (
        args_str_to_parse_[optional_arg_value_with_quotes_match.end(1) + 1:].lstrip())
    else:
      optional_arg_value_without_quotes_match = (
        re.search(r'(.+?)(\s|$)', args_str_to_parse_))
      
      if optional_arg_value_without_quotes_match is not None:
        optional_arg_value_ = optional_arg_value_without_quotes_match.group(1)
        args_str_to_parse_ = (
          args_str_to_parse_[optional_arg_value_without_quotes_match.end(1) + 1:].lstrip())
      else:
        raise ValueError(f'missing value for optional argument "{optional_arg_name_}"')
    
    return args_str_to_parse_, optional_arg_name_, optional_arg_value_
  
  parsed_args = {'args': [], 'optional_args': {}}
  
  args_str = args_str.strip()
  args_str_to_parse = args_str
  
  while args_str_to_parse:
    if args_str_to_parse[0] == quote_char:
      args_str_to_parse = args_str_to_parse[1:]
      
      end_quote_index = args_str_to_parse.find(quote_char)
      if end_quote_index != -1:
        parsed_args['args'].append(args_str_to_parse[:end_quote_index])
        args_str_to_parse = args_str_to_parse[end_quote_index + 1:].lstrip()
      else:
        raise ValueError(f'missing closing "{quote_char}": {args_str}')
    else:
      optional_arg_name_match = (
        re.search(r'^(\S+?)' + optional_arg_separator_char, args_str_to_parse))
      
      if optional_arg_name_match is not None:
        args_str_to_parse, optional_arg_name, optional_arg_value = (
          _parse_optional_arg(args_str_to_parse, optional_arg_name_match))
        parsed_args['optional_args'][optional_arg_name] = optional_arg_value
      else:
        space_or_end_match = re.search(r'(.+?)(\s+|$)', args_str_to_parse)
        
        if space_or_end_match is not None:
          next_space_index = space_or_end_match.end(1)
          parsed_args['args'].append(args_str_to_parse[:next_space_index])
          args_str_to_parse = args_str_to_parse[next_space_index:].lstrip()
        else:
          args_str_to_parse = ''
  
  return parsed_args


class DocumentNotFoundError(Exception):
  pass


class CustomLiquidTag(metaclass=abc.ABCMeta):
  
  def __init__(self, source_filepath, matching_regex):
    self.source_filepath = source_filepath
    self.matching_regex = matching_regex
    
    self.args = []
    self.optional_args = {}
  
  @abc.abstractmethod
  def get_args_from_match(self, match):
    pass
  
  @abc.abstractmethod
  def get_match_to_be_replaced(self, match):
    pass
  
  @abc.abstractmethod
  def process_args(self, args, optional_args):
    pass
  
  @abc.abstractmethod
  def get_contents(self):
    pass
  

class IncludeSectionTag(CustomLiquidTag):
  
  def get_args_from_match(self, match):
    return match.group(3)
  
  def get_match_to_be_replaced(self, match):
    return match.group(2)
  
  def process_args(self, args, optional_args):
    self.args = [self._process_filepath_arg(args[0])]
    self.optional_args = self._process_optional_args(optional_args)
  
  def get_contents(self):
    document_filepath = self.args[0]
    section_name = self.optional_args['section']
    
    if not os.path.isfile(document_filepath):
      raise DocumentNotFoundError(
        (f'Document path "{document_filepath}" inside "{self.source_filepath}" does not'
         ' exist or is not a file'))
    
    with open(document_filepath, 'r', encoding=constants.TEXT_FILE_ENCODING) as f:
      document_contents = f.read()
      if section_name:
        section_header, section_contents = find_section(document_contents, section_name)
      elif not section_name and self.optional_args['no-header']:
        section_header, section_contents = find_section(
          document_contents, section_name, get_contents_if_section_name_empty=True)
      else:
        section_header, section_contents = '', document_contents
    
    section_header, section_contents = self._get_sentences_from_section(
      section_header, section_contents, self.optional_args['sentences'])
    
    section_header, section_contents = self._strip_section_header(
      section_header, section_contents, self.optional_args['no-header'])
    
    return section_header + section_contents
  
  def _process_filepath_arg(self, relative_filepath):
    return os.path.normpath(
      os.path.join(os.path.dirname(self.source_filepath), relative_filepath))
  
  def _process_optional_args(self, optional_args):
    return {
      'section': optional_args.get('section', ''),
      'sentences': self._parse_sentence_indices(optional_args.get('sentences', '')),
      'no-header': self._parse_bool_from_str(optional_args.get('no-header', 'False')),
    }
  
  @staticmethod
  def _parse_sentence_indices(arg_str):
    if not arg_str:
      return []
    
    sentence_indices_str = arg_str.split(':')[:2]
    sentence_indices = []
    for index_str in sentence_indices_str:
      try:
        index = int(index_str)
      except (ValueError, TypeError):
        index = None
      sentence_indices.append(index)
    
    return sentence_indices
  
  @staticmethod
  def _parse_bool_from_str(arg_str):
    return arg_str.lower() == 'true'
  
  @staticmethod
  def _get_sentences_from_section(section_header, section_contents, sentence_indices):
    if sentence_indices:
      sentences = re.split(r'\.[ \n]', section_contents)
      
      if len(sentence_indices) == 1:
        section_sentences = sentences[sentence_indices[0]].strip()
        if not section_sentences.endswith('.'):
          section_sentences += '.'
        
        return section_header, section_sentences
      elif len(sentence_indices) == 2:
        section_sentences = '. '.join(
          sentence.strip()
          for sentence in sentences[sentence_indices[0]:sentence_indices[1]])
        
        if not section_sentences.endswith('.'):
          section_sentences += '.'
        
        return section_header, section_sentences
    
    return section_header, section_contents
  
  @staticmethod
  def _strip_section_header(section_header, section_contents, should_strip_header):
    if should_strip_header:
      return '', section_contents
    else:
      return section_header, section_contents


def find_section(contents, section_name=None, get_contents_if_section_name_empty=False):
  
  def _get_section_contents(contents_, start_of_section_contents_, end_of_section_header_):
    next_section_match_regex = (
      '\n'
      + '('
      + r'#+ .*?\n'
      + '|'
      + r'.*?\n[=-]+\n'
      + ')')
    next_section_match = re.search(next_section_match_regex, contents_[start_of_section_contents_:])
    
    if next_section_match:
      start_of_next_section_header = next_section_match.start(1)
      end_of_section_contents = start_of_section_contents_ + start_of_next_section_header - 1
      
      return contents_[end_of_section_header_:end_of_section_contents]
    else:
      return contents_[end_of_section_header_:]
  
  section_header = ''
  section_contents = ''
  
  if section_name:
    section_name_pattern = re.escape(section_name)
  else:
    section_name_pattern = r'.*?'
  
  section_match_regex = (
    r'(^|\n)'
    + '('
    + '(' + section_name_pattern + ')' + r'\n[=-]+\n'
    + '|'
    + r'#+ ' + '(' + section_name_pattern + ')' + r'\n'
    + ')')
  
  section_match = re.search(section_match_regex, contents)
  if section_match:
    start_of_section_header = section_match.start(2)
    end_of_section_header = section_match.end(2)
    
    start_of_section_contents = end_of_section_header + 1
    
    section_header = contents[start_of_section_header:end_of_section_header]
    
    if section_name or not get_contents_if_section_name_empty:
      section_contents = _get_section_contents(
        contents, start_of_section_contents, end_of_section_header)
    else:
      section_contents = contents[end_of_section_header:]
  
  section_contents = section_contents.rstrip('\n')
  
  return section_header, section_contents


class IncludeConfigTag(CustomLiquidTag):
  
  def get_args_from_match(self, match):
    return match.group(2)
  
  def get_match_to_be_replaced(self, match):
    return match.group(1)
  
  def process_args(self, args, optional_args):
    self.args = args
  
  def get_contents(self):
    return getattr(CONFIG, self.args[0], '') if self.args else ''


_TAGS = {
  'include-section': IncludeSectionTag,
  'include-config': IncludeConfigTag,
}

_TAG_MATCHING_REGEXES = {
  'include-section': r'( *)(\{% include-section (.*?) %\})',
  'include-config': r'(\{% include-config (.*?) %\})',
}


if __name__ == '__main__':
  main(sys.argv[1])
