import glasbey
import seaborn as sns
import matplotlib as mpl

########################################################

def get_color_palette(number_of_colors, base_palette_name="muted", max_base_colors=None):
    if max_base_colors is None:
        base_rgb_list = sns.color_palette(base_palette_name)
    else:
        base_rgb_list = sns.color_palette(base_palette_name, max_base_colors)

    base_hex_list = [mpl.colors.to_hex(rgb_tuple) for rgb_tuple in base_rgb_list]
    if number_of_colors <= len(base_hex_list):
        return base_hex_list[:number_of_colors]

    extension_parameters = {
        "palette_size": number_of_colors,
        "as_hex": True
    }

    return glasbey.extend_palette(base_hex_list, **extension_parameters)

########################################################

def get_node_color(node_type):
    color_mapping = {
        'maximum': 'red',
        'minimum': 'blue',
        'join':    'hotpink',
        'split':   'orange',
        'both':    'green',
    }
    return color_mapping.get(node_type, 'grey')

########################################################
