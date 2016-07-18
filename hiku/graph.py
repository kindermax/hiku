from abc import ABCMeta, abstractmethod
from itertools import chain
from collections import OrderedDict

from .utils import kw_only, cached_property, const
from .compat import with_metaclass


Maybe = const('Maybe')
One = const('One')
Many = const('Many')

Nothing = const('Nothing')


class AbstractNode(with_metaclass(ABCMeta)):

    @abstractmethod
    def accept(self, visitor):
        pass


class AbstractOption(AbstractNode):
    pass


class Option(AbstractOption):

    def __init__(self, name, *other, **kwargs):
        if not len(other):
            type_ = None
        elif len(other) == 1:
            type_, = other
        else:
            raise TypeError('More positional arguments ({}) than expected (2)'
                            .format(len(other) + 1))

        self.name = name
        self.type = type_
        self.default, = kw_only(kwargs, [], ['default'])

    def accept(self, visitor):
        return visitor.visit_option(self)


class AbstractField(AbstractNode):
    pass


class Field(AbstractField):

    def __init__(self, name, *other, **kwargs):
        if not len(other):
            raise TypeError('Missing required argument')
        elif len(other) == 1:
            type_, func = None, other[0]
        elif len(other) == 2:
            type_, func = other
        else:
            raise TypeError('More positional arguments ({}) than expected (3)'
                            .format(len(other) + 1))

        options, description = kw_only(kwargs, [], ['options', 'description'])

        self.name = name
        self.type = type_
        self.func = func
        self.options = options or ()
        self.description = description

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_field(self)


class AbstractLink(AbstractNode):
    pass


class Link(AbstractLink):

    def __init__(self, name, type_, func, **kwargs):
        edge, requires, options, description = \
            kw_only(kwargs, ['edge', 'requires'], ['options', 'description'])

        self.name = name
        self.type = type_
        self.func = func
        self.edge = edge
        self.requires = requires
        self.options = options or ()
        self.description = description

    @cached_property
    def options_map(self):
        return OrderedDict((op.name, op) for op in self.options)

    def accept(self, visitor):
        return visitor.visit_link(self)


class AbstractEdge(AbstractNode):
    pass


class Edge(AbstractEdge):

    def __init__(self, name, fields, **kwargs):
        self.name = name
        self.fields = fields
        self.description, = kw_only(kwargs, [], ['description'])

    @cached_property
    def fields_map(self):
        return OrderedDict((f.name, f) for f in self.fields)

    def accept(self, visitor):
        return visitor.visit_edge(self)


class Root(Edge):

    def __init__(self, items):
        super(Root, self).__init__(None, items)


class AbstractGraph(AbstractNode):
    pass


class Graph(AbstractGraph):

    def __init__(self, items):
        self.items = items

    @cached_property
    def root(self):
        return Root(list(chain.from_iterable(e.fields for e in self.items
                                             if e.name is None)))

    @cached_property
    def edges(self):
        return [e for e in self.items if e.name is not None]

    @cached_property
    def edges_map(self):
        return OrderedDict((e.name, e) for e in self.edges)

    def accept(self, visitor):
        return visitor.visit_graph(self)


class GraphVisitor(object):

    def visit(self, obj):
        return obj.accept(self)

    def visit_option(self, obj):
        pass

    def visit_field(self, obj):
        for option in obj.options:
            self.visit(option)

    def visit_link(self, obj):
        for option in obj.options:
            self.visit(option)

    def visit_edge(self, obj):
        for item in obj.fields:
            self.visit(item)

    def visit_graph(self, obj):
        for item in obj.items:
            self.visit(item)
