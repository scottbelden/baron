from .render import RenderWalker, render
from .utils import string_instance
from collections import namedtuple


def position_to_path(tree, line, column):
    return PositionFinder().find(tree, line, column)


def path_to_node(tree, path):
    if path is None:
        return None
    node = tree
    for key in path.path:
        if not isinstance(node[key], string_instance):
            node = node[key]
    return node


def position_to_node(tree, line, column):
    return path_to_node(tree, position_to_path(tree, line, column))


def node_to_bounding_box(node):
    return BoundingBox().compute(node)


def path_to_bounding_box(tree, path):
    return BoundingBox().compute(tree, path)


def make_path(path = None, node_type = None, position_in_rendering_list = None):
    return namedtuple('Position', ['path', 'node_type', 'position_in_rendering_list'])._make([
            [] if path is None else path,
            node_type,
            position_in_rendering_list
        ])


class PositionFinder(RenderWalker):
    """Find a node by line and column and return the path to it.

    First, walk through all the nodes while maintaining the current line
    and column. When the targetted node is found, stop there and build
    the path while going back up the tree.
    """
    def find(self, tree, line, column):
        self.current = Position(1,1)
        self.target = Position(line, column)
        self.path_found = False
        self.path = []
        self.node_type = None
        self.position_in_rendering_list = None

        self.walk(tree)
        return make_path(self.path, self.node_type, self.position_in_rendering_list) if self.path_found else None

    def after_list(self, node, pos, key):
        if self.path_found:
            self.path.insert(0, key)

    def after_key(self, node, pos, key):
        if self.path_found:
            self.path.insert(0, key)
            if self.node_type is None and 'type' in node:
                self.node_type = node['type']

    def after_formatting(self, node, pos, key):
        if self.path_found:
            self.path.insert(0, key)

    def after_node(self, node, pos, key):
        if self.path_found:
            self.path.insert(0, key)
            if self.position_in_rendering_list is None:
                self.position_in_rendering_list = pos
            if self.node_type is None:
                self.node_type = node['type']

    def on_leaf(self, constant, pos, key):
        """Determine if we're on the targetted node.

        If the targetted column is reached, `stop` and `path_found` are
        set. If the targetted line is passed, only `stop` is set. This
        prevents unnecessary tree travelling when the targetted column
        is out of bounds.
        """
        newlines_split = split_on_newlines(constant)

        for c in newlines_split:
            if c == "\n":
                self.current.advance_line()
                # if target lined is passed
                if self.current.line > self.target.line:
                    return self.STOP

            else:
                advance_by = len(c)
                if self.is_on_targetted_node(advance_by):
                    if key is not None:
                        self.path.insert(0, key)
                    self.position_in_rendering_list = pos
                    self.path_found = True
                    return self.STOP
                self.current.advance_columns(advance_by)

    def is_on_targetted_node(self, advance_by):
        return self.target.line == self.current.line \
            and self.target.column >= self.current.column \
            and self.target.column <  self.current.column + advance_by


class PathWalker(RenderWalker):
    def walk(self, tree):
        self.current_path = []
        self.current_node_type = None
        self.current_position_in_rendering_list = None

        RenderWalker.walk(self, tree)

    def current_decorated_path(self):
        return make_path(self.current_path, self.current_node_type, self.current_position_in_rendering_list)

    def _walk(self, node):
        for key_type, item, render_pos, render_key in render(node):
            if render_key != None:
                self.current_path.append(render_key)
            if key_type != 'constant':
                old_type = self.current_node_type
                self.current_node_type = item["type"] if "type" in item else key_type
            old_pos = self.current_position_in_rendering_list
            self.current_position_in_rendering_list = render_pos

            stop = self._walk_on_item(key_type, item, render_pos, render_key)

            if render_key != None:
                self.current_path.pop()
            if key_type != 'constant':
                self.current_node_type = old_type
            self.current_position_in_rendering_list = old_pos

            if stop:
                return self.STOP


class BoundingBox(PathWalker):
    """Compute the bounding box of the given node.

    First, walk to the target path while incrementing the position.
    When reached, the top-left position is set to the current position.
    Then walke the whole node, still incrementing the position. When
    arriving at the end of the node, store the previous position, not
    the current one, as the bottom-right position.
    If no target path is given, assume the targetted node is the whole
    tree.
    """
    def compute(self, tree, target_path = None):
        self.target_path = target_path
        self.current_position = Position(1, 1)
        self.left_of_current_position = Position(1, 0)
        self.left = None
        self.right = None
        self.found = True if self.target_path is None else False

        self.walk(tree)
        if self.found and self.left is None:
            self.left = (1, 1)
        if self.found and self.right is None:
            self.right = (self.left_of_current_position.line, self.left_of_current_position.column)

        return (self.left, self.right)

    def on_leaf(self, constant, pos, key):
        if self.current_decorated_path() == self.target_path:
            self.found = True
        if self.left is None and self.found:
            self.left = (self.current_position.line, self.current_position.column)

        newlines_split = split_on_newlines(constant)

        for c in newlines_split:
            if c == "\n":
                self.current_position.advance_line()
            elif c != "":
                self.current_position.advance_columns(len(c))
                self.left_of_current_position = self.current_position.left()

        if self.right is None and self.found and self.current_decorated_path() == self.target_path:
            self.right = (self.left_of_current_position.line, self.left_of_current_position.column)
            return self.STOP


def split_on_newlines(constant):
    return ["\n"] if constant == "\n" else intersperce(constant.split("\n"), "\n")


# Stolen shamelessly from http://stackoverflow.com/a/5656097/1013628
def intersperce(iterable, delimiter):
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x


class Position:
    def __init__(self, line, column):
        self.line = line
        self.column = column

    def advance_columns(self, columns):
        self.column += columns

    def advance_line(self):
        self.line += 1
        self.column = 1

    def left(self):
        return Position(self.line, self.column - 1)

