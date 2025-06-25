import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
from gi.repository import GObject

from src import setting as setting_
from src import settings_from_pdb as settings_from_pdb_
from src import placeholders as placeholders_
from src import pypdb

from src.tests import stubs_gimp


@mock.patch('src.setting.settings._gimp_objects.Gimp', new_callable=stubs_gimp.GimpModuleStub)
@mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
class TestGetSettingDataFromPdbProcedure(unittest.TestCase):

  @mock.patch('src.pypdb.Gimp.get_pdb', return_value=stubs_gimp.PdbStub)
  def setUp(self, *_mocks):
    self.procedure_name = 'file-png-export'

    self.procedure_stub_kwargs = dict(
      name=self.procedure_name,
      arguments_spec=[
        dict(
          value_type=Gimp.RunMode.__gtype__,
          name='run-mode',
          blurb='The run mode',
          default_value=Gimp.RunMode.NONINTERACTIVE,
        ),
        dict(
          value_type=GObject.GType.from_name('GimpCoreObjectArray'),
          name='drawables',
          blurb='Drawables',
          object_type=Gimp.Drawable.__gtype__,
        ),
        dict(
          value_type=GObject.TYPE_STRING, name='filename', blurb='Filename to save the image in')],
      blurb='Saves files in PNG file format')

    settings_from_pdb_.pdb.remove_from_cache(self.procedure_name)

  def test_with_non_unique_param_names(self, *_mocks):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(
        value_type=GObject.GType.from_name('GimpCoreObjectArray'),
        name='drawables',
        blurb='More drawables',
        object_type=Gimp.Drawable.__gtype__,
      ),
      dict(value_type=GObject.TYPE_STRING, name='filename', blurb='Another filename'),
      dict(value_type=GObject.TYPE_STRV, name='brushes', blurb='Brush names'),
    ])

    extended_procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    procedure, procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      extended_procedure_stub.get_name())

    self.assertIsInstance(procedure, pypdb.PDBProcedure)
    self.assertEqual(procedure_name, self.procedure_name)

    self.maxDiff = None

    self.assertListEqual(
      arguments,
      [
        {
          'name': 'run-mode',
          'type': setting_.EnumSetting,
          'default_value': Gimp.RunMode.NONINTERACTIVE,
          'enum_type': (procedure, procedure.arguments[0]),
          'display_name': 'The run mode',
        },
        {
          'name': 'drawables',
          'type': placeholders_.PlaceholderDrawableArraySetting,
          'element_type': setting_.DrawableSetting,
          'display_name': 'Drawables',
        },
        {
          'name': 'filename',
          'type': setting_.StringSetting,
          'pdb_type': GObject.TYPE_STRING,
          'display_name': 'Filename to save the image in',
        },
        {
          'name': 'drawables-2',
          'type': placeholders_.PlaceholderDrawableArraySetting,
          'element_type': setting_.DrawableSetting,
          'display_name': 'More drawables',
        },
        {
          'name': 'filename-2',
          'type': setting_.StringSetting,
          'pdb_type': GObject.TYPE_STRING,
          'display_name': 'Another filename',
        },
        {
          'name': 'brushes',
          'type': setting_.ArraySetting,
          'element_type': setting_.StringSetting,
          'display_name': 'Brush names',
        },
      ]
    )

  def test_unsupported_pdb_param_type(self, *_mocks):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(
        value_type='unsupported',
        default_value='test',
        name='param-with-unsupported-type',
        blurb='Test'),
    ])

    extended_procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      extended_procedure_stub.get_name())

    unsupported_param = arguments[-1]

    self.assertDictEqual(
      unsupported_param,
      {
        'type': placeholders_.PlaceholderUnsupportedParameterSetting,
        'name': 'param-with-unsupported-type',
        'display_name': 'Test',
        'default_param_value': 'test',
      }
    )

  def test_default_run_mode_is_noninteractive(self, *_mocks):
    self.procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(self.procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      self.procedure_name)

    self.assertEqual(arguments[0]['default_value'], Gimp.RunMode.NONINTERACTIVE)

  def test_gimp_object_types_are_replaced_with_placeholders(self, *_mocks):
    self.procedure_stub_kwargs['arguments_spec'].extend([
      dict(value_type=Gimp.Image.__gtype__, name='image', blurb='The image'),
      dict(value_type=Gimp.Layer.__gtype__, name='layer', blurb='The layer to process'),
    ])

    extended_procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(extended_procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      self.procedure_name)

    self.assertEqual(arguments[-2]['type'], placeholders_.PlaceholderImageSetting)
    self.assertEqual(arguments[-1]['type'], placeholders_.PlaceholderLayerSetting)

  def test_with_hard_coded_custom_default_value(self, *_mocks):
    self.procedure_name = 'plug-in-lighting'
    self.procedure_stub_kwargs['name'] = self.procedure_name

    self.procedure_stub_kwargs['arguments_spec'].append(
      dict(value_type=GObject.TYPE_BOOLEAN, name='new-image', default_value=True),
    )

    procedure_stub = stubs_gimp.Procedure(**self.procedure_stub_kwargs)
    stubs_gimp.PdbStub.add_procedure(procedure_stub)

    _procedure, _procedure_name, arguments = settings_from_pdb_.get_setting_data_from_pdb_procedure(
      self.procedure_name)

    self.assertEqual(arguments[-1]['default_value'], False)
