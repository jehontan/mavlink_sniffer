import xmltodict
import jinja2 as j2
import re
from typing import List, Tuple, Mapping
import os

type_map = {
    'char': ('bytes', 's', 1),
    'int8_t': ('int', 'b', 1),
    'uint8_t': ('int', 'B', 1),
    'uint8_t_mavlink_version': ('int', 'B', 1),
    'int16_t': ('int', 'h', 2),
    'uint16_t': ('int', 'H', 2),
    'int32_t': ('int', 'i', 4),
    'uint32_t': ('int', 'I', 4),
    'int64_t': ('int', 'q', 8),
    'uint64_t': ('int', 'Q', 8),
    'float': ('float', 'f', 4),
    'double': ('float', 'd', 8)
}

def to_camel_case(snake_str):
    return "".join(x.capitalize() for x in snake_str.lower().split("_"))

def ensure_list(thing):
    if not isinstance(thing, list):
        return [thing]
    else:
        return thing

def resolve_type(field:dict) -> str:
    if '@enum' in field.keys():
        return field['@enum']
    
    # handle arrays
    T = field['@type']
    match = re.search('(?<=\[).+(?=\])', T)

    if match:
        arr_len = int(match.group())
        T = T[:match.span()[0]-1]
        if T == 'char':
            return 'bytes'
        else:
            t = type_map[T][0]
            return f'Tuple[{",".join([t for i in range(arr_len)])}]'
    else:
        return type_map[T][0]

def type_size(field:dict) -> int:
    # handle arrays
    T = field['@type']
    match = re.search('(?<=\[).+(?=\])', T)

    if match:
        T = T[:match.span()[0]-1]

    return type_map[T][2]

def reorder_fields(fields: list):
    return sorted(fields, key=type_size, reverse=True)

def resolve_fmt(msg:dict) -> Tuple[str, List[Tuple[int, str]]]:
    main_fmt = '!'
    sub_fmts = []
    for i, field in enumerate(ensure_list(msg['field'])):
        # check if array
        T = field['@type']
        match = re.search('(?<=\[).+(?=\])', T)

        if match:
            T = T[:match.span()[0]-1]
            arr_len = int(match.group())
            main_fmt += f'{arr_len * type_map[T][2]}s'
            if T != 'char':
                sub_fmts.append((i, f'<{arr_len}{type_map[T][1]}'))
        else:
            main_fmt += type_map[T][1]

    return main_fmt, sub_fmts


def update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            d[k] = update(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k] = d.get(k, []) + v
        else:
            d[k] = v
    return d

def load_xml(filename, mavlink_ver = 1, dir_='') -> dict:
    with open(os.path.join(dir_, filename), 'r') as f:
        xml = f.read()

    if mavlink_ver == 1:
        xml = re.sub('(\<extensions\/\>)[\s\S]*?(?=\<\/message\>)', '', xml)

    msgdef = xmltodict.parse(xml)
    # create a empty list to enable merge
    if msgdef['mavlink']['messages'] is None:
        msgdef['mavlink']['messages'] = {'message': []}
    if msgdef['mavlink']['enums'] is None:
        msgdef['mavlink']['enums'] = {'enum': []}

    includes = msgdef['mavlink']['include'] if 'include' in msgdef['mavlink'] else []
    includes = ensure_list(includes)

    for include in includes:
        more_def = load_xml(include, mavlink_ver, dir_)
        msgdef = update(msgdef, more_def)

    return msgdef

# TODO: make CLI program

def main(args):
    msgdef = load_xml(args.in_file, args.mavlink_version, args.xml_dir)

    enums = msgdef['mavlink']['enums']['enum'] if 'enums' in msgdef['mavlink'] else []
    enums = ensure_list(enums)

    messages = msgdef['mavlink']['messages']['message'] if 'messages' in msgdef['mavlink'] else []
    messages = ensure_list(messages)

    env = j2.Environment(loader=j2.FileSystemLoader('templates'))
    template = env.get_template('template.py.j2')

    with open(args.out_file, 'w') as f:
        f.write(template.render(
            enums=enums,
            messages=messages,
            reorder_fields = reorder_fields,
            resolve_type = resolve_type,
            resolve_fmt = resolve_fmt,
            ensure_list = ensure_list,
            to_camel_case = to_camel_case
        ))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', type=str, dest='in_file', default='common.xml')
    parser.add_argument('-o', type=str, dest='out_file', default='mavlink_messages.py')
    parser.add_argument('-d', type=str, dest='xml_dir', default='xml')
    parser.add_argument('-v', type=int, dest='mavlink_version', default=1)

    args = parser.parse_args()
    main(args)

IN_FILE = 'common.xml'
OUT_FILE = 'mavlink_messages.py'
MAVLINK_VER = 1.0

