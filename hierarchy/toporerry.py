from ..debug.hierarchy import visualize_branches_horizontal_toporerry

class Toporerry:
    def traverse_descending(self):
        """
        Depth-first traversal of the branch hierarchy tree,
        always descending into the largest child first using stored branch values.
        Returns a flat list of (birth, death) pairs in visit order.
        """

        # find root tuples (in-degree == 0)
        root_nodes = [node for node in self.hierarchy_tree.nodes if self.hierarchy_tree.in_degree(node) == 0]
        [root_node] = root_nodes

        root_branch = root_node

        visit_order = []

        def traverse_branch(branch):
            visit_order.append(branch)

            children = self.hierarchy_tree.get_children(branch)
            child_branches = [node for node in children]

            for child in sorted(child_branches, reverse=True):
                traverse_branch(child)

        traverse_branch(root_branch)

        return visit_order

    def visualize_toporerry(self, base_dx=1.0, dy=0.1, circle_size=50, flip=None, reverse=None, connector_linestyle='dotted', grid_color='lightgray', grid_alpha=0.5):
        if flip is None and reverse is None:
            if self.type == 'join':
                reverse = True
            elif self.type == 'split':
                reverse = False

        visualize_branches_horizontal_toporerry(
            self, base_dx, dy, circle_size,
            flip, reverse, connector_linestyle, grid_color, grid_alpha
        )
