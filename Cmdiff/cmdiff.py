#################### Variables ####################
import os
import glob
import logging

from ruamel import yaml
from ruamel.yaml import CommentedMap
from ruamel.yaml.compat import ordereddict
from ruamel.yaml.scalarstring import SingleQuotedScalarString

services = [
    #    'alpp-serv-notification',
    'alpp-comn-integration-abs',
    'alpp-comn-integration-autoteka',
    'alpp-serv-docs',
    'alpp-serv-integration-dwh',
    'alpp-serv-pledge',
    'alpp-serv-orchestrator',
    'alpp-serv-bff-ol',
    # 'alpp-serv-file-transfer',
]

# left_dir = r'D:\idea_workspaces\VTB\AUTO\inventory'
left_dir = r'/data/code/_ins/configmap-diff/left'
left_env = 'k3'

# right_dir = r'D:\idea_workspaces\VTB\AUTO\inventory.prod'
right_dir = r'/data/code/_ins/configmap-diff/right'
right_env = 'k4'

#################### / Variables ###################


logger = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s',
                    level=logging.INFO)


def read_config(dir, environment, service_name, config_block):
    paths = ('os_project', 'configmaps') if config_block == 'configmap' else ('os_project', 'apps')
    target_dir = os.path.join(os.path.abspath(dir), environment, *paths)
    config_glob = os.path.join(target_dir, '*_{}-config.yaml'.format(service_name))
    matching_files = glob.glob(config_glob)
    if len(matching_files) != 1:
        raise FileNotFoundError('No config found by glob: {}'.format(config_glob))
    f = matching_files[0]
    logger.debug('reading {}'.format(f))
    with open(f, 'r', encoding='UTF-8') as config:
        return yaml.round_trip_load(config, preserve_quotes=True)


def diff_keys(reference, compared_to, conf_block):
    e_keys = reference[conf_block].keys()
    c_keys = compared_to[conf_block].keys()
    return set(e_keys) - set(c_keys)


def merge(source, target, block):
    left = source[block]
    right: dict = target[block].copy()
    right_clone = target.copy()
    result: CommentedMap = CommentedMap(ordereddict())
    i = 0
    for key, value in left.items():
        right_value = right[key] if key in right else SingleQuotedScalarString('TODO')
        result.insert(pos=i, key=key, value=right_value)
        comment = left.ca.items[key] if key in left.ca.items else None
        if comment:
            # result.yaml_set_start_comment(comment=comment[2])
            # result.yaml_set_comment_before_after_key(key=key, before=key, indent=comment[2].column)
            # result.yaml_set_start_comment(comment=comment[2].value, indent=comment[2].column)
            # result.yaml_key_comment_extend(key=key, comment=comment)
            result.yaml_end_comment_extend(comment=comment)
        i = i + 1
    right_clone[block] = result
    return right_clone


# def merge(source, target, block):
#     left = source[block]
#     right: dict = target[block].copy()
#     right_clone = target.copy()
#     commented_map: CommentedMap = CommentedMap(ordereddict())
#     i = 0
#     for key, value in left.items():
#         right_value = right[key] if key in right else SingleQuotedScalarString('TODO')
#         commented_map.insert(pos=i, key=key, value=right_value)
#         i = i + 1
#     right_clone[block] = commented_map
#     return right_clone


def diff_values(reference, compared_to, conf_block):
    e_values = reference[conf_block].values()
    c_values = compared_to[conf_block].values()
    pass


def repr_keys(keys):
    return keys if len(keys) > 0 else '-'


if __name__ == '__main__':
    for ms in services:
        logger.info('> {}'.format(ms))
        try:
            left_conf = read_config(left_dir, left_env, ms, 'configmap')
            right_conf = read_config(right_dir, right_env, ms, 'configmap')

            merged = merge(left_conf, right_conf, 'data')
            yaml.round_trip_dump(merged, stream=open('out.yaml', mode='w'))

            missing = diff_keys(left_conf, right_conf, 'data')
            excessive = diff_keys(right_conf, left_conf, 'data')
            logger.info('Missing keys: {}'.format(repr_keys(missing)))
            logger.info('Excessive keys found: {}'.format(repr_keys(excessive)))
        except FileNotFoundError as e:
            logger.error('File {} not found!'.format(e.filename))
        finally:
            logger.info('')
