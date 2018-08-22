import unittest

from hconfig import _merge_lists_by_dict_id, merge_trees, merge_files, IncompatibleValues, merge_files_to_stream
from strif import temp_output_file, read_string_from_file, write_string_to_file
from contextlib import contextmanager
from io import StringIO
from ruamel.yaml import YAML
import os
import json
from glob import glob


def yaml_equal(string1, string2):
  """
  Two strings represent the same ordered YAML tree. Key ordering must match. Useful for tests.
  """
  yaml = YAML()
  return yaml.load(StringIO(string1)) == yaml.load(StringIO(string2))


@contextmanager
def string_as_file(string: str, suffix: str = ""):
  """
  Context manager that yields a filename (string) of a temp file with given string contents.
  Useful for tests.
  """
  with temp_output_file(suffix=suffix) as (_fd, out_filename):
    write_string_to_file(out_filename, string)
    yield out_filename


class HConfigTests(unittest.TestCase):
  def _run_files_test(self, base: str):
    output = StringIO()
    merge_files_to_stream(output, *glob("resources/{}_?.json".format(base)), output_format='json')
    expected_output = read_string_from_file("resources/{}_output.json".format(base))
    # Reserializing output to be compact rather than pretty printed
    self.assertEqual(output.getvalue(), json.dumps(json.loads(expected_output)))

  def test_list_merger(self):
    self.assertEqual(
      _merge_lists_by_dict_id([{
        "id": "a",
        "value": 1
      }], [{
        "id": "b",
        "value": 2
      }, {
        "id": "a",
        "value": 3
      }]), [{
        "id": "b",
        "value": 2
      }, {
        "id": "a",
        "value": 3
      }])

  def test_merge_trees(self):
    # Atomics override:
    self.assertEqual(merge_trees(1, 2, 3), 3)
    # Lists fully override:
    self.assertEqual(merge_trees([1, 2, 3], [4], [5, 6]), [5, 6])
    # Dictionaries merge:
    with self.assertRaises(IncompatibleValues):
      merge_trees({"a": 1, "c": 3}, {"b": 2, "a": 10})
    self.assertEqual(merge_trees({"a": 1, "c": 3}, {"b": 2, "a": 10}, strict_base=False), {"c": 3, "b": 2, "a": 10})
    # Lists of dicts are made unique by id (preserving order):
    self.assertEqual(
      merge_trees(
        [{
          "id": "a",
          "value": 1
        }], [{
          "id": "x",
          "value": 99
        }, {
          "id": "b",
          "value": 2
        }, {
          "id": "a",
          "value": 3
        }],
        strict_base=False), [{
          "id": "x",
          "value": 99
        }, {
          "id": "b",
          "value": 2
        }, {
          "id": "a",
          "value": 3
        }])

  def test_type_consistency(self):
    with self.assertRaises(IncompatibleValues):
      merge_trees({"dict": {}}, {"dict": 1})
    with self.assertRaises(IncompatibleValues):
      merge_trees({"list": []}, {"list": 1})
    with self.assertRaises(IncompatibleValues):
      merge_trees({"list": []}, {"list": {}})

    self.assertEqual(
      merge_trees({
        "atom": "!!unset",
        "dict": {},
        "list": []
      }, {
        "atom": "!!unset",
        "dict": {
          "a": 1
        },
        "list": [1, 2, 3]
      }), {
        "atom": "!!unset",
        "dict": {
          "a": 1
        },
        "list": [1, 2, 3]
      })

  def test_functions(self):
    os.environ['MYN'] = "42"
    os.environ['MYVAR'] = 'foo'
    self._run_files_test("test_functions")

  def test_function_override(self):
    os.environ['FOO'] = 'bar'
    self._run_files_test("test_function_override")

  def test_merge_files(self):
    base_config = """
    title: (overridden)
    emoji-tooltip:
      - id: important
        unicode: 🔹
        longText: Important or often overlooked tip
      - id: danger
        unicode: ❗️
        longText: Serious warning or “gotcha” (risks or costs are significant)
    protected:
      enabled: true
    """

    override_config = """
    title: The Open Guide to Amazon Web Services
    short_title: AWS
    slug: og-aws
    emoji-tooltip:
      - id: danger
        unicode: ❗️
        longText: Overriding previous definition
      - id: video
        unicode: 🎥
        longText: Video
    pages:
      - id: authors
        source_url: https://github.com/open-guides/og-aws/raw/master/AUTHORS.md
      - id: contribute
        source_url: https://github.com/open-guides/og-aws/raw/master/CONTRIBUTING.md
    figures:
      figure_regexes:
      - aws-market-landscape.png
      - awsiot-how-it-works_HowITWorks_1-26.png
      - greengrass.png
      - aws-data-transfer-costs.png
    protected:
      enabled: false
    """

    expected = """
    title: The Open Guide to Amazon Web Services
    emoji-tooltip:
    - id: important
      unicode: 🔹
      longText: Important or often overlooked tip
    - id: danger
      unicode: ❗️
      longText: Overriding previous definition
    - id: video
      unicode: 🎥
      longText: Video
    protected:
      enabled: false
    short_title: AWS
    slug: og-aws
    pages:
    - id: authors
      source_url: https://github.com/open-guides/og-aws/raw/master/AUTHORS.md
    - id: contribute
      source_url: https://github.com/open-guides/og-aws/raw/master/CONTRIBUTING.md
    figures:
      figure_regexes:
      - aws-market-landscape.png
      - awsiot-how-it-works_HowITWorks_1-26.png
      - greengrass.png
      - aws-data-transfer-costs.png
    """

    with string_as_file(
        base_config, suffix=".yml") as parent_file, string_as_file(
          override_config, suffix=".yml") as child_file:
      with temp_output_file(suffix='.yml') as (fd, target_file):
        merge_files(target_file, parent_file, child_file, strict_base=False)
        result = read_string_from_file(target_file)
        self.assertTrue(yaml_equal(expected, result))


if __name__ == '__main__':
  unittest.main()
