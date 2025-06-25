"""Test cases for Convert. Requires GIMP to be running."""

import inspect
import os
import shutil
import unittest

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio

from config import CONFIG
from src import builtin_actions
from src import commands
from src import core
from src import itemtree
from src import plugin_settings
from src import utils
from src import utils_pdb
from src import utils_setting as utils_setting_
from src.procedure_groups import *
from src.pypdb import pdb


_CURRENT_MODULE_DIRPATH = os.path.dirname(os.path.abspath(utils.get_current_module_filepath()))
TEST_IMAGES_DIRPATH = os.path.join(_CURRENT_MODULE_DIRPATH, 'test_images')
INPUT_IMAGES_DIRPATH = os.path.join(TEST_IMAGES_DIRPATH, 'convert_inputs')

DEFAULT_EXPECTED_RESULTS_DIRPATH = os.path.join(TEST_IMAGES_DIRPATH, 'convert_expected_results')
OUTPUT_DIRPATH = os.path.join(TEST_IMAGES_DIRPATH, 'temp_output')
INCORRECT_RESULTS_DIRPATH = os.path.join(TEST_IMAGES_DIRPATH, 'incorrect_results')


class TestConvertCompareContents(unittest.TestCase):
  
  @classmethod
  def setUpClass(cls):
    CONFIG.PROCEDURE_GROUP = CONVERT_GROUP

    Gimp.context_push()

    cls.test_images_filepaths = sorted(
      os.path.join(INPUT_IMAGES_DIRPATH, filename) for filename in os.listdir(INPUT_IMAGES_DIRPATH))

    cls.output_dirpath = OUTPUT_DIRPATH
    
    if os.path.exists(cls.output_dirpath):
      shutil.rmtree(cls.output_dirpath)
    
    if os.path.exists(INCORRECT_RESULTS_DIRPATH):
      shutil.rmtree(INCORRECT_RESULTS_DIRPATH)

    gimp_version = '-'.join(
      str(version_number_part) for version_number_part in cls._get_gimp_version_as_tuple()[:2]
    )

    version_specific_expected_results_dirpath = (
      f'{DEFAULT_EXPECTED_RESULTS_DIRPATH}_{gimp_version}')
    
    if os.path.isdir(version_specific_expected_results_dirpath):
      cls.expected_results_root_dirpath = version_specific_expected_results_dirpath
    else:
      cls.expected_results_root_dirpath = DEFAULT_EXPECTED_RESULTS_DIRPATH
  
  @classmethod
  def tearDownClass(cls):
    Gimp.context_pop()

    CONFIG.PROCEDURE_GROUP = CONFIG.PLUGIN_NAME
  
  def tearDown(self):
    if os.path.exists(self.output_dirpath):
      shutil.rmtree(self.output_dirpath)
  
  def test_default_settings(self):
    self.compare(
      expected_results_dirpath=os.path.join(self.expected_results_root_dirpath, 'default'),
    )
  
  def test_remove_folder_structure(self):
    self.compare(
      action_names_to_add={'remove_folder_structure': None},
      expected_results_dirpath=os.path.join(
        self.expected_results_root_dirpath, 'remove_folder_structure'),
    )

  def compare(
        self,
        action_names_to_add=None,
        action_names_to_remove=None,
        expected_results_dirpath=None,
  ):
    settings = plugin_settings.create_settings_for_convert()
    settings['main/output_directory'].set_value(Gio.file_new_for_path(self.output_dirpath))
    settings['main/file_extension'].set_value('png')

    if expected_results_dirpath is None:
      expected_results_dirpath = os.path.join(self.expected_results_root_dirpath, 'default')

    expected_image_filepaths = sorted(
      os.path.join(root, filename)
      for root, _dirnames, filenames in os.walk(expected_results_dirpath)
      for filename in filenames
    )
    expected_images = {
      filepath: self._load_image(filepath)
      for filepath in expected_image_filepaths
    }

    self._export(settings, action_names_to_add, action_names_to_remove)

    actual_image_filepaths = sorted(
      os.path.join(root, filename)
      for root, _dirnames, filenames in os.walk(self.output_dirpath)
      for filename in filenames
    )
    actual_images = {
      filepath: self._load_image(filepath)
      for filepath in actual_image_filepaths
    }
    
    for expected_image, actual_image in zip(expected_images.values(), actual_images.values()):
      test_case_name = inspect.stack()[1][-3]
      self._compare_images(
        actual_image,
        expected_image,
        settings,
        test_case_name)

    for image in expected_images.values():
      image.delete()

    for image in actual_images.values():
      image.delete()

  def _export(
        self,
        settings,
        action_names_to_add,
        action_names_to_remove,
  ):
    if action_names_to_add is None:
      action_names_to_add = {}
    
    if action_names_to_remove is None:
      action_names_to_remove = []
    
    for action_name, order in action_names_to_add.items():
      commands.add(
        settings['main/actions'],
        builtin_actions.BUILTIN_ACTIONS[action_name])
      if order is not None:
        commands.reorder(settings['main/actions'], action_name, order)
    
    for action_name in action_names_to_remove:
      if action_name in settings['main/actions']:
        commands.remove(settings['main/actions'], action_name)

    item_tree = itemtree.ImageFileTree()
    item_tree.add(self.test_images_filepaths)

    batcher = core.ImageBatcher(
      item_tree=item_tree,
      actions=settings['main/actions'],
      conditions=settings['main/conditions'],
      initial_export_run_mode=Gimp.RunMode.NONINTERACTIVE,
    )
    
    batcher.run(**utils_setting_.get_settings_for_batcher(settings['main']))
    
    for action_name in action_names_to_add:
      commands.remove(settings['main/actions'], action_name)
  
  def _compare_images(self, actual_image, expected_image, settings, test_case_name):
    actual_layer = actual_image.get_layers()[0]
    expected_layer = actual_image.get_layers()[0]

    comparison_result = utils_pdb.compare_layers([actual_layer, expected_layer])

    if not comparison_result:
      self._save_incorrect_image(actual_image, expected_image, settings, test_case_name)
    
    self.assertEqual(
      comparison_result,
      True,
      msg=(
        'Images are not identical:'
        f'\nprocessed image: {actual_image.get_name()}'
        f'\nexpected image: {expected_image.get_name()}'))
  
  def _save_incorrect_image(self, actual_image, expected_image, settings, test_case_name):
    incorrect_images_dirpath = os.path.join(INCORRECT_RESULTS_DIRPATH, test_case_name)
    os.makedirs(incorrect_images_dirpath, exist_ok=True)
    
    self._copy_incorrect_image(actual_image, settings, incorrect_images_dirpath, '_actual')
    self._copy_incorrect_image(expected_image, settings, incorrect_images_dirpath, '_expected')

  @staticmethod
  def _copy_incorrect_image(image, settings, incorrect_images_dirpath, filename_suffix):
    image_filename = os.path.basename(image.get_name())
    image_filename_root = os.path.splitext(image_filename)[0]

    image_output_filename = (
      f'{image_filename_root}{filename_suffix}.{settings["main/file_extension"].value}')
    
    shutil.copy(
      image_filename,
      os.path.join(incorrect_images_dirpath, image_output_filename))
  
  @classmethod
  def _load_image(cls, image_filepath):
    return pdb.gimp_file_load(
      run_mode=Gimp.RunMode.NONINTERACTIVE, file=Gio.file_new_for_path(image_filepath))

  @staticmethod
  def _get_gimp_version_as_tuple():
    return Gimp.MAJOR_VERSION, Gimp.MINOR_VERSION, Gimp.MICRO_VERSION
