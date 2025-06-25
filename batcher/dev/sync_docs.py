#!/usr/bin/env python3

"""Propagating changes in "raw" documentation to the files comprising the
end-user documentation.

Care must be taken to select only files that should not be updated manually,
because any previous updates to such files are discarded.
"""

import os
import shutil

from src import utils

utils.initialize_i18n()

from dev import preprocess_document_contents
from src import constants


DEV_DIRPATH = os.path.abspath(os.path.dirname(utils.get_current_module_filepath()))
ROOT_DIRPATH = os.path.dirname(os.path.dirname(DEV_DIRPATH))

PATHS_TO_PREPROCESS_FILEPATH = os.path.join(DEV_DIRPATH, 'sync_docs_files_to_preprocess.txt')
PATHS_TO_COPY_FILEPATH = os.path.join(DEV_DIRPATH, 'sync_docs_files_to_copy.txt')


def main():
  sync_files(get_filepaths(PATHS_TO_PREPROCESS_FILEPATH), get_filepaths(PATHS_TO_COPY_FILEPATH))


def sync_files(filepaths_to_preprocess, filepaths_to_copy):
  preprocess_document_contents.main(filepaths_to_preprocess)
  
  for source_filepath, dest_filepath in filepaths_to_copy:
    shutil.copy2(source_filepath, dest_filepath)


def get_filepaths(file_list_filepath):
  """Returns a dictionary of `{source_path: destination_path}` pairs.
  
  ``file_list_filepath`` is a file containing newline-separated pairs of file or
  directory paths. The first path in the pair represents a "raw", unprocessed
  file or directory with unprocessed files, and the second path represents the
  processed file or directory with files.
  
  Empty lines from ``file_list_filepath`` are ignored.
  """
  
  def _list_filepaths(dirpath):
    listed_filepaths = []
    
    for root_dirpath, _unused, filepaths in os.walk(dirpath):
      for filepath in filepaths:
        listed_filepaths.append(os.path.normpath(os.path.join(root_dirpath, filepath)))
        
    return listed_filepaths
  
  def _replace_path_part(path, part_to_replace, replacement, path_root_):
    processed_path = os.path.relpath(os.path.join(path_root_, path), path_root_)
    processed_path = processed_path.replace(part_to_replace, replacement, 1)
    processed_path = os.path.join(path_root_, processed_path)
    return processed_path
  
  with open(file_list_filepath, 'r', encoding=constants.TEXT_FILE_ENCODING) as f:
    lines = f.readlines()
  
  lines = [line.strip() for line in lines if line.strip()]
  
  source_paths = [os.path.normpath(line) for line in lines[::2]]
  dest_paths = [os.path.normpath(line) for line in lines[1::2]]
  path_root = ROOT_DIRPATH
  
  paths_to_sync = []
  
  for source_path, dest_path in zip(source_paths, dest_paths):
    full_source_path = os.path.join(path_root, source_path)
    full_dest_path = os.path.join(path_root, dest_path)
    
    if os.path.isfile(full_source_path):
      paths_to_sync.append((full_source_path, full_dest_path))
    elif os.path.isdir(full_source_path) and os.path.isdir(full_dest_path):
      listed_source_filepaths = _list_filepaths(full_source_path)
      listed_dest_filepaths = [
        _replace_path_part(listed_source_filepath, source_path, dest_path, path_root)
        for listed_source_filepath in listed_source_filepaths]
      
      paths_to_sync.extend(zip(listed_source_filepaths, listed_dest_filepaths))
    else:
      continue
  
  return paths_to_sync


if __name__ == '__main__':
  main()
