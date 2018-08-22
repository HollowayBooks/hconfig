"""
Simple config handling with hierarchical overrides.
Combines and merges multiple YAML files so child files "inherit" values from "parent" ones.
Not performance oriented, for moderately sized configs.

Can be used from command line or as a lib.
"""

from collections import OrderedDict
from itertools import chain
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from strif import atomic_output_file
from io import StringIO
import os.path
import json


def as_yaml_string(data):
  """
  Convert an object to a literal YAML string.
  """
  out = StringIO()
  yaml = YAML()
  yaml.dump(data, out)
  return out.getvalue()


class IncompatibleValues(ValueError):
  """
  When overridden values or structures are incompatible.
  """

  def __init__(self, message, *details):
    self.message = message
    self.details = details

  def __str__(self):
    return "%s\n%s\ntypes:%s\n" % (self.message, "\n-----\n".join(as_yaml_string(detail) for detail in self.details),
                                   ",".join(str(type(d)) for d in self.details))


def _is_atomic(item):
  """None or other atomic value."""
  return not isinstance(item, dict) and not isinstance(item, list)


def _toint(value: str) -> int:
  return int(value)


def _expandenv(value: str) -> str:
  return os.path.expandvars(value)


FUNCTIONS = {"H::int": _toint, "H::expandenv": _expandenv}


def get_node_type(node):
  if is_function(node):
    func = FUNCTIONS[list(node.keys())[0]]
    return func.__annotations__['return']
  else:
    return type(node)


ATOMIC_TYPES = [str, int, float, bool]
DICT_TYPES = [dict, OrderedDict, CommentedMap]
LIST_TYPES = [list, CommentedSeq]


def is_type(node, types: list) -> bool:
  return get_node_type(node) in types


def is_function(node: dict):
  try:
    if len(node) == 1:
      funcname = list(node.keys())[0]
      return funcname in FUNCTIONS
  except:
    pass
  return False


def evaluate_function(node: dict):
  func = FUNCTIONS[list(node.keys())[0]]
  arg = list(node.values())[0]
  if is_function(arg):
    arg = evaluate_function(arg)
  return func(arg)


def evaluate_functions(tree):
  # FIXME: newer versions of ruamel break this check
  if is_type(tree, DICT_TYPES):
    for key, value in tree.items():
      if is_function(value):
        tree[key] = evaluate_function(value)
      else:
        tree[key] = evaluate_functions(value)
  elif is_type(tree, LIST_TYPES):
    for j, item in enumerate(tree):
      if is_function(item):
        tree[j] = evaluate_function(item)
      else:
        tree[j] = evaluate_functions(item)
  return tree


def _merge_lists_by_dict_id(*lists, id_field="id"):
  """
  Combine a list of items, eliding dict items (overrides) that have the same id field value.
  Ordering is preserved, except for overridden items, which appear at the point where (last) override occurred.
  """
  # TODO: Could also support concatenation of lists if first item in second list is a magic string (say "...")
  all_items = list(chain(*lists))
  value_by_id = {}

  non_ids = 0
  for item in all_items:
    if is_type(item, DICT_TYPES) and id_field in item:
      value_by_id[item[id_field]] = item
    else:
      non_ids += 1

  if len(value_by_id) > 0:
    # We have objects with ids, so include all previous values.
    if non_ids > 0:
      raise IncompatibleValues("if some items have an id, all items should have an id", *lists)

    result = []
    for item in all_items:
      if item[id_field] not in value_by_id or item is value_by_id[item[id_field]]:  # Last override.
        result.append(item)
    return result
  else:
    # In all other situations, we only use the last list.
    return lists[-1]


def merge_trees(*trees, list_merger=_merge_lists_by_dict_id, dict_type=dict, strict_base=True):
  """
  Merge compatible trees (dicts, lists, or atomic), where values in later trees override values in
  earlier trees. Trees must have compatible structure (corresponding keys have same general types).
  If strict_base is set, we enforce that non-empty dictionaries in the base (the first tree) must
  list every key that is used elsewhere.
  """
  if len(trees) < 1:
    raise IncompatibleValues("must have at least one tree", trees)
  if all(is_type(tree, ATOMIC_TYPES) for tree in trees):
    # Atomic values supersede.
    return trees[-1]
  # FIXME: newer versions of ruamel break this check
  elif all(is_type(tree, DICT_TYPES) for tree in trees):  # Covers OrderedDict, ruamel CommentedMap, EasyDict, dict.
    # Merge dictionaries recursively. We preserve order (so don't use defaultdict).
    # First roll up mapping of keys to all past values.
    key_map = OrderedDict()
    base = trees[0]
    for d in trees:
      for key, value in d.items():
        # With strict mode, an empty base can be overridden, but if any are named, all must be named.
        if strict_base and len(base) > 0 and key not in base:
          raise IncompatibleValues("base definition does not include key '%s'" % key, list(base.keys()), list(d.keys()))
        if key not in key_map:
          key_map[key] = []
        key_map[key].append(value)
    # Now merge each one.
    target = dict_type()
    for (key, items_to_merge) in key_map.items():
      target[key] = merge_trees(*items_to_merge, list_merger=list_merger, dict_type=dict_type)
    return target
  elif all(is_type(tree, LIST_TYPES) for tree in trees):
    # Merge lists.
    return list_merger(*trees)
  else:
    raise IncompatibleValues("to merge, overrides must match overridden type (atomic/list/dict): %s", *trees)


def load_file(filename: Path):
  if filename.suffix == '.json':
    with open(filename) as f:
      return json.load(f)
  elif filename.suffix == '.yml':
    yaml = YAML()
    return yaml.load(filename)
  else:
    raise Exception("unsupported file type: {}".format(filename))


def merge_files_to_stream(target_stream, *yaml_filenames, strict_base: bool = True, output_format: str = 'yaml'):
  if output_format == 'yaml':
    target_stream.write("# *** Not an original file! Generated by hconfig.py from other config files.\n")
    target_stream.write("# *** Sources: %s\n" % ", ".join(yaml_filenames))
    output_writer = YAML()
  elif output_format == 'json':
    output_writer = json
  # noinspection PyTypeChecker
  output_tree = merge_trees(*(load_file(Path(filename)) for filename in yaml_filenames), strict_base=strict_base)

  # To another pass to replace string with values coming from env vars
  evaluate_functions(output_tree)

  output_writer.dump(output_tree, target_stream)


def merge_files(target_filename, *yaml_filenames, strict_base=True, make_parents=True, output_format='yaml'):
  """
  Merge and write out a unified config file to target location, with settings from later files overriding
  those in earlier files, and output in consistent key order (according to last occurrence).
  """
  with atomic_output_file(target_filename, make_parents=make_parents) as temp_out:
    with open(temp_out, "w") as out:
      target_path = Path(target_filename)
      if target_path.suffix == '.json':
        output_format = 'json'
      elif target_path.suffix == '.yml':
        output_format = 'yaml'
      merge_files_to_stream(out, *yaml_filenames, strict_base=strict_base, output_format=output_format)
