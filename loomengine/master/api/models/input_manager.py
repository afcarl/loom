import copy
import re


class InputManager(object):
    """Manages the set of nodes acting as inputs for one step.
    Each input node may have more than one DataObject,
    and DataObjects may arrive to the node at different times.
    """
    def __init__(self, input_nodes, target_channel, triggered_data_path):
        target_node_list = filter(lambda n: n.channel==target_channel, input_nodes)
        assert len(target_node_list) == 1, \
            'expected exactly 1 node with channel %s but found %s' \
            % (channel, len(target_node_list))
        target_node = target_node_list[0]
        target_group = target_node.group
        # New data has arrived at triggered_data_path, but if the input
        # has mode "gather", we have to search for data from a level higher
        # on the tree. target_data_path represents that adjusted data path.
        target_data_path = self._gather(
            triggered_data_path,
            self._get_gather_depth(target_node))

        groups = set()
        for input_node in input_nodes:
            groups.add(input_node.group)

        combined_generator = None
        for group in groups:
            # These will be processed in order of group id, ensuring
            # correct order for cross products.
            group_input_nodes = filter(lambda n: n.group==group, input_nodes)

            # The target group is restricted to "data_path",
            # which is where new data has arrived. We will take a cross-
            # product of data between groups, so we want to check the new
            # data against all data in other groups. To capture all data
            # on non-target gropus, we use the root data path (a.k.a. [])
            if group == target_group:
                group_data_path = target_data_path
            else:
                group_data_path = []

            group_generator = None
            for node in group_input_nodes:
                generator = InputSetGeneratorNode.create_from_input_output_node(
                    node,
                    target_path=group_data_path,
                    gather_depth=self._get_gather_depth(node))
                if group_generator is None:
                    group_generator = generator
                else:
                    group_generator = group_generator.dot_product(generator)

            if combined_generator is None:
                combined_generator = group_generator
            else:
                combined_generator = combined_generator.cross_product(group_generator)

        self.generator = combined_generator

    def get_input_sets(self):
        seed_path = []
        return self.generator.get_input_sets(seed_path)

    @classmethod
    def _get_gather_depth(cls, node):
        mode = node.mode
        if mode == 'no_gather':
            return 0
        elif mode == 'gather':
            return 1
        else:
            match = re.match('gather\(([0-9]+)\)', mode)
            if match is None:
                raise Exception('Failed to parse input mode %s' % mode)
            return int(match.groups()[0])

    @classmethod
    def _gather(cls, data_path, gather_depth):
        """New data has arrived at "input_data_path", 
        but this may trigger action at a higher data_path if
        the input is in a "gather" mode.

        For example, if an input has mode "gather" and just received 
        the first member of a 5-element 1-dimensional array, the input_data_path
        is ([0, 5],). That data will not be processed alone, but rather once all 5
        elements arrive they will be processed as a single ArrayDataObject 
        input for downstream tasks. The data_path of that array is up one level,
        in general, which is at the root node (data_path=[]) in this example.
        """
        if len(data_path) < gather_depth:
            return []
        return data_path[0:len(data_path)-gather_depth]


class InputSetGeneratorNode(object):
    """A class for creating InputSets from various possible input configurations.

    Must handle the following variations in inputs:
    - Varied dimensionality of data on each input: scalar, array, or nested aray data
      e.g. 1, [1,2], or [[1,2],[3,4,5]], and so on.
    - One or more input in an input group (i.e. dot product), 
      e.g., combining two channels in the same group, 
      [1;2] * [3;4] -> [1,2;3,4]
    - One or more input groups (i.e. cross product), 
      e.g., combining two channels in different groups, 
      [1;2] x [3;4] -> [1,3;1,4;2,3;2,4]
    - "Gather" behavior or one or more inputs, 
       e.g. [1,2] -> Array(1,2), where the Array serves as an input to a single task
       or [[1,2],[3,4,5]] -> [Array(1,2),Array(3,4,5)], where each Array serves as an
       input to a task
    - "Gather(n)" behavior on one or more inputs,
      e.g. for gather(2), [[1,2],[3,4,5]] -> [Array(1,2,3,4,5)]

    An InputSetGeneratorNode may be triggered when one new DataObject arrives, 
    so it is not necessary to scan the whole data tree on the target input. 
    Instead, a target_data_path specifies which subtree to check for new 
    InputSets. (This target_data_path must be adjusted prior to calling 
    InputSetGeneratorNode if the input has "gather" mode.)
    """

    def __init__(self, index=None):
        self.index = index # Remains None for root node only
        self.degree = None # Remains None for leaf nodes only
        self.children = {} # key is index, value is InputSetGeneratorNode
        self.input_items = [] # list of InputItems, only on leaf nodes

    @classmethod
    def create_from_input_output_node(cls, io_node, target_path=None, gather_depth=0):
        """Scan the data tree on the given io_node to create a corresponding
        InputSetGenerator tree.
        """

        # If target_path is given, any data above that path will be ignored.
        # The path [] represents the root node, so this default value scans
        # the whole tree
        if not target_path:
            target_path = []

        generator = InputSetGeneratorNode()
        for (data_path, data_node) in io_node.get_ready_data_nodes(
                target_path, gather_depth):
            input_item = InputItem(data_node, io_node.channel, mode=io_node.mode)
            generator._add_input_item(data_path, input_item)
        return generator

    def _add_input_item(self, data_path, input_item):
        return self._add_input_items(data_path, [input_item,])

    def _add_input_items(self, data_path, input_items):
        if len(data_path) == 0:
            self.input_items.extend(input_items)
            return

        (index, degree) = data_path.pop(0)

        if self.degree is None:
            self.degree = degree
        assert degree == self.degree, 'Degree mismatch'
        if not self.children.get(index):
            self.children[index] = InputSetGeneratorNode(index=index)
        self.children[index]._add_input_items(data_path, input_items)

    def dot_product(self, generator_B):
        generator_A_dot_B = InputSetGeneratorNode()
        for input_set_A in self.get_input_sets([]):
            seed_node_B = generator_B.get_node(input_set_A.data_path)
            if seed_node_B is None:
                continue
            for input_set_B in seed_node_B.get_input_sets(input_set_A.data_path):
                data_path = self._select_longer_path(
                    input_set_A.data_path, input_set_B.data_path)
                input_items = input_set_A.input_items + input_set_B.input_items
                generator_A_dot_B._add_input_items(data_path, input_items)
        return generator_A_dot_B

    def _select_longer_path(self, path1, path2):
        if len(path1) > len(path2):
            longer_path = path1
            shorter_path = path2
        else:
            longer_path = path2
            shorter_path=path1
        assert shorter_path == longer_path[0:len(shorter_path)], 'path mismatch'
        return longer_path

    def cross_product(self, generator_B):
        generator_A_cross_B = InputSetGeneratorNode()
        for input_set_A in self.get_input_sets([]):
            for input_set_B in generator_B.get_input_sets([]):
                data_path = input_set_A.data_path + input_set_B.data_path
                input_items = input_set_A.input_items + input_set_B.input_items
                generator_A_cross_B._add_input_items(data_path, input_items)
        return generator_A_cross_B

    def get_input_sets(self, seed_path):
        if self._is_leaf:
            path = copy.deepcopy(seed_path)
            if not self.input_items:
                return []
            else:
                return [InputSet(path, self.input_items)]
        else:
            input_sets = []
            for child in self.children.values():
                path = copy.deepcopy(seed_path)
                path.append([child.index, self.degree])
                input_sets.extend(child.get_input_sets(path))
            return input_sets

    @property
    def _is_leaf(self):
        return self.degree == None

    def get_node(self, path):
        if self._is_leaf:
            return self
        if len(path) == 0:
            return self
        path = copy.copy(path)
        index, degree = path.pop(0)
        assert degree == self.degree, 'degree mismatch in get_node'
        child = self.children.get(index)
        if not child:
            return None
        else:
            return child.get_node(path)

class InputSet(object):
    """All the information needed to create a Task from a given StepRun.
    """
    

    def __iter__(self):
        return self.input_items.__iter__()

    def __init__(self, data_path, input_items):
        self.data_path = data_path
        self.input_items = input_items


class InputItem(object):
    """All the information needed by the Task to construct one TaskInput.
    For array inputs, we avoid creating the ArrayDataObject now and instead
    provide the data_tree_node from which the array can be generated. That way,
    if we find that the downstream Task has already been created, we can
    refrain from creating a new ArrayDataObject for no reason.
    """

    def __init__(self, data_tree, channel, mode):
        self.channel = channel
        self.data_tree = data_tree
        self.mode = mode

    @property
    def type(self):
        return self.data_tree.type
