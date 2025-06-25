import io
import unittest
import unittest.mock as mock

from src.setting import group as group_
from src.setting import settings as settings_
from src.setting import sources as sources_

from src.tests import stubs_gimp
from src.tests.setting import stubs_group


def _test_settings_for_read_write():
  settings = group_.create_groups({
    'name': 'all_settings',
    'groups': [
      {
        'name': 'main',
        'setting_attributes': {'gui_type': None},
      },
      {
        'name': 'gui',
        'setting_attributes': {'gui_type': None},
      },
    ],
  })
  
  settings['main'].add([
    {
      'type': 'str',
      'name': 'file_extension',
      'default_value': 'png',
    },
  ])
  
  procedures = group_.create_groups({
    'name': 'actions',
    'groups': [
      {
        'name': 'resize_to_layer_size',
        'tags': ['command', 'action'],
      },
      {
        'name': 'insert_background',
        'tags': ['command', 'action'],
      },
    ]
  })
  
  settings['main'].add([procedures])
  
  procedures['resize_to_layer_size'].add([
    {
      'type': 'bool',
      'name': 'enabled',
      'default_value': True,
    },
    group_.Group(name='arguments'),
  ])
  
  procedures['insert_background'].add([
    {
      'type': 'bool',
      'name': 'enabled',
      'default_value': True,
    },
    group_.Group(name='arguments'),
  ])
  
  procedures['insert_background/arguments'].add([
    {
      'type': 'str',
      'name': 'tag',
      'default_value': 'background',
    }
  ])
  
  conditions = group_.Group(name='conditions')
  
  settings['main'].add([conditions])
  
  settings['gui'].add([
    {
      'type': 'bool',
      'name': 'edit_mode',
      'default_value': False,
    },
  ])
  
  settings.add([
    {
      'type': 'str',
      'name': 'standalone_setting',
      'default_value': 'something',
      'gui_type': None,
    }
  ])
  
  return settings


def _test_data_for_read_write():
  return [
    {
      'name': 'all_settings',
      'settings': [
        {
          'name': 'main',
          'setting_attributes': {'gui_type': None},
          'settings': [
            {
              'type': 'string',
              'name': 'file_extension',
              'value': 'png',
              'default_value': 'png',
              'gui_type': None,
            },
            {
              'name': 'actions',
              'settings': [
                {
                  'name': 'resize_to_layer_size',
                  'tags': ['command', 'action'],
                  'settings': [
                    {
                      'type': 'bool',
                      'name': 'enabled',
                      'value': True,
                      'default_value': True,
                      'gui_type': None,
                    },
                    {
                      'name': 'arguments',
                      'settings': [],
                    },
                  ],
                },
                {
                  'name': 'insert_background',
                  'tags': ['command', 'action'],
                  'settings': [
                    {
                      'type': 'bool',
                      'name': 'enabled',
                      'value': True,
                      'default_value': True,
                      'gui_type': None,
                    },
                    {
                      'name': 'arguments',
                      'settings': [
                        {
                          'type': 'string',
                          'name': 'tag',
                          'value': 'background',
                          'default_value': 'background',
                          'gui_type': None,
                        },
                      ],
                    },
                  ],
                },
              ],
            },
            {
              'name': 'conditions',
              'settings': [],
            },
          ],
        },
        {
          'name': 'gui',
          'setting_attributes': {'gui_type': None},
          'settings': [
            {
              'type': 'bool',
              'name': 'edit_mode',
              'value': False,
              'default_value': False,
              'gui_type': None,
            },
          ],
        },
        {
          'type': 'string',
          'name': 'standalone_setting',
          'value': 'something',
          'default_value': 'something',
          'gui_type': None,
        },
      ],
    },
  ]


class TestSourceRead(unittest.TestCase):

  def setUp(self):
    self.source_name = 'test_settings'
    self.source = sources_.SimpleInMemorySource(self.source_name)
    
    self.settings = _test_settings_for_read_write()
    
    self.maxDiff = None

  def test_read(self):
    self.source.data = _test_data_for_read_write()
    
    self.source.data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
    self.source.data[0]['settings'][0]['settings'][1]['settings'][0][
      'settings'][0]['value'] = False
    self.source.data[0]['settings'][2]['value'] = 'something_else'
    
    expected_setting_values = {
      setting.get_path(): setting.value for setting in self.settings.walk()}
    expected_setting_values['all_settings/main/file_extension'] = 'jpg'
    expected_setting_values['all_settings/main/actions/resize_to_layer_size/enabled'] = False
    expected_setting_values['all_settings/standalone_setting'] = 'something_else'
    
    self.source.read([self.settings])
    
    for setting in self.settings.walk():
      self.assertEqual(setting.value, expected_setting_values[setting.get_path()])
  
  def test_read_specific_settings(self):
    self.source.data = _test_data_for_read_write()
    
    self.source.data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
    self.source.data[0]['settings'][0]['settings'][1]['settings'][1][
      'settings'][0]['value'] = False
    self.source.data[0]['settings'][0]['settings'][1]['settings'][1][
      'settings'][1]['settings'][0]['value'] = 'foreground'
    self.source.data[0]['settings'][2]['value'] = 'something_else'
    
    expected_setting_values = {
      setting.get_path(): setting.value for setting in self.settings.walk()}
    expected_setting_values[
      'all_settings/main/actions/insert_background/enabled'] = False
    expected_setting_values[
      'all_settings/main/actions/insert_background/arguments/tag'] = 'foreground'
    expected_setting_values['all_settings/standalone_setting'] = 'something_else'
    
    self.source.read([self.settings['main/actions'], self.settings['standalone_setting']])
    
    for setting in self.settings.walk():
      self.assertEqual(setting.value, expected_setting_values[setting.get_path()])
  
  def test_read_ignores_non_value_attributes_for_existing_settings(self):
    self.source.data = _test_data_for_read_write()
    
    self.source.data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
    self.source.data[0]['settings'][0]['settings'][0]['default_value'] = 'gif'
    self.source.data[0]['settings'][0]['settings'][0]['description'] = 'some description'
    
    self.source.read([self.settings['main/file_extension']])
    
    self.assertEqual(self.settings['main/file_extension'].value, 'jpg')
    self.assertEqual(self.settings['main/file_extension'].default_value, 'png')
    self.assertEqual(self.settings['main/file_extension'].description, 'File extension')
  
  def test_read_not_all_settings_found(self):
    self.source.data = _test_data_for_read_write()
    
    # 'main/actions/resize_to_layer_size/arguments'
    del self.source.data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][1]
    # 'main/actions/resize_to_layer_size/enabled'
    del self.source.data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]
    # 'main/actions/insert_background'
    del self.source.data[0]['settings'][0]['settings'][1]['settings'][1]
    # 'main/conditions'
    del self.source.data[0]['settings'][0]['settings'][2]
    # 'main/file_extension'
    del self.source.data[0]['settings'][0]['settings'][0]
    # 'gui'
    del self.source.data[0]['settings'][1]
    
    self.source.read(
      [self.settings['main/file_extension'],
       self.settings['main/actions/insert_background'],
       self.settings['main/actions/resize_to_layer_size']])
    
    self.assertListEqual(
      self.source.settings_not_loaded,
      [self.settings['main/file_extension'],
       self.settings['main/actions/insert_background'],
       # Missing settings and empty groups must be expanded.
       self.settings['main/actions/resize_to_layer_size/enabled'],
       self.settings['main/actions/resize_to_layer_size/arguments']])
    
    # Test if `settings_not_loaded` is reset on each call to `read()`
    self.source.read([self.settings['main/conditions']])
    
    self.assertListEqual(self.source.settings_not_loaded, [self.settings['main/conditions']])
  
  def test_read_creates_new_child_groups_and_settings_if_missing(self):
    self.source.data = _test_data_for_read_write()
    
    # Add 'main/actions/resize_to_layer_size/arguments/tag'
    tag_argument = {
      'type': 'string',
      'name': 'tag',
      'value': 'foreground',
      'default_value': 'background',
    }
    self.source.data[0]['settings'][0]['settings'][1]['settings'][0][
      'settings'][1]['settings'].append(tag_argument)
    
    # Add 'main/conditions/visible'
    visible_condition = {
      'name': 'visible',
      'tags': ['command', 'condition'],
      'setting_attributes': {'gui_type': None},
      'settings': [
        {
          'type': 'bool',
          'name': 'enabled',
          'value': False,
          'default_value': True,
        },
        {
          'name': 'arguments',
          'setting_attributes': {'gui_type': None},
          'settings': [
            {
              'type': 'string',
              'name': 'tag',
              'value': 'foreground',
              'default_value': 'background',
            },
          ],
        },
      ],
    }
    self.source.data[0]['settings'][0]['settings'][2]['settings'].append(visible_condition)
    
    expected_num_settings_and_groups = len(list(self.settings.walk(include_groups=True))) + 5
    
    self.source.read([self.settings])
    
    self.assertEqual(
      len(list(self.settings.walk(include_groups=True))), expected_num_settings_and_groups)
    self.assertDictEqual(
      self.settings['main/actions/resize_to_layer_size/arguments/tag'].to_dict(),
      {
        'type': 'string',
        'name': 'tag',
        'value': 'foreground',
        'default_value': 'background',
        'gui_type': None,
      })
    self.assertSetEqual(
      self.settings['main/conditions/visible'].tags, {'command', 'condition'})
    self.assertDictEqual(
      self.settings['main/conditions/visible/enabled'].to_dict(),
      {
        'type': 'bool',
        'name': 'enabled',
        'value': False,
        'default_value': True,
        'gui_type': None,
      })
    self.assertDictEqual(
      self.settings['main/conditions/visible/arguments/tag'].to_dict(),
      {
        'type': 'string',
        'name': 'tag',
        'value': 'foreground',
        'default_value': 'background',
        'gui_type': None,
      })
  
  def test_read_setting_without_parent(self):
    self.source.data = _test_data_for_read_write()
    
    self.source.data.append({'name': 'setting_without_parent', 'value': True, 'type': 'bool'})
    
    setting_without_parent = settings_.BoolSetting('setting_without_parent')
    
    self.source.read([self.settings, setting_without_parent])
    
    self.assertTrue(setting_without_parent.value)
  
  def test_read_ignore_settings_with_ignore_load_tag(self):
    self.source.data = _test_data_for_read_write()
    
    # 'main/file_extension'
    self.source.data[0]['settings'][0]['settings'][0]['tags'] = ['ignore_load']
    # A new setting inside 'main/conditions' to be ignored
    self.source.data[0]['settings'][0]['settings'][2]['settings'].append(
      {'name': 'enabled', 'type': 'bool', 'value': False})
    # A new group inside 'main/actions' to be ignored
    self.source.data[0]['settings'][0]['settings'][1]['settings'].append(
      {'name': 'rename',
       'tags': ['ignore_load'],
       'settings': [{'name': 'enabled', 'type': 'bool', 'value': False}]})
    # A new setting inside 'main/actions' to be ignored
    self.source.data[0]['settings'][0]['settings'][1]['settings'].append(
      {'name': 'new_setting', 'type': 'string', 'value': 'new', 'tags': ['ignore_load']})
    
    self.settings['main/file_extension'].set_value('jpg')
    
    self.settings['main/actions/resize_to_layer_size/enabled'].tags.add('ignore_load')
    self.settings['main/actions/resize_to_layer_size/enabled'].set_value(False)
    
    self.settings['main/actions/insert_background'].tags.add('ignore_load')
    self.settings['main/actions/insert_background/enabled'].set_value(False)
    self.settings['main/actions/insert_background/arguments/tag'].set_value('fg')
    
    self.settings['main/conditions'].tags.add('ignore_load')
    
    self.source.read([self.settings])
    
    self.assertFalse(self.source.settings_not_loaded)
    # The tag was not found in the code. Any attribute except 'value' in the
    # source is ignored. Therefore, the setting value is overridden.
    self.assertEqual(self.settings['main/file_extension'].value, 'png')
    # The tag is found in the code, therefore the value for this setting will not be overridden
    self.assertEqual(self.settings['main/actions/resize_to_layer_size/enabled'].value, False)
    # The tag is found in the code for a parent
    self.assertEqual(
      self.settings['main/actions/insert_background/enabled'].value, False)
    self.assertEqual(
      self.settings['main/actions/insert_background/arguments/tag'].value, 'fg')
    # Group does not exist in the code, exists in the source but is not loaded
    self.assertNotIn('rename', self.settings['main/actions'])
    # Setting does not exist in the code, exists in the source but is not loaded
    self.assertNotIn('new_setting', self.settings['main/actions'])
    # The tag exists in a group in the code and any child in the source is ignored
    self.assertFalse(list(self.settings['main/conditions']))
  
  def test_read_order_of_settings_in_source_has_no_effect_if_settings_exist_in_memory(self):
    self.settings['main/actions'].reorder('resize_to_layer_size', 1)
    
    self.settings['main/actions/resize_to_layer_size/enabled'].set_value(False)
    self.settings['main/actions/insert_background/enabled'].set_value(False)
    
    self.source.data = _test_data_for_read_write()
    
    self.source.read([self.settings])
    
    self.assertEqual(self.settings['main/actions/resize_to_layer_size/enabled'].value, True)
    self.assertEqual(self.settings['main/actions/insert_background/enabled'].value, True)
  
  def test_read_invalid_setting_value_retains_the_value(self):
    setting_dict = {
      'name': 'some_number',
      'default_value': 2,
      'min_value': 0,
    }
    
    setting = settings_.IntSetting(**setting_dict)
    setting.set_value(5)
    
    setting_dict['type'] = 'int'
    setting_dict['value'] = 2
        
    self.source.data = [setting_dict]
    
    self.source.read([setting])
    
    self.assertEqual(
      setting.value,
      setting.default_value)
  
  def test_read_raises_error_if_list_expected_but_not_found(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': {'name': 'file_extension_not_inside_list', 'type': 'string', 'value': 'png'}
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_expected_but_not_found(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [[{'name': 'file_extension_not_inside_list', 'type': 'string', 'value': 'png'}]]
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_is_missing_name(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [{'type': 'string', 'value': 'png'}]
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_is_missing_value(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [{'name': 'file_extension', 'type': 'string'}]
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_is_missing_settings(self):
    self.source.data = [
      {
        'name': 'all_settings',
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_has_both_value_and_settings(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [{'name': 'file_extension', 'type': 'string', 'value': 'png'}],
        'value': 'png',
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_has_value_but_object_is_group(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [
          {
            'type': 'string',
            'name': 'main',
            'value': 'png',
          },
        ],
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])
  
  def test_read_raises_error_if_dict_has_settings_but_object_is_setting(self):
    self.source.data = [
      {
        'name': 'all_settings',
        'settings': [
          {
            'name': 'main',
            'settings': [
              {
                'name': 'file_extension',
                'settings': [
                  {
                    'type': 'string',
                    'name': 'some_setting',
                    'value': 'png',
                  }
                ],
              },
            ]
          },
        ],
      }
    ]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.read([self.settings])

  def test_read_with_modify_data_func(self):
    def modify_data(data):
      data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
      data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]['value'] = False
      data[0]['settings'][2]['value'] = 'something_else'

      return data

    self.source.data = _test_data_for_read_write()

    expected_setting_values = {
      setting.get_path(): setting.value for setting in self.settings.walk()}
    expected_setting_values['all_settings/main/file_extension'] = 'jpg'
    expected_setting_values['all_settings/main/actions/resize_to_layer_size/enabled'] = False
    expected_setting_values['all_settings/standalone_setting'] = 'something_else'

    self.source.read([self.settings], modify_data_func=modify_data)

    for setting in self.settings.walk():
      self.assertEqual(setting.value, expected_setting_values[setting.get_path()])

  def test_read_error_in_modify_data_func_raises_error(self):
    def modify_data_before_load(_data):
      raise ValueError

    with self.assertRaises(sources_.SourceModifyDataError):
      self.source.read([self.settings], modify_data_func=modify_data_before_load)

  def test_read_invalid_modify_data_func_raises_error(self):
    with self.assertRaises(sources_.SourceModifyDataError):
      # noinspection PyTypeChecker
      self.source.read([self.settings], modify_data_func=12)


class TestSourceWrite(unittest.TestCase):
  
  def setUp(self):
    self.source_name = 'test_settings'
    self.source = sources_.SimpleInMemorySource(self.source_name)
    
    self.settings = _test_settings_for_read_write()
    
    self.maxDiff = None
  
  def test_write_empty_data(self):
    expected_data = _test_data_for_read_write()
    
    self.source.write([self.settings])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_modifies_existing_data(self):
    expected_data = _test_data_for_read_write()
    
    self.settings['main/file_extension'].set_value('jpg')
    self.settings['main/actions/resize_to_layer_size/enabled'].set_value(False)
    self.settings['standalone_setting'].set_value('something_else')
    
    expected_data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
    expected_data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]['value'] = False
    expected_data[0]['settings'][2]['value'] = 'something_else'
    
    self.source.data = _test_data_for_read_write()
    self.source.write([self.settings])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_modifies_only_selected_settings(self):
    expected_data = _test_data_for_read_write()
    
    self.settings['main/file_extension'].set_value('jpg')
    self.settings['main/actions/resize_to_layer_size/enabled'].set_value(False)
    self.settings['main/actions/insert_background/enabled'].set_value(False)
    self.settings['standalone_setting'].set_value('something_else')
    
    expected_data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]['value'] = False
    expected_data[0]['settings'][0]['settings'][1]['settings'][1]['settings'][0]['value'] = False
    expected_data[0]['settings'][2]['value'] = 'something_else'
    
    self.source.data = _test_data_for_read_write()
    
    self.source.write([self.settings['main/actions'], self.settings['standalone_setting']])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_adds_groups_which_are_not_present_in_source(self):
    expected_data = _test_data_for_read_write()
    
    # Keep only 'main/actions/resize_to_layer_size/enabled' and 'standalone_setting'
    del expected_data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][1]
    del expected_data[0]['settings'][0]['settings'][1]['settings'][1]
    del expected_data[0]['settings'][0]['settings'][2]
    del expected_data[0]['settings'][0]['settings'][0]
    del expected_data[0]['settings'][1]
    
    self.source.write(
      [self.settings['main/actions/resize_to_layer_size/enabled'],
       self.settings['standalone_setting']])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_adds_settings_to_existing_groups(self):
    expected_data = _test_data_for_read_write()
    
    new_setting = {
      'type': 'string',
      'name': 'origin',
    }
    
    expected_new_setting_dict = {
      'type': 'string',
      'name': 'origin',
      'value': 'builtin',
      'gui_type': None,
    }
    
    self.settings['main/actions/resize_to_layer_size/arguments'].add([new_setting])
    self.settings['main/actions/resize_to_layer_size/arguments/origin'].set_value('builtin')
    
    expected_data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][1][
      'settings'].append(expected_new_setting_dict)
    
    self.source.write([self.settings])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_multiple_settings_separately(self):
    expected_data = _test_data_for_read_write()
    
    expected_data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
    expected_data[0]['settings'][2]['value'] = 'something_else'
    
    self.settings['main/file_extension'].set_value('jpg')
    
    self.source.write([self.settings])
    
    self.settings['standalone_setting'].set_value('something_else')
    
    self.source.write([self.settings['standalone_setting']])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_setting_without_parent(self):
    expected_data = _test_data_for_read_write()
    
    expected_data.append({'name': 'setting_without_parent', 'value': False, 'type': 'bool'})
    
    setting_without_parent = settings_.BoolSetting('setting_without_parent')
    
    self.source.write([self.settings, setting_without_parent])
    
    self.assertListEqual(self.source.data, expected_data)
  
  def test_write_ignores_settings_with_ignore_save_tag(self):
    self.source.data = _test_data_for_read_write()
    
    self.settings['main/file_extension'].set_value('jpg')
    
    self.settings['main/actions/resize_to_layer_size/enabled'].tags.add('ignore_save')
    self.settings['main/actions/resize_to_layer_size/enabled'].set_value(False)
    
    self.settings['main/actions/insert_background'].tags.add('ignore_save')
    self.settings['main/actions/insert_background/enabled'].set_value(False)
    self.settings['main/actions/insert_background/arguments/tag'].set_value('fg')
    
    self.settings['main/conditions'].tags.add('ignore_save')
    self.settings['main/conditions'].add([{'name': 'enabled', 'type': 'bool'}])
    self.settings['main/conditions/enabled'].set_value(False)
    
    self.source.write([self.settings])
    
    self.assertEqual(
      self.source.data[0]['settings'][0]['settings'][0]['value'], 'jpg')
    # 'main/actions/resize_to_layer_size/enabled' setting is not saved
    self.assertFalse(
      self.source.data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]['settings'])
    # 'main/actions/insert_background' group is not saved
    self.assertEqual(len(self.source.data[0]['settings'][0]['settings'][1]['settings']), 1)
    # Child not present in data and the tag exists in the parent
    self.assertEqual(len(self.source.data[0]['settings'][0]['settings']), 2)
  
  def test_write_setting_is_completely_overridden_and_extra_attributes_in_data_are_removed(self):
    self.source.data = _test_data_for_read_write()
    self.source.data[0]['settings'][0]['settings'][0]['pdb_type'] = [None]
    
    expected_data = _test_data_for_read_write()
    
    self.source.write([self.settings])
    
    self.assertEqual(self.source.data, expected_data)
  
  def test_write_group_is_removed_and_stored_anew_in_data(self):
    self.source.data = _test_data_for_read_write()
    self.source.data[0]['settings'][0]['settings'][1]['settings'].append(
      {
        'name': 'new_group',
        'settings': [
          {
            'name': 'enabled',
            'type': 'bool',
          },
        ],
      })
    
    expected_data = _test_data_for_read_write()
    
    self.source.write([self.settings])
    
    self.assertEqual(self.source.data, expected_data)
  
  def test_write_current_order_of_settings_within_group_is_applied_to_data(self):
    self.settings['main/actions'].reorder('resize_to_layer_size', 1)
    
    self.source.data = _test_data_for_read_write()
    
    expected_data = _test_data_for_read_write()
    resize_to_layer_size_dict = expected_data[0]['settings'][0]['settings'][1]['settings'].pop(0)
    expected_data[0]['settings'][0]['settings'][1]['settings'].append(resize_to_layer_size_dict)
    
    self.source.write([self.settings])
    
    self.assertEqual(self.source.data, expected_data)
  
  def test_write_raises_error_if_list_expected_but_not_found(self):
    self.source.data = {'source_name': []}
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.write([self.settings])
  
  def test_write_raises_error_if_dict_expected_but_not_found(self):
    self.source.data = [[{'source_name': []}]]
    
    with self.assertRaises(sources_.SourceInvalidFormatError):
      self.source.write([self.settings])

  def test_write_with_modify_data_func(self):
    def modify_data(data):
      data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
      data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]['value'] = False
      data[0]['settings'][2]['value'] = 'something_else'

      return data

    expected_data = _test_data_for_read_write()

    expected_data[0]['settings'][0]['settings'][0]['value'] = 'jpg'
    expected_data[0]['settings'][0]['settings'][1]['settings'][0]['settings'][0]['value'] = False
    expected_data[0]['settings'][2]['value'] = 'something_else'

    self.source.data = _test_data_for_read_write()
    self.source.write([self.settings], modify_data_func=modify_data)

    self.assertListEqual(self.source.data, expected_data)

  def test_write_error_in_modify_data_func_raises_error(self):
    def modify_data(_data):
      raise ValueError

    with self.assertRaises(sources_.SourceModifyDataError):
      self.source.write([self.settings], modify_data_func=modify_data)

  def test_write_invalid_modify_data_func_raises_error(self):
    with self.assertRaises(sources_.SourceModifyDataError):
      # noinspection PyTypeChecker
      self.source.write([self.settings], modify_data_func=12)


@mock.patch('src.setting.sources.Gimp', new_callable=stubs_gimp.GimpModuleStub)
class TestGimpParasiteSource(unittest.TestCase):
  
  @mock.patch('src.setting.sources.Gimp')
  def setUp(self, mock_gimp_module):
    mock_gimp_module.directory.return_value = 'gimp_directory'

    self.source_name = 'test_settings'
    self.source = sources_.GimpParasiteSource(self.source_name)
    self.settings = stubs_group.create_test_settings()
  
  def test_write_read(self, _mock_gimp_module):
    self.settings['file_extension'].set_value('jpg')
    self.settings['flatten'].set_value(True)
    
    self.source.write([self.settings])
    
    self.settings['file_extension'].reset()
    self.settings['flatten'].reset()
    
    self.source.read([self.settings])
    
    self.assertEqual(self.settings['file_extension'].value, 'jpg')
    self.assertEqual(self.settings['flatten'].value, True)
  
  def test_read_source_not_found(self, _mock_gimp_module):
    with self.assertRaises(sources_.SourceNotFoundError):
      self.source.read([self.settings])
  
  def test_read_settings_invalid_format(self, _mock_gimp_module):
    self.source.write([self.settings])

    with mock.patch('src.setting.sources.pickle') as temp_mock_pickle:
      temp_mock_pickle.loads.side_effect = ValueError

      with self.assertRaises(sources_.SourceInvalidFormatError):
        self.source.read([self.settings])
  
  def test_clear(self, _mock_gimp_module):
    self.source.write([self.settings])
    self.source.clear()
    
    with self.assertRaises(sources_.SourceNotFoundError):
      self.source.read([self.settings])
  
  def test_has_data_with_no_data(self, _mock_gimp_module):
    self.assertFalse(self.source.has_data())
  
  def test_has_data_with_data(self, _mock_gimp_module):
    self.source.write([self.settings['file_extension']])
    self.assertTrue(self.source.has_data())


# noinspection PyUnresolvedReferences
class _FileSourceTests:
  
  def __init__(self, source_name, filepath, source_class):
    self._source_name = source_name
    self._filepath = filepath
    self._source_class = source_class
  
  def test_write_read(self, mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)

    self.settings['file_extension'].set_value('jpg')
    self.settings['flatten'].set_value(True)
    
    self.source.write([self.settings])
    
    mock_os_path_isfile.return_value = True
    self.source.read([self.settings])
    
    self.assertEqual(self.settings['file_extension'].value, 'jpg')
    self.assertEqual(self.settings['flatten'].value, True)
  
  def test_write_multiple_settings_separately(self, mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)

    self.settings['file_extension'].set_value('jpg')
    
    self.source.write([self.settings['file_extension']])
    
    self.settings['flatten'].set_value(True)
    
    mock_os_path_isfile.return_value = True
    self.source.write([self.settings['flatten']])
    
    self.source.read([self.settings['file_extension']])
    self.source.read([self.settings['flatten']])
    
    self.assertEqual(self.settings['file_extension'].value, 'jpg')
    self.assertEqual(self.settings['flatten'].value, True)
    
    self.settings['file_extension'].set_value('gif')
    
    self.source.write([self.settings['file_extension']])
    self.source.read([self.settings['file_extension']])
    
    self.assertEqual(self.settings['file_extension'].value, 'gif')
    self.assertEqual(self.settings['flatten'].value, True)
  
  def test_write_retains_other_source_names(self, mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)

    source_2 = self._source_class('test_settings_2', self.filepath)
    self.source.write_data_to_source = mock.Mock(wraps=self.source.write_data_to_source)
    source_2.write_data_to_source = mock.Mock(wraps=source_2.write_data_to_source)
    
    self.settings['file_extension'].set_value('jpg')
    self.settings['flatten'].set_value(True)
    
    self.source.write([self.settings['file_extension']])
    mock_os_path_isfile.return_value = True
    
    source_2.write([self.settings['flatten']])
    
    self.source.read([self.settings['file_extension']])
    source_2.read([self.settings['flatten']])
    
    self.assertEqual(self.settings['file_extension'].value, 'jpg')
    self.assertEqual(self.settings['flatten'].value, True)
    
    self.assertEqual(self.source.write_data_to_source.call_count, 1)
    self.assertEqual(source_2.write_data_to_source.call_count, 1)
  
  def test_has_data_no_data(self, _mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)

    self.assertFalse(self.source.has_data())
  
  def test_has_data_contains_data(self, mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)

    self.settings['file_extension'].set_value('jpg')
    
    self.source.write([self.settings['file_extension']])
    
    mock_os_path_isfile.return_value = True
    
    self.assertTrue(self.source.has_data())
  
  def test_has_data_error_on_read(self, mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)

    self.source.write([self.settings['file_extension']])
    
    mock_os_path_isfile.return_value = True
    mock_open.return_value.__exit__.side_effect = sources_.SourceInvalidFormatError
    
    self.assertEqual(self.source.has_data(), 'invalid_format')
  
  def test_clear_no_data(self, _mock_os_path_isfile, mock_open):
    self._set_up_mock_open(mock_open)
    self.source.write_data_to_source = mock.Mock(wraps=self.source.write_data_to_source)
    
    self.source.clear()
    
    self.assertFalse(self.source.has_data())
    self.assertEqual(self.source.write_data_to_source.call_count, 0)

  def test_clear_data_in_different_source(self, mock_os_path_isfile, mock_open):
    def _truncate_and_write(data):
      string_io.truncate(0)
      _orig_string_io_write(data)

    string_io = self._set_up_mock_open(mock_open)

    source_2 = self._source_class('test_settings_2', self.filepath)
    self.source.write_data_to_source = mock.Mock(wraps=self.source.write_data_to_source)
    source_2.write_data_to_source = mock.Mock(wraps=source_2.write_data_to_source)

    self.source.write([self.settings['file_extension']])
    mock_os_path_isfile.return_value = True

    source_2.write([self.settings['flatten']])

    _orig_string_io_write = string_io.write
    string_io.write = _truncate_and_write

    self.source.clear()

    source_has_data = self.source.has_data()
    # FIXME: 'invalid_format' should not happen for real data
    self.assertTrue(not source_has_data or source_has_data == 'invalid_format')

    self.assertTrue(source_2.has_data())

    self.assertEqual(self.source.write_data_to_source.call_count, 1)
    self.assertEqual(source_2.write_data_to_source.call_count, 1)

  @staticmethod
  def _set_up_mock_open(mock_open):
    string_io = io.StringIO()

    mock_open.return_value.__enter__.return_value = string_io
    mock_open.return_value.__exit__.side_effect = (
      lambda *args, **kwargs: mock_open.return_value.__enter__.return_value.seek(0))

    return string_io


@mock.patch('src.setting.sources.open')
@mock.patch('src.setting.sources.os.path.isfile', return_value=False)
class TestJsonFileSource(unittest.TestCase, _FileSourceTests):
  
  def __init__(self, *args, **kwargs):
    _FileSourceTests.__init__(
      self, 'test_settings', 'test_filepath.json', sources_.JsonFileSource)
    
    unittest.TestCase.__init__(self, *args, **kwargs)
  
  def setUp(self):
    self.source_name = self._source_name
    self.filepath = self._filepath
    self.source = self._source_class(self.source_name, self.filepath)
    self.settings = stubs_group.create_test_settings()
