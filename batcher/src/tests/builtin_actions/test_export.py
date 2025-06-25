import unittest
import unittest.mock as mock

import gi

gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import Gio
from gi.repository import GObject

from src import builtin_actions
from src import file_formats as file_formats_
from src import setting as setting_
from src.pypdb import pdb

from src.tests import stubs_gimp


@mock.patch('src.pypdb.Gimp', new_callable=stubs_gimp.GimpModuleStub)
@mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
class TestExport(unittest.TestCase):

  @mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
  def setUp(self, mock_get_setting_data_from_pdb_procedure):
    self.common_options = [
      {
        'name': 'run-mode',
        'type': setting_.EnumSetting,
        'default_value': Gimp.RunMode.NONINTERACTIVE,
        'enum_type': Gimp.RunMode.__gtype__,
        'display_name': 'run-mode',
      },
      {
        'name': 'image',
        'type': setting_.ImageSetting,
        'default_value': None,
        'display_name': 'image',
      },
      {
        'name': 'file',
        'type': setting_.FileSetting,
      },
      {
        'name': 'options',
        'type': setting_.ExportOptionsSetting,
        'default_value': None,
        'display_name': 'options',
      },
    ]

    self.png_options = [
      {
        'name': 'offsets',
        'type': setting_.ArraySetting,
        'element_type': setting_.IntSetting,
        'display_name': 'Offsets',
        'default_value': (7, 11),
      },
      {
        'name': 'is-interlaced',
        'type': setting_.BoolSetting,
        'display_name': 'interlaced',
        'default_value': False,
      },
    ]

    self.file_format_options = [
      *self.common_options,
      *self.png_options,
    ]

    self.procedure_name = 'file-png-export'
    self.procedure_stub_kwargs = dict(
      name=self.procedure_name,
      arguments_spec=[
        dict(value_type=Gimp.RunMode.__gtype__, name='run-mode', blurb='The run mode'),
        dict(value_type=Gimp.Image, name='image', blurb='Image'),
        dict(value_type=Gio.File, name='file', blurb='File to save the image in'),
        dict(value_type=Gimp.ExportOptions, name='options', blurb='Export options'),
        dict(value_type=Gimp.Int32Array, name='offsets'),
        dict(value_type=GObject.TYPE_BOOLEAN, name='is-interlaced'),
      ],
    )
    self.procedure = stubs_gimp.Procedure(**self.procedure_stub_kwargs)

    builtin_actions._export.pdb.remove_from_cache(self.procedure_name)
    file_formats_.pdb.remove_from_cache(self.procedure_name)

  def test_get_export_function(self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    self._test_get_export_function(mock_get_setting_data_from_pdb_procedure, mock_gimp)

  def test_get_export_function_with_fewer_common_options(
        self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    self.file_format_options = [
      *self.common_options[:-1],
      *self.png_options,
    ]

    self._test_get_export_function(mock_get_setting_data_from_pdb_procedure, mock_gimp)

  def _test_get_export_function(self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    mock_get_setting_data_from_pdb_procedure.return_value = (
      None, 'file-png-export', self.file_format_options)
    mock_gimp.get_pdb().add_procedure(self.procedure)

    file_format_options = {}

    # noinspection PyTypeChecker
    proc, kwargs = builtin_actions.get_export_function(
      'png', builtin_actions.FileFormatModes.USE_EXPLICIT_VALUES, file_format_options)

    self.assertIs(proc, pdb.file_png_export)
    mock_get_setting_data_from_pdb_procedure.assert_called_once()
    self.assertEqual(len(file_format_options['png']), 2)
    self.assertEqual(file_format_options['png']['is-interlaced'].value, False)
    self.assertEqual(file_format_options['png']['offsets'].value, (7, 11))

    self.assertListEqual(list(kwargs), ['offsets', 'is_interlaced'])
    self.assertFalse(kwargs['is_interlaced'])
    self.assertIsInstance(kwargs['offsets'], Gimp.Int32Array)

  def test_get_default_export_function_if_file_format_mode_is_not_use_explicit_values(
        self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    mock_gimp.get_pdb().add_procedure(stubs_gimp.Procedure('gimp-file-save'))

    file_format_options = {}

    # noinspection PyTypeChecker
    proc, kwargs = builtin_actions.get_export_function(
      'unknown', builtin_actions.FileFormatModes.USE_NATIVE_PLUGIN_VALUES, file_format_options)

    self.assertIs(proc, pdb.gimp_file_save)
    mock_get_setting_data_from_pdb_procedure.assert_not_called()
    self.assertFalse(file_format_options)

  def test_get_default_export_function_if_file_format_is_not_recognized(
        self, mock_get_setting_data_from_pdb_procedure, mock_gimp):
    mock_gimp.get_pdb().add_procedure(stubs_gimp.Procedure('gimp-file-save'))

    file_format_options = {}

    # noinspection PyTypeChecker
    proc, kwargs = builtin_actions.get_export_function(
      'unknown', builtin_actions.FileFormatModes.USE_EXPLICIT_VALUES, file_format_options)

    self.assertIs(proc, pdb.gimp_file_save)
    mock_get_setting_data_from_pdb_procedure.assert_not_called()
    self.assertFalse(file_format_options)
