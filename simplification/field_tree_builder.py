from ..field.field_analyzer import FieldAnalyzer
from ..manager.critical_manager import CriticalManager
from ..tree.reeb_tree import ReebTree

class FieldTreeBuilder:
    def __init__(self, field, field_name, tree_type):
        self.field = field
        self.field_name = field_name
        self.tree_type = tree_type

        self.field_data = FieldAnalyzer(self.field, self.field_name)
        self.points = self.field_data.points
        self.critical_points = self.field_data.critical_points
        self.critical_manager = CriticalManager(self.field_data)
        self.tree = ReebTree(self.critical_manager, self.tree_type)
        self.mesh = self.field_data.mesh
