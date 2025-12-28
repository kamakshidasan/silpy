import re
import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
from ..debug.palette import get_color_palette, get_node_color
from ..formatter.value_formatter import ValueFormatter
from IPython.display import display, HTML

########################################################

def visualize_tree_pairs(tree, node_pairs, step, label=None, reverse=False, use_node_type_colors=True, node_size=500, font_size=6):
    fig, ax = plt.subplots()

    graph = nx.DiGraph(tree)
    if reverse:
        graph = graph.reverse(copy=False)

    pos = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    nodes = list(graph.nodes)

    color_map = get_color_palette(
        number_of_colors=len(node_pairs),
        base_palette_name="tab20",
        max_base_colors=8
    )

    # map: node -> list of (partner_node, color)
    node_color_info = {}
    for index, (birth, death) in enumerate(node_pairs):
        color = color_map[index]
        # at the birth node we color by its death-partner
        node_color_info.setdefault(birth, []).append((death, color))
        # at the death node we color by its birth-partner
        node_color_info.setdefault(death, []).append((birth, color))

    # “gray out” everything up to step, keeping partner logic
    for birth, death in node_pairs[:step]:
        birth_entries = node_color_info.get(birth, [])
        for list_position, (partner_node, partner_color) in enumerate(birth_entries):
            if partner_node == death:
                birth_entries[list_position] = (partner_node, 'gray')
                break

        death_entries = node_color_info.get(death, [])
        for list_position, (partner_node, partner_color) in enumerate(death_entries):
            if partner_node == birth:
                death_entries[list_position] = (partner_node, 'gray')
                break

    # draw edges
    nx.draw_networkx_edges(graph, pos=pos, ax=ax, arrows=True)

    # compute pie size in figure‐fraction from node_size
    point_radius = (node_size ** 0.5) / 2
    radius_inches = point_radius / 72
    figure_width, figure_height = fig.get_size_inches()
    width_fraction = (2 * radius_inches) / figure_width
    height_fraction = (2 * radius_inches) / figure_height

    label_key = label if label else 'index'

    for node in nodes:
        x, y = pos[node]
        dx, dy = ax.transData.transform((x, y))
        figure_x, figure_y = fig.transFigure.inverted().transform((dx, dy))

        # inset axes for the pie
        pie_ax = fig.add_axes(
            [figure_x - width_fraction/2, figure_y - height_fraction/2, width_fraction, height_fraction],
            frameon=False
        )

        # get list of (partner_node, color) or single gray slice
        partner_color_pairs = node_color_info.get(node, [])
        if any(color != 'gray' for (_partner_node, color) in partner_color_pairs):
            partner_color_pairs = [pair for pair in partner_color_pairs if pair[1] != 'gray']
        if not partner_color_pairs:
            partner_color_pairs = [(node, 'gray')]
        # sort by partner ascending → largest partner last (drawn on top)
        partner_color_pairs.sort(
            key=lambda partner_color_pair: partner_color_pair[0],
            reverse=True
        )

        # extract colors for the pie slices
        slice_colors = [color for (_partner_node, color) in partner_color_pairs]

        pie_ax.pie([1] * len(slice_colors), colors=slice_colors)
        pie_ax.set_aspect('equal')
        pie_ax.axis('off')

        # label at center
        label = node.label(label_key)
        pie_ax.text(
            0.5, 0.5, label,
            ha='center', va='center',
            fontsize=font_size, color='white',
            transform=pie_ax.transAxes
        )

    ax.set_axis_off()
    plt.show()

########################################################


def visualize_attribute_tree(
    tree, edge_attribute=None, pairs=None,
    label=None, reverse=False, use_node_type_colors=True,
    node_size=900, font_size=6, edge_width=2.0,
):
    graph = nx.DiGraph(tree)

    if reverse:
        graph = graph.reverse(copy=False)

    layout_positions = nx.nx_agraph.graphviz_layout(graph, prog="dot")
    nodes = list(graph.nodes)

    if hasattr(tree, "arcs"):
        arcs_dict = tree.arcs
        arc_colors = get_color_palette(
            number_of_colors=len(arcs_dict),
            base_palette_name="muted",
            max_base_colors=8
        )
        arc_to_color = {arc_key: arc_colors[index] for index, arc_key in enumerate(arcs_dict.keys())}
        edge_color_list = [arc_to_color[(start_node, end_node)] for start_node, end_node in graph.edges()]
    else:
        edge_list = list(graph.edges())
        edge_colors = get_color_palette(
            number_of_colors=len(edge_list),
            base_palette_name="muted",
            max_base_colors=8
        )
        edge_color_list = [edge_colors[index] for index, edge_pair in enumerate(edge_list)]

    label_key = label if label else "index"
    label_mapping = {node_item: node_item.label(label_key) for node_item in nodes}

    if pairs is None:
        plt.figure()

        if use_node_type_colors:
            node_color_list = [get_node_color(node_item.type) for node_item in nodes]
        else:
            node_color_list = get_color_palette(
                number_of_colors=len(nodes),
                base_palette_name="muted",
                max_base_colors=20
            )

        nx.draw(
            graph,
            layout_positions,
            labels=label_mapping,
            node_color=node_color_list,
            with_labels=True,
            node_size=node_size,
            font_size=font_size,
            font_color="white",
            edge_color=edge_color_list,
            width=edge_width
        )

        axes_for_labels = plt.gca()

    else:
        # if you want pairs, then you want to have the circles as pies
        fig, ax = plt.subplots()

        nx.draw_networkx_edges(
            graph,
            pos=layout_positions,
            ax=ax,
            arrows=True,
            edge_color=edge_color_list,
            width=edge_width
        )

        color_map = get_color_palette(
            number_of_colors=len(pairs),
            base_palette_name="tab20",
            max_base_colors=8
        )

        node_color_info = {}
        for index, (birth, death) in enumerate(pairs):
            color = color_map[index]
            node_color_info.setdefault(birth, []).append((death, color))
            node_color_info.setdefault(death, []).append((birth, color))

        node_size *= 1.8 # when you have the pies, the normal node size decreases
        point_radius = (node_size ** 0.5) / 2
        radius_inches = point_radius / 72
        figure_width, figure_height = fig.get_size_inches()
        width_fraction = (2 * radius_inches) / figure_width
        height_fraction = (2 * radius_inches) / figure_height

        for node in nodes:
            x, y = layout_positions[node]
            dx, dy = ax.transData.transform((x, y))
            figure_x, figure_y = fig.transFigure.inverted().transform((dx, dy))

            pie_ax = fig.add_axes(
                [figure_x - width_fraction/2, figure_y - height_fraction/2, width_fraction, height_fraction],
                frameon=False
            )

            partner_color_pairs = node_color_info.get(node) or [(node, 'gray')]
            partner_color_pairs.sort(
                key=lambda partner_color_pair: partner_color_pair[0],
                reverse=True
            )

            slice_colors = [color for (_partner_node, color) in partner_color_pairs]

            pie_ax.pie([1] * len(slice_colors), colors=slice_colors)
            pie_ax.set_aspect('equal')
            pie_ax.axis('off')

            node_text = node.label(label_key)
            pie_ax.text(
                0.5, 0.5, node_text,
                ha='center', va='center',
                fontsize=font_size, color='white',
                transform=pie_ax.transAxes
            )

        ax.set_axis_off()
        axes_for_labels = ax

    if edge_attribute is not None:
        edge_label_mapping = {}
        for start_node, end_node in graph.edges():
            attribute_value = graph[start_node][end_node][edge_attribute]
            edge_label_mapping[(start_node, end_node)] = ValueFormatter.format(attribute_value)

        nx.draw_networkx_edge_labels(
            graph,
            layout_positions,
            edge_labels=edge_label_mapping,
            font_size=font_size,
            ax=axes_for_labels
        )

    plt.show()

########################################################


def visualize_pairs_bar_graph(node_pairs, values, step, crop=False, show_labels=True):
    total = len(node_pairs)
    assert -total <= step <= total

    if step < 0:
        step = total + step

    color_map = get_color_palette(
        number_of_colors=total,
        base_palette_name="tab20",
        max_base_colors=8
    )

    if crop:
        selected_indices = list(range(step, total))
        selected_pairs = [node_pairs[index] for index in selected_indices]
        pair_labels = [f"({birth.index},{death.index})" for birth, death in selected_pairs]
        bar_colors = [color_map[index] for index in selected_indices]
        raw_values = [values[index] for index in selected_indices]
    else:
        pair_labels = [f"({birth.index},{death.index})" for birth, death in node_pairs]
        bar_colors = color_map[:]
        if step > 0:
            for index in range(step):
                bar_colors[index] = 'gray'
        raw_values = values

    epsilon = 1e-5
    clipped_values = [max(value, epsilon) for value in raw_values]

    plt.figure(figsize=(6, 4))
    plt.bar(range(len(clipped_values)), clipped_values, color=bar_colors)
    plt.yscale('log')

    plt.xlabel("Pairs", fontsize=12)
    plt.ylabel("Score (Log Scale)", fontsize=12)
    plt.xticks(range(len(clipped_values)), pair_labels, rotation=45, ha='right', fontsize=10)

    if show_labels:
        for index, original_value in enumerate(raw_values):
            if original_value > epsilon:
                plt.text(index, clipped_values[index], ValueFormatter.format(original_value), ha='center', va='bottom', fontsize=9)
            else:
                plt.text(index, clipped_values[index], "≤ ε", ha='center', va='bottom', fontsize=9)
    plt.show()

########################################################

def visualize_pairs_scatter_plot(node_pairs, step, crop=False, show_labels=True, score='scalar'):
    total = len(node_pairs)
    assert -total <= step <= total

    if step < 0:
        step = total + step

    color_map = get_color_palette(
        number_of_colors=total,
        base_palette_name="tab20",
        max_base_colors=8
    )

    if crop:
        selected_indices = list(range(step, total))
        selected_pairs = [node_pairs[index] for index in selected_indices]
        point_colors = [color_map[index] for index in selected_indices]
    else:
        selected_pairs = node_pairs
        point_colors = color_map[:]
        if step > 0:
            for index in range(step):
                point_colors[index] = 'gray'

    x_values = [birth[score] for birth, death in selected_pairs]
    y_values = [death[score] for birth, death in selected_pairs]
    differences = [y - x for x, y in zip(x_values, y_values)]
    bar_heights = [x - y for x, y in zip(x_values, y_values)]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x_values, y_values, color=point_colors)

    # draw y = x reference line
    x_min, x_max = ax.get_xlim()
    ax.plot([x_min, x_max], [x_min, x_max], linestyle='--', zorder=0)

    # draw vertical bars from each point to the diagonal with small width
    bar_width = 0.0065
    ax.bar(x_values, bar_heights, bottom=y_values, width=bar_width, color=point_colors, align='center')

    # plot projection points (x, x) on the diagonal
    ax.scatter(x_values, x_values, color=point_colors)

    plt.xlabel(f"Birth [{score}]", fontsize=12)
    plt.ylabel(f"Death [{score}]", fontsize=12)

    # expand y-axis limits to fit text labels if labels will be shown
    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min, y_max + (y_max - y_min) * 0.05)
    vertical_offset = 0.02

    # add labels only if requested
    if show_labels:
        epsilon = 1e-5
        for index, difference in enumerate(differences):
            if difference > epsilon * 1.2:
                x_value = x_values[index]
                y_value = y_values[index]
                ax.text(
                    x_value,
                    y_value + vertical_offset,
                    ValueFormatter.format(difference),
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    clip_on=False
                )

    plt.tight_layout(pad=1.2)
    plt.show()

########################################################

def visualize_pairs_line_chart(node_pairs, values, step, crop=False, show_labels=True):
    total = len(node_pairs)
    assert -total <= step <= total

    if step < 0:
        step = total + step

    color_map = get_color_palette(
        number_of_colors=total,
        base_palette_name="tab20",
        max_base_colors=8
    )

    if crop:
        selected_indices = list(range(step, total))
        selected_pairs = [node_pairs[index] for index in selected_indices]
        pair_labels = [f"({birth.index},{death.index})" for birth, death in selected_pairs]
        raw_values = [values[index] for index in selected_indices]
        bar_colors = [color_map[index] for index in selected_indices]
    else:
        pair_labels = [f"({birth.index},{death.index})" for birth, death in node_pairs]
        raw_values = values
        bar_colors = color_map[:]

    display_pair_labels = list(reversed(pair_labels))
    display_values = list(reversed(raw_values))
    display_colors = list(reversed(bar_colors))

    number_of_points = len(display_values)
    display_positions = list(range(number_of_points))

    plt.figure(figsize=(6, 4))

    # Draw the base line for the whole series
    plt.plot(display_positions, display_values)

    # Determine and grey-out the stepped segment when not cropping
    if not crop and step > 0 and number_of_points > 0:
        grey_count = min(step, number_of_points)
        grey_start_position = number_of_points - grey_count

        # Grey line segment for the stepped region
        plt.plot(
            display_positions[grey_start_position:],
            display_values[grey_start_position:],
            color='gray'
        )

        # Grey markers for the stepped region
        for position_index in range(grey_start_position, number_of_points):
            display_colors[position_index] = 'gray'

    # Colored markers point-by-point
    plt.scatter(display_positions, display_values, c=display_colors, zorder=3)

    plt.xlabel("Pairs", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.xticks(display_positions, display_pair_labels, rotation=45, ha='right', fontsize=10)

    if show_labels and number_of_points > 0:
        plt.margins(y=0.1)
        for position_index, value_at_point in enumerate(display_values):
            plt.annotate(
                ValueFormatter.format(value_at_point),
                xy=(position_index, value_at_point),
                xytext=(0, 6),
                textcoords='offset points',
                ha='center',
                va='bottom',
                clip_on=True,
                fontsize=9
            )

    plt.show()
########################################################
