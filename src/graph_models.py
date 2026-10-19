from dataclasses import dataclass, field


@dataclass
class DataPoint:
    pixel_x: float
    pixel_y: float
    value_x: float
    value_y: float


@dataclass
class GraphSeries:
    graph_id: str
    name: str
    color: str
    visible: bool = True
    points: list[DataPoint] = field(default_factory=list)


class GraphCollection:
    def __init__(self):
        self._graphs = {}
        self._next_number = 1

    def add(self, name, color):
        graph_id = f"graph-{self._next_number}"
        self._next_number += 1
        graph = GraphSeries(graph_id, name, color)
        self._graphs[graph_id] = graph
        return graph

    def remove(self, graph_id):
        self._graphs.pop(graph_id, None)

    def get(self, graph_id):
        return self._graphs[graph_id]

    def values(self):
        return self._graphs.values()

    def __iter__(self):
        return iter(self._graphs)

    def __len__(self):
        return len(self._graphs)
