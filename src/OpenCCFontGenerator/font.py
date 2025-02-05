from collections import defaultdict
from datetime import date
from itertools import chain, groupby
import json
from os import path
import subprocess

HERE = path.abspath(path.dirname(__file__))

# Define the max entries size in a subtable.
# We define a number that is small enough here, so that the entries will not exceed
# the size limit.
SUBTABLE_MAX_COUNT = 4000

# The following two functions are used to split a GSUB table into several subtables.


def grouper(iterable, n=SUBTABLE_MAX_COUNT):
    '''
    Split a list into chunks of size n.
    >>> list(grouper([1, 2, 3, 4, 5], n=2))
    [[1, 2], [3, 4], [5]]
    >>> list(grouper([1, 2, 3, 4, 5, 6], n=2))
    [[1, 2], [3, 4], [5, 6]]
    '''
    iterator = iter(iterable)
    while True:
        lst = []
        try:
            for _ in range(n):
                lst.append(next(iterator))
        except StopIteration:
            if lst:
                yield lst
            break
        yield lst


def grouper2(iterable, n=SUBTABLE_MAX_COUNT, key=None):
    '''
    Split a iterator into chunks of maximum size n by the given key.
    >>> list(grouper2(['AA', 'BBB', 'CCC', 'DDD', 'EE'], n=3, key=len))
    [['AA'], ['BBB', 'CCC', 'DDD'], ['EE']]
    >>> list(grouper2(['AA', 'BBB', 'CCC', 'DDD', 'EE'], n=2, key=len))
    [['AA'], ['BBB', 'CCC'], ['DDD'], ['EE']]
    '''
    for _, vx in groupby(iterable, key=key):
        for vs in grouper(vx, n):
            yield vs


# An opentype font can hold at most 65535 glyphs.
MAX_GLYPH_COUNT = 65535

# Here we are going to add a special key, cmap_rev, to the font object.
# This key is the reverse mapping of the cmap table and will be used in next steps.


def build_cmap_rev(obj):
    cmap_rev = defaultdict(list)
    for codepoint, glyph_name in obj['cmap'].items():
        cmap_rev[glyph_name].append(codepoint)
    return cmap_rev


def load_font(path, ttc_index=None):
    '''Load a font as a JSON object.'''
    ttc_index_args = () if ttc_index is None else ('--ttc-index', str(ttc_index))
    obj = json.loads(subprocess.check_output(
        ('otfccdump', path, *ttc_index_args)))
    obj['cmap_rev'] = build_cmap_rev(obj)
    return obj


def save_font(obj, path):
    '''Save a font object to file.'''
    del obj['cmap_rev']
    subprocess.run(('otfccbuild', '-o', path),
                   input=json.dumps(obj), encoding='utf-8')


def codepoint_to_glyph_name(obj, codepoint):
    '''Convert a codepoint to a glyph name in a font.'''
    return obj['cmap'][str(codepoint)]


def insert_empty_glyph(obj, name):
    '''Insert an empty glyph to a font with the given name.'''
    obj['glyf'][name] = {'advanceWidth': 0,
                         'advanceHeight': 1000, 'verticalOrigin': 880}
    obj['glyph_order'].append(name)


def get_glyph_count(obj):
    '''Get the total numbers of glyph in a font.'''
    return len(obj['glyph_order'])


def build_codepoints_han():
    '''Build a set of codepoints of Han characters to be included.'''
    with open(path.join(HERE, 'cache/code_points_han.txt')) as f:
        s = set()
        for line in f:
            s.add(int(line))
        return s


def build_codepoints_font(obj):
    '''Build a set of all the codepoints in a font.'''
    return set(map(int, obj['cmap']))


def build_codepoints_non_han():
    '''Build a set of codepoints of the needed non-Han characters in the final font.'''
    return set(chain(
        range(0x0020, 0x00FF + 1),
        range(0x02B0, 0x02FF + 1),
        range(0x2002, 0x203B + 1),
        range(0x2E00, 0x2E7F + 1),
        range(0x2E80, 0x2EFF + 1),
        range(0x3000, 0x301C + 1),
        range(0x3100, 0x312F + 1),
        range(0x3190, 0x31BF + 1),
        range(0xFE10, 0xFE1F + 1),
        range(0xFE30, 0xFE4F + 1),
        range(0xFF01, 0xFF5E + 1),
        range(0xFF5F, 0xFF60 + 1),
        range(0xFF61, 0xFF64 + 1),
    ))


def build_opencc_char_table(codepoints_font, twp=False):
    entries = []
    twp_suffix = '_twp' if twp else ''

    with open(path.join(HERE, f'cache/convert_table_chars{twp_suffix}.txt')) as f:
        for line in f:
            k, v = line.rstrip('\n').split('\t')
            codepoint_k = ord(k)
            codepoint_v = ord(v)
            if codepoint_k in codepoints_font \
                    and codepoint_v in codepoints_font:  # TODO FIXME: codepoint_k in codepoints_font should be unnecessary
                entries.append((codepoint_k, codepoint_v))

    return entries


def build_opencc_word_table(codepoints_font, twp=False):
    entries = []
    twp_suffix = '_twp' if twp else ''

    with open(path.join(HERE, f'cache/convert_table_words{twp_suffix}.txt')) as f:
        for line in f:
            k, v = line.rstrip('\n').split('\t')
            codepoints_k = tuple(ord(c) for c in k)
            codepoints_v = tuple(ord(c) for c in v)
            if all(codepoint in codepoints_font for codepoint in codepoints_k) \
                    and all(codepoint in codepoints_font for codepoint in codepoints_v):  # TODO FIXME: the first line should be unnecessary
                entries.append((codepoints_k, codepoints_v))

    # The entries are already Sorted from longest to shortest to force longest match
    return entries


def disassociate_codepoint_and_glyph_name(obj, codepoint, glyph_name):
    '''
    Remove a codepoint from the cmap table of a font object.

    Returns `True` if the codepoint is the only codepoint that is associated
    with the glyph. Otherwise returns `False`.
    '''
    # Remove glyph from cmap table
    del obj['cmap'][codepoint]

    is_only_item = obj['cmap_rev'][glyph_name] == [codepoint]

    # Remove glyph from cmap_rev
    if is_only_item:
        del obj['cmap_rev'][glyph_name]
    else:
        obj['cmap_rev'][glyph_name].remove(codepoint)

    return is_only_item


def remove_codepoint(obj, codepoint):
    '''Remove a codepoint from a font object.'''
    codepoint = str(codepoint)

    glyph_name = obj['cmap'].get(codepoint)
    if not glyph_name:
        return  # The codepoint is not associated with a glyph name. No action is needed

    is_only_item = disassociate_codepoint_and_glyph_name(
        obj, codepoint, glyph_name)
    if is_only_item:
        remove_glyph(obj, glyph_name)


def remove_codepoints(obj, codepoints):
    '''Remove a sequence of codepoints from a font object.'''
    for codepoint in codepoints:
        remove_codepoint(obj, codepoint)


def remove_associated_codepoints_of_glyph(obj, glyph_name):
    '''Remove a glyph from the cmap table of a font object.'''
    # Remove glyph from cmap table
    for codepoint in obj['cmap_rev'][glyph_name]:
        del obj['cmap'][codepoint]

    # Remove glyph from cmap_rev
    del obj['cmap_rev'][glyph_name]


def remove_glyph(obj, glyph_name):
    '''Remove a glyph from all the tables except the cmap table of a font object.'''
    # Remove glyph from glyph_order table
    try:
        obj['glyph_order'].remove(glyph_name)
    except ValueError:
        pass

    # Remove glyph from glyf table
    obj['glyf'].pop(glyph_name, None)

    # Remove glyph from GSUB table
    for lookup in obj.get('GSUB', {}).get('lookups', {}).values():
        if lookup['type'] == 'gsub_single':
            for subtable in lookup['subtables']:
                subtable.pop(glyph_name, None)
                # 反向替换中可能也需要删除
                for key in list(subtable.keys()):
                    if subtable[key] == glyph_name:
                        subtable.pop(key)
        elif lookup['type'] == 'gsub_alternate':
            for subtable in lookup['subtables']:
                subtable.pop(glyph_name, None)
                for key, alternates in list(subtable.items()):
                    if glyph_name in alternates:
                        alternates.remove(glyph_name)
                    if key == glyph_name:
                        subtable.pop(key)
        elif lookup['type'] == 'gsub_ligature':
            for subtable in lookup['subtables']:
                subtable['substitutions'] = [
                    s for s in subtable['substitutions']
                    if glyph_name not in s['from'] and glyph_name != s['to']
                ]
        else:
            print(f"Unknown GSUB lookup type: {lookup['type']}")
            # 如果需要，可以选择跳过或添加处理逻辑
            # raise NotImplementedError(f"Unknown GSUB lookup type: {lookup['type']}")

    # Remove glyph from GPOS table
    for lookup in obj.get('GPOS', {}).get('lookups', {}).values():
        if lookup['type'] == 'gpos_single':
            for subtable in lookup['subtables']:
                subtable.pop(glyph_name, None)
        elif lookup['type'] == 'gpos_pair':
            for subtable in lookup['subtables']:
                subtable['first'].pop(glyph_name, None)
                subtable['second'].pop(glyph_name, None)
        elif lookup['type'] == 'gpos_mark_to_base':
            for subtable in lookup['subtables']:
                subtable['marks'].pop(glyph_name, None)
                subtable['bases'].pop(glyph_name, None)
        elif lookup['type'] == 'gpos_mark_to_mark':
            for subtable in lookup['subtables']:
                subtable['marks'].pop(glyph_name, None)
                subtable['mark2s'].pop(glyph_name, None)
        elif lookup['type'] == 'gpos_mark_to_ligature':
            for subtable in lookup['subtables']:
                subtable['marks'].pop(glyph_name, None)
                for anchors in subtable['bases'].values():
                    for anchor in anchors.values():
                        anchor.pop(glyph_name, None)
        elif lookup['type'] == 'gpos_cursive':
            for subtable in lookup['subtables']:
                subtable.pop(glyph_name, None)
        elif lookup['type'] == 'gpos_context':
            for subtable in lookup['subtables']:
                # 检查 'rules' 是否在 subtable 中
                if 'rules' in subtable:
                    subtable['rules'] = [
                        rule for rule in subtable['rules']
                        if glyph_name not in rule.get('input', []) and
                           glyph_name not in rule.get('lookups', [])
                    ]
                elif 'coverage' in subtable and 'pos' in subtable:
                    # Format 3: Coverage-based Contextual Positioning
                    if glyph_name in subtable['coverage']:
                        index = subtable['coverage'].index(glyph_name)
                        subtable['coverage'].pop(index)
                        subtable['pos'].pop(index)
                elif 'classes' in subtable:
                    # Format 2: Class-based Contextual Positioning
                    for class_list in subtable['classes']:
                        if glyph_name in class_list:
                            class_list.remove(glyph_name)
                else:
                    # 未知格式，打印调试信息或添加处理
                    print(f"Unknown subtable format in gpos_context: {subtable.keys()}")
        elif lookup['type'] == 'gpos_chaining':
            for subtable in lookup['subtables']:
                if 'rules' in subtable:
                    subtable['rules'] = [
                        rule for rule in subtable['rules']
                        if glyph_name not in rule.get('input', []) and
                           glyph_name not in rule.get('backtrack', []) and
                           glyph_name not in rule.get('lookahead', []) and
                           glyph_name not in rule.get('lookups', [])
                    ]
                else:
                    # 处理其他可能的结构
                    print(f"Unknown subtable format in gpos_chaining: {subtable.keys()}")
        else:
            print(f"Unknown GPOS lookup type: {lookup['type']}")
            # 如果需要，可以选择跳过或添加处理逻辑
            # raise NotImplementedError(f"Unknown GPOS lookup type: {lookup['type']}")

    # Remove glyph from BASE table if present
    if 'BASE' in obj:
        base_table = obj['BASE']
        for axis in base_table.get('HorizAxis', {}).get('BaseTagList', {}).get('BaseScriptList', {}).values():
            for base_lang_sys in axis.values():
                for base_record in base_lang_sys.get('BaseValues', []):
                    if glyph_name in base_record.get('BaseCoord', {}):
                        base_record['BaseCoord'].pop(glyph_name, None)

    # Remove glyph from other tables as needed

def get_reachable_glyphs(obj):
    '''Get all the reachable glyphs of a font object.'''
    reachable_glyphs = {'.notdef', '.null'}

    for glyph_name in obj['cmap'].values():
        # Add the glyph in cmap table
        reachable_glyphs.add(glyph_name)

        # Add the glyphs referenced by the glyph in cmap table
        for lookup in obj['GSUB']['lookups'].values():
            if lookup['type'] == 'gsub_single':  # {a: b}
                for subtable in lookup['subtables']:
                    for k, v in subtable.items():
                        if glyph_name == k:
                            reachable_glyphs.add(v)
            elif lookup['type'] == 'gsub_alternate':  # {a: [b1, b2, ...]}
                for subtable in lookup['subtables']:
                    for k, vs in subtable.items():
                        if glyph_name == k:
                            reachable_glyphs.update(vs)
            # {from: [a1, a2, ...], to: b}
            elif lookup['type'] == 'gsub_ligature':
                for subtable in lookup['subtables']:
                    for item in subtable['substitutions']:
                        if glyph_name in item['from']:
                            reachable_glyphs.add(item['to'])
            else:
                raise NotImplementedError('Unknown GSUB lookup type')

    return reachable_glyphs


def clean_unused_glyphs(obj):
    reachable_glyphs = get_reachable_glyphs(obj)
    all_glyphs = set(obj['glyph_order'])
    for glyph_name in all_glyphs - reachable_glyphs:
        remove_associated_codepoints_of_glyph(obj, glyph_name)
        remove_glyph(obj, glyph_name)


def insert_empty_feature(obj, feature_name):
    for table in obj['GSUB']['languages'].values():
        table['features'].append(feature_name)
    obj['GSUB']['features'][feature_name] = []


def create_word2pseu_table(obj, feature_name, conversions):
    def conversion_item_len(conversion_item): return len(conversion_item[0])
    subtables = [{'substitutions': [{'from': glyph_names_k, 'to': pseudo_glyph_name} for glyph_names_k, pseudo_glyph_name in subtable]}
                 for subtable in grouper2(conversions, key=conversion_item_len)]  # {from: [a1, a2, ...], to: b}
    obj['GSUB']['features'][feature_name].append('word2pseu')
    obj['GSUB']['lookups']['word2pseu'] = {
        'type': 'gsub_ligature',
        'flags': {},
        'subtables': subtables
    }
    obj['GSUB']['lookupOrder'].append('word2pseu')


def create_char2char_table(obj, feature_name, conversions):
    subtables = [{k: v for k, v in subtable}
                 for subtable in grouper(conversions)]
    obj['GSUB']['features'][feature_name].append('char2char')
    obj['GSUB']['lookups']['char2char'] = {
        'type': 'gsub_single',
        'flags': {},
        'subtables': subtables
    }
    obj['GSUB']['lookupOrder'].append('char2char')


def create_pseu2word_table(obj, feature_name, conversions):
    def conversion_item_len(conversion_item): return len(conversion_item[1])
    subtables = [{k: v for k, v in subtable}
                 for subtable in grouper2(conversions, key=conversion_item_len)]
    obj['GSUB']['features'][feature_name].append('pseu2word')
    obj['GSUB']['lookups']['pseu2word'] = {
        'type': 'gsub_multiple',
        'flags': {},
        'subtables': subtables
    }
    obj['GSUB']['lookupOrder'].append('pseu2word')


def build_name_header(name_header_file, style, version, date):
    with open(name_header_file) as f:
        name_header = json.load(f)

    for item in name_header:
        item['nameString'] = item['nameString'] \
            .replace('<Typographic Subfamily Name>', style) \
            .replace('<Version>', version) \
            .replace('<Date>', date)

    return name_header


def modify_metadata(obj, name_header_file, font_version: float):
    styles = [item['nameString'] for item in obj['name'] if item['nameID'] in [17, 2]]
    if styles:
        style = styles[0]
    else:
        style = 'Regular'
    today = date.today().strftime('%b %d, %Y')

    name_header = build_name_header(
        name_header_file, style, str(font_version), today)

    obj['head']['fontRevision'] = font_version
    obj['name'] = name_header


def build_font(input_file, output_file, name_header_file, font_version, ttc_index=None, twp=False):
    font = load_font(input_file, ttc_index=ttc_index)

    # Determine the final Unicode range by the original font and OpenCC convert tables

    codepoints_font = build_codepoints_font(font)
    entries_char = build_opencc_char_table(codepoints_font, twp=twp)
    entries_word = build_opencc_word_table(codepoints_font, twp=twp)

    codepoints_final = (build_codepoints_non_han() |
                        build_codepoints_han()) & codepoints_font

    remove_codepoints(font, codepoints_font - codepoints_final)
    clean_unused_glyphs(font)

    available_glyph_count = MAX_GLYPH_COUNT - get_glyph_count(font)
    assert available_glyph_count >= len(entries_word)

    # Build glyph substitution tables and insert into font

    word2pseu_table = []
    char2char_table = []
    pseu2word_table = []

    for i, (codepoints_k, codepoints_v) in enumerate(entries_word):
        pseudo_glyph_name = 'pseu%X' % i
        glyph_names_k = [codepoint_to_glyph_name(
            font, codepoint) for codepoint in codepoints_k]
        glyph_names_v = [codepoint_to_glyph_name(
            font, codepoint) for codepoint in codepoints_v]
        insert_empty_glyph(font, pseudo_glyph_name)
        word2pseu_table.append((glyph_names_k, pseudo_glyph_name))
        pseu2word_table.append((pseudo_glyph_name, glyph_names_v))

    for codepoint_k, codepoint_v in entries_char:
        glyph_name_k = codepoint_to_glyph_name(font, codepoint_k)
        glyph_name_v = codepoint_to_glyph_name(font, codepoint_v)
        char2char_table.append((glyph_name_k, glyph_name_v))

    feature_name = 'liga_s2t'
    insert_empty_feature(font, feature_name)
    create_word2pseu_table(font, feature_name, word2pseu_table)
    create_char2char_table(font, feature_name, char2char_table)
    create_pseu2word_table(font, feature_name, pseu2word_table)

    modify_metadata(font, name_header_file, font_version)
    save_font(font, output_file)
