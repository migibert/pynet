from __future__ import absolute_import
import subprocess
from pynetlib.exceptions import ValueNotFoundException


def execute_command(command, namespace=None):
    ns = namespace
    if hasattr(namespace, 'name'):
        ns = namespace.name
    if ns is None or ns == '':
        cmd = command
    else:
        cmd = 'ip netns exec %s %s' % (ns, command)
    return subprocess.check_output(cmd, shell=True)


def get_devices_info(output):
    devices = []
    blocks = parse_output(output)
    for block in blocks:
        id, name, flags = parse_header(block)
        state = find_values_or_default_value(block, 'state', single=True, default_value='UNKNOWN')
        inet = find_values_or_default_value(block, 'inet', default_value=[])
        inet6 = find_values_or_default_value(block, 'inet6', default_value=[])
        mtu = find_values_or_default_value(block, 'mtu', default_value=None, single=True)
        qlen = find_values_or_default_value(block, 'qlen', default_value=None, single=True)
        devices.append((id, name, flags, state, inet, inet6, mtu, qlen))
    return devices


def parse_output(output):
    blocks = []
    current_block = ''

    for line in output.split('\n'):
        if line and line[0].isdigit():
            if current_block:
                blocks.append(current_block)
                current_block = ''
        current_block = current_block + line
    if current_block:
        blocks.append(current_block)
    return blocks


def parse_header(header):
    prefixes = header.split(':')
    id = prefixes[0]
    name = prefixes[1].strip()
    flags = header[header.index('<') + 1:header.index('>')].split(',')
    return id, name, flags


def find_values(data, key):
    result = []
    words = data.split(' ')
    indexes = [index for index, word in enumerate(words) if word == key]
    for index in indexes:
        value_index = index + 1
        if len(words) > value_index:
            result.append(words[value_index])
        else:
            raise ValueNotFoundException(key)
    if len(result) == 0:
        raise ValueNotFoundException(key)
    return result


def find_values_or_default_value(data, key, default_value=None, single=False):
    try:
        result = find_values(data, key)
        return result[0] if single else result
    except ValueNotFoundException:
        return default_value
