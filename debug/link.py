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
