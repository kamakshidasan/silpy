import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from ..debug.palette import get_color_palette
from ..formatter.value_formatter import ValueFormatter

########################################################

def visualize_branch_hierarchy(tree_graph, branches, all_branches, scheme, step, label=None, reverse=False, node_size=500):
    total = len(tree_graph.nodes)
    assert -total <= step <= total

    # Use the passed Tree's underlying DiGraph
    hierarchy_graph = tree_graph.reverse(copy=True) if reverse else tree_graph

    # Layout with orthogonal routing via Graphviz
    positions = nx.nx_agraph.graphviz_layout(hierarchy_graph, prog="dot")

    node_pairs = [(branch.birth, branch.death) for branch in all_branches]

    # Color each branch-pair, gray out up to 'step'
    palette = get_color_palette(
        number_of_colors=len(all_branches),
        base_palette_name="tab20",
        max_base_colors=8
    )

    node_colors = {branch: palette[index] for index, branch in enumerate(all_branches)}
    for branch in branches[:step]:
        node_colors[branch] = 'gray'

    # Build labels based on provided key (default 'index')
    label_key = label if label else 'index'

    if label == scheme:
        labels = {}
        for branch in hierarchy_graph.nodes():
            value = branch.value
            value_string = ValueFormatter.format(value)
            labels[branch] = value_string

    # to print out a branch's label (like order)
    # clearly, this elif came later
    elif label is not None and all(hasattr(branch, label) for branch in hierarchy_graph.nodes()):
        labels = {}
        for branch in hierarchy_graph.nodes():
            attribute_value = getattr(branch, label)
            attribute_value = attribute_value() if callable(attribute_value) else attribute_value
            value_string = ValueFormatter.format(attribute_value)
            labels[branch] = value_string
    else:
        labels = {}
        for branch in hierarchy_graph.nodes():
            birth, death = branch.birth, branch.death
            birth_string = birth.label(label_key)
            death_string = death.label(label_key)
            value_string = f"({birth_string}, {death_string})"
            labels[branch] = value_string

    color_list = [node_colors[node] for node in hierarchy_graph.nodes()]

    # Draw and show
    plt.figure()
    nx.draw(
        hierarchy_graph,
        positions,
        labels=labels,
        node_color=color_list,
        with_labels=True,
        node_size=node_size,
        font_size=6,
        font_color='white'
    )
    plt.show()





########################################################


def visualize_branches_horizontal_toporerry(
    branch_hierarchy,
    base_dx=1.0,
    dy=None,
    circle_size=50,
    flip=False,
    reverse=False,
    connector_linestyle='dotted',
    grid_color='lightgray',
    grid_alpha=0.5
):
    # prepare figure and axis
    fig, ax = plt.subplots()

    # compute branch traversal and positions
    traversal_order = branch_hierarchy.traverse_descending()
    position_map = {pair: index * base_dx for index, pair in enumerate(traversal_order)}

    # collect all y-values for automatic dy
    y_values = []

    # build color maps
    all_branches = branch_hierarchy.all_branches

    palette = get_color_palette(
        number_of_colors=len(all_branches),
        base_palette_name="tab20",
        max_base_colors=8
    )

    node_color_map = {}

    for index, branch in enumerate(all_branches):
        for node in [branch.birth, branch.death]:
            node_color_map[node] = palette[index]


    branch_color_map = {pair: palette[index] for index, pair in enumerate(all_branches)}

    birth_y_map = {}

    # plot each branch
    for branch in traversal_order:
        birth_node, death_node = branch.birth, branch.death
        x = position_map[branch]
        y_death = death_node.scalar if flip else birth_node.scalar
        y_birth = birth_node.scalar if flip else death_node.scalar
        y_values.extend([y_death, y_birth])

        # vertical segment
        y_min, y_max = min(y_death, y_birth), max(y_death, y_birth)
        ax.plot([x, x], [y_min, y_max], color=branch_color_map[branch], linewidth=3)

        # endpoint markers
        ax.scatter([x], [y_death], s=circle_size, color=node_color_map[death_node], zorder=3)
        ax.scatter([x], [y_birth], s=circle_size, color=node_color_map[birth_node], zorder=3)

        birth_y_map[branch] = y_birth

    # set locators and grid
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(MultipleLocator(base_dx))
    if dy is None:
        unique_y = sorted(set(y_values))
        differences = [j - i for i, j in zip(unique_y, unique_y[1:]) if j > i]
        if differences:
            step = min(differences)
            ax.yaxis.set_major_locator(MultipleLocator(step))
    else:
        ax.yaxis.set_major_locator(MultipleLocator(dy))
    ax.grid(True, color=grid_color, alpha=grid_alpha)

    # if reverse, lock in autoscaled y-limits and invert axis
    if reverse:
        ax.relim()
        ax.autoscale_view(scalex=False, scaley=True, tight=False)
        y0, y1 = ax.get_ylim()
        ax.set_ylim(y1, y0)

    # plot connectors
    for child_pair, parent_pair in branch_hierarchy.branch_parent.items():
        if parent_pair is None:
            continue
        child_x = position_map[child_pair]
        parent_x = position_map[parent_pair]
        connector_y = birth_y_map[child_pair]
        ax.plot(
            [parent_x, child_x], [connector_y, connector_y],
            linestyle=connector_linestyle,
            linewidth=2,
            color=branch_color_map[child_pair]
        )

    ax.set_xlabel("Branch traversal position")
    ax.set_ylabel("Pair score")

    plt.show()

########################################################
