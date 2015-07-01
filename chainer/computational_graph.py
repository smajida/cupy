import heapq

import numpy as np

from chainer import function
from chainer.functions import basic_math
from chainer import variable


class DotNode(object):
    def _shape(self):
        if isinstance(self.node, variable.Variable):
            return "oval"
        elif isinstance(self.node, function.Split):
            return "hexagon"
        else:
            return "box"

    def __init__(self, node):
        self.node = node
        self.id_ = id(node)
        self.attribute = {
            "label": str(self.node),
            "shape": self._shape()
        }

    def __str__(self):
        attributes = ["%s=\"%s\"" % (k, v) for (k, v)
                      in self.attribute.items()]
        return "%s [%s];" % (self.id_, ",".join(attributes))


class ComputationalGraph(object):
    def __init__(self, edges):
        self.edges = edges

    def _to_dot(self):
        ret = "digraph graphname{"
        for edge in self.edges:
            head, tail = edge
            assert (isinstance(head, variable.Variable)
                    and isinstance(tail, function.Function)) or \
                   (isinstance(head, function.Function)
                    and isinstance(tail, variable.Variable))
            head_node = DotNode(head)
            tail_node = DotNode(tail)
            ret += str(head_node)
            ret += str(tail_node)
            ret += "%s -> %s;" % (head_node.id_, tail_node.id_)
        ret += "}"
        return ret

    def __str__(self):
        return self._to_dot()

    def __len__(self):
        return len(self.edges)

    def __contains__(self, e):
        return e in self.edges


def computational_graph(outputs, remove_split=False):
    cands = []
    seen_edges = set()

    def heap_with_push_counter():
        table = []

        def add(cand):
            heapq.heappush(cands, (-cand.rank, len(table), cand))
            table.append(cand)
        return add

    heap = heap_with_push_counter()

    for o in outputs:
        heap(o)

    while cands:
        _, _, cand = heapq.heappop(cands)
        if isinstance(cand, variable.Variable):
            creator = cand.creator
            if remove_split and isinstance(creator, function.Split):
                # assume that function.Split has only one input
                next_cand = creator.inputs[0]
                heap(next_cand)
                continue
            if creator is not None and (creator, cand) not in seen_edges:
                heap(creator)
                seen_edges.add((creator, cand))
        elif isinstance(cand, function.Function):
            if remove_split and isinstance(cand, function.Split):
                next_cand = creator.inputs[0]
                heap(next_cand)
                continue
            for input_ in cand.inputs:
                if input_ != cand and (input_, cand) not in seen_edges:
                    creator = input_.creator
                    if remove_split and\
                       creator is not None and\
                       isinstance(creator, function.Split):
                        input_ = creator.inputs[0]
                    heap(input_)
                    seen_edges.add((input_, cand))
    return ComputationalGraph(seen_edges)
