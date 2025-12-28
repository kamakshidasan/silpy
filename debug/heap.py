import networkx as nx
import matplotlib.pyplot as plt
from ..debug.palette import get_color_palette

########################################################

def visualize_union_find(union_find_instance):
    # build a mapping from each representative to its member nodes
    groups = union_find_instance.get_groups()
    # initialize an undirected graph object
    graph = nx.Graph()

    # add nodes tagged by their group and connect them sequentially
    for representative, member_list in groups.items():
        for member in member_list:
            graph.add_node(member, group=representative)
        for first_member, second_member in zip(member_list, member_list[1:]):
            graph.add_edge(first_member, second_member)

    # choose a distinct color for each group representative
    representatives = list(groups.keys())
    distinct_color_palette = get_color_palette(
        number_of_colors=len(representatives),
        base_palette_name="muted",
        max_base_colors=10
    )

    # map each representative to its assigned hex color
    color_mapping_by_representative = {
        representative: distinct_color_palette[index]
        for index, representative in enumerate(representatives)
    }

    # separate nodes into those that are representatives vs others
    representative_nodes = []
    non_representative_node_list = []
    for representative, member_list in groups.items():
        for member in member_list:
            if member == representative:
                representative_nodes.append(member)
            else:
                non_representative_node_list.append(member)

    # compute positions for all nodes using a force-directed layout
    node_positions = nx.spring_layout(graph, k=0.3, seed=42)

    # draw non-representative nodes as circles with appropriate colors
    nx.draw_networkx_nodes(
        graph,
        node_positions,
        nodelist=non_representative_node_list,
        node_color=[
            color_mapping_by_representative[union_find_instance.find(member)]
            for member in non_representative_node_list
        ],
        node_shape="o",
        node_size=300
    )
    # draw representative nodes as squares with the same mapping
    nx.draw_networkx_nodes(
        graph,
        node_positions,
        nodelist=representative_nodes,
        node_color=[
            color_mapping_by_representative[union_find_instance.find(member)]
            for member in representative_nodes
        ],
        node_shape="s",
        node_size=300
    )

    # draw connecting edges between nodes
    nx.draw_networkx_edges(graph, node_positions)
    # label each node for clarity
    nx.draw_networkx_labels(graph, node_positions, font_color="white")

    # render the complete visualization
    plt.show()

########################################################

def visualize_heap_manager(heap_manager_instance):
    heaps = heap_manager_instance.heaps
    graph = nx.Graph()
    node_to_root = {}

    # add each root and its heap nodes
    for root, heap_list in heaps.items():
        graph.add_node(root, label=f"Root {root}", root=True)
        for element in heap_list:
            node_value, node_index = element.value, element.index
            graph.add_node(node_index, label=f"{round(float(node_value),3), node_index}")
            graph.add_edge(root, node_index)
            node_to_root[node_index] = root

    # pick distinct colors for each root
    roots = list(heaps.keys())

    palette = get_color_palette(
        number_of_colors=len(roots),
        base_palette_name="muted",
        max_base_colors=10
    )

    color_map = {root: palette[index] for index, root in enumerate(roots)}

    # split nodes by root vs heap nodes
    heap_nodes = [node for node in graph.nodes if node not in roots]

    positions = nx.spring_layout(graph, k=0.5, seed=42)

    # draw heap nodes
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=heap_nodes,
        node_color=[color_map[node_to_root[node]] for node in heap_nodes],
        node_shape='o',
        node_size=200
    )

    # draw roots
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=roots,
        node_color=[color_map[root] for root in roots],
        node_shape='s',
        node_size=200
    )

    nx.draw_networkx_edges(graph, positions)
    nx.draw_networkx_labels(
        graph,
        positions,
        labels={node: node_attributes['label'] for node, node_attributes in graph.nodes(data=True)},
        font_color='black'
    )
    plt.show()
