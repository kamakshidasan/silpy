import networkx as nx
import matplotlib.pyplot as plt
import math

########################################################

# This works only in 2D because of the coordinates
def visualize_point_link_2d(point):
    # Create an empty graph
    point_graph = nx.Graph()

    # Dictionaries to hold node positions and their labels
    node_positions = {}
    node_labels = {}

    # Add the central point as a node
    central_x, central_y = point.coordinates[:2]
    central_index = point.index
    point_graph.add_node(central_index, role='central')
    node_positions[central_index] = (central_x, central_y)
    node_labels[central_index] = f"{central_index}\n{point.scalar:.3f}"

    def add_link_points(link_point_collections, link_role):
        """
        Add each point in the collections to the graph,
        with a solid edge back to the central node.
        """
        for point_collection in link_point_collections:
            for link_point in point_collection:
                link_index = link_point.index
                link_x, link_y = link_point.coordinates[:2]

                point_graph.add_node(link_index, role=link_role)
                node_positions[link_index] = (link_x, link_y)
                node_labels[link_index] = f"{link_index}\n{link_point.scalar:.3f}"

                # Draw a solid connection from the central node to this link node
                point_graph.add_edge(central_index, link_index, connection_style='solid')

    # Add nodes and solid edges for lower and upper links
    add_link_points(point.lower_link, link_role='lower')
    add_link_points(point.upper_link, link_role='upper')

    # Add dashed edges for neighbor relationships in the underlying link_graph
    for first_neighbor, second_neighbor in point.link_graph.edges():
        point_graph.add_edge(
            first_neighbor.index,
            second_neighbor.index,
            connection_style='dashed'
        )

    # Draw the nodes, grouping by their role
    for node_role, outline_color in [
        ('central', 'purple'),
        ('lower', 'blue'),
        ('upper', 'red')
    ]:
        nodes_of_role = [
            node_id
            for node_id, attributes in point_graph.nodes(data=True)
            if attributes.get('role') == node_role
        ]
        nx.draw_networkx_nodes(
            point_graph,
            node_positions,
            nodelist=nodes_of_role,
            node_size=1500,
            node_color='white',
            edgecolors=outline_color,
            linewidths=2
        )

    # Draw edges: solid thicker for direct links, thinner dashed for neighbor links
    for style in ('solid', 'dashed'):
        edges_with_style = [
            (node_u, node_v)
            for node_u, node_v, attributes in point_graph.edges(data=True)
            if attributes.get('connection_style') == style
        ]
        nx.draw_networkx_edges(
            point_graph,
            node_positions,
            edgelist=edges_with_style,
            style=style,
            edge_color='black',
            width=2 if style == 'solid' else 1
        )

    # Add labels to each node
    nx.draw_networkx_labels(
        point_graph,
        node_positions,
        labels=node_labels,
        font_size=10
    )

    # Remove axes for clarity and add a descriptive title
    plt.axis('off')
    plt.title(f"Point {central_index}: {point.scalar:.3f} [{point.type}]")
    plt.show()

########################################################

def visualize_point_link_circle(point):
    # oh, the things that we do for debugging
    # visualize_point_link_circle: flow description
    # 1. Initialize a NetworkX graph and add central point as a node.
    # 2. Add peripheral points and solid edges connecting them to the central point.
    # 3. Add dashed edges between neighboring peripheral points.
    # 4. Compute connected components of the link graph and order them by descending maximum point (uses Point.__gt__/__lt__).
    # 5. For each component, trace an ordered sequence from its highest-scalar endpoint.
    # 6. Separate sequences into those above vs. below-or-equal to the central point’s scalar.
    # 7. Interleave above-central (red) and below-or-equal-central (blue) sequences.
    # 8. Compute positions around a circle for peripheral points based on interleaving.
    # 9. Draw central and peripheral nodes with colored outlines, edges, labels, and title.
    graph = nx.Graph()

    central_point_index = point.index
    graph.add_node(central_point_index, role='central')

    neighbor_link_graph = point.link_graph

    # 2. Add peripheral nodes and solid edges
    for peripheral_point in neighbor_link_graph.nodes:
        graph.add_node(peripheral_point.index, role='peripheral')
        graph.add_edge(
            central_point_index,
            peripheral_point.index,
            connection_style='solid'
        )

    # 3. Add dashed edges between neighboring points
    for first_neighbor_point, second_neighbor_point in neighbor_link_graph.edges:
        graph.add_edge(
            first_neighbor_point.index,
            second_neighbor_point.index,
            connection_style='dashed'
        )

    # 4. Compute connected components of the link graph and order them by descending maximum point
    connected_component_sets = list(nx.connected_components(neighbor_link_graph))
    sorted_component_sets = sorted(
        connected_component_sets,
        key=lambda component_set: max(component_set),
        reverse=True
    )

    # 5. Trace each component into an ordered sequence
    component_point_sequences = []
    for component_point_set in sorted_component_sets:
        neighbor_subgraph = neighbor_link_graph.subgraph(component_point_set)
        endpoint_point_candidates = [
            candidate_point for candidate_point, node_degree in neighbor_subgraph.degree()
            if node_degree == 1
        ]
        if endpoint_point_candidates:
            starting_endpoint_point = max(endpoint_point_candidates)
        else:
            starting_endpoint_point = max(component_point_set)

        ordered_sequence = [starting_endpoint_point]
        previous_sequence_point = None
        current_sequence_point = starting_endpoint_point
        for _ in range(len(component_point_set) - 1):
            neighbor_sequence_list = [
                neighbor_point for neighbor_point in neighbor_subgraph.neighbors(current_sequence_point)
                if neighbor_point is not previous_sequence_point
            ]
            if not neighbor_sequence_list:
                break
            next_sequence_point = neighbor_sequence_list[0]
            ordered_sequence.append(next_sequence_point)
            previous_sequence_point = current_sequence_point
            current_sequence_point = next_sequence_point

        component_point_sequences.append(ordered_sequence)

    # 6. Split sequences above vs. below-or-equal central scalar
    upper_sequence = []
    lower_sequence = []
    for point_sequence in component_point_sequences:
        if max(point_sequence) > point:
            upper_sequence.append(point_sequence)
        else:
            lower_sequence.append(point_sequence)

    # 7. Interleave upper and lower sequences
    interleaved_sequence_blocks = []
    upper_sequence_index = 0
    lower_sequence_index = 0
    total_upper_sequences = len(upper_sequence)
    total_lower_sequences = len(lower_sequence)
    while upper_sequence_index < total_upper_sequences or lower_sequence_index < total_lower_sequences:
        if upper_sequence_index < total_upper_sequences:
            interleaved_sequence_blocks.append(upper_sequence[upper_sequence_index])
            upper_sequence_index += 1
        if lower_sequence_index < total_lower_sequences:
            interleaved_sequence_blocks.append(lower_sequence[lower_sequence_index])
            lower_sequence_index += 1

    # 8. Flatten and compute circle layout
    ordered_peripheral_points = [
        point_instance for sequence_block in interleaved_sequence_blocks
        for point_instance in sequence_block
    ]
    total_peripheral_points = len(ordered_peripheral_points)

    if total_peripheral_points > 0:
        angle_increment = 2 * math.pi / total_peripheral_points
    else:
        angle_increment = 0.0

    circle_radius = 1.0

    node_positions = {}
    node_labels = {}
    for sequence_position, peripheral_point in enumerate(ordered_peripheral_points):
        angle = sequence_position * angle_increment
        x_position = circle_radius * math.cos(angle)
        y_position = circle_radius * math.sin(angle)
        node_positions[peripheral_point.index] = (x_position, y_position)
        node_labels[peripheral_point.index] = f"{peripheral_point.index}\n{peripheral_point.scalar:.3f}"

    node_positions[central_point_index] = (0.0, 0.0)
    node_labels[central_point_index] = f"{central_point_index}\n{point.scalar:.3f}"

    # 9. Draw nodes, edges, labels, and show plot
    nx.draw_networkx_nodes(
        graph,
        node_positions,
        nodelist=[central_point_index],
        node_size=1500,
        node_color='white',
        edgecolors='purple',
        linewidths=2
    )
    for sequence_block in upper_sequence:
        peripheral_indexes = [peripheral_point.index for peripheral_point in sequence_block]
        nx.draw_networkx_nodes(
            graph,
            node_positions,
            nodelist=peripheral_indexes,
            node_size=1500,
            node_color='white',
            edgecolors='red',
            linewidths=2
        )
    for sequence_block in lower_sequence:
        peripheral_indexes = [peripheral_point.index for peripheral_point in sequence_block]
        nx.draw_networkx_nodes(
            graph,
            node_positions,
            nodelist=peripheral_indexes,
            node_size=1500,
            node_color='white',
            edgecolors='blue',
            linewidths=2
        )
    for edge_style in ['solid', 'dashed']:
        edge_list = [
            (node_u, node_v) for node_u, node_v, edge_attributes in graph.edges(data=True)
            if edge_attributes.get('connection_style') == edge_style
        ]
        nx.draw_networkx_edges(
            graph,
            node_positions,
            edgelist=edge_list,
            style=edge_style,
            edge_color='black',
            width=(2 if edge_style == 'solid' else 1)
        )
    nx.draw_networkx_labels(
        graph,
        node_positions,
        labels=node_labels,
        font_size=10
    )
    plt.axis('off')
    plt.title(f"Point {central_point_index}: {point.scalar:.3f} [{point.type}]")
    plt.show()
