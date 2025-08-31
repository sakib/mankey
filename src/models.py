from pydantic.dataclasses import dataclass, Field
from plotly import graph_objects
from enum import Enum

NODE_PADDING = 10  # pixels


class Cadence(Enum):
  BIMONTHLY = "bimonthly"
  MONTHLY = "monthly"


@dataclass
class Stock:
  name: str
  units: str
  value: float = Field(default=0.0)
  inf: bool = Field(default=False)

  def __post_init__(self) -> None:
    if self.inf:
      self.value = float("inf")


@dataclass
class Flow:
  src_name: str
  dst_name: str
  val: float = Field(default=None)
  pct: float = Field(default=1.0)
  src: Stock | None = Field(default=None)
  dst: Stock | None = Field(default=None)
  cadence: Cadence = Field(default=Cadence.MONTHLY)

  def __post_init__(self):
    assert 0.0 <= self.pct <= 1.0


@dataclass
class System:
  stocks: list[Stock]
  flows: list[Flow]

  def __post_init__(self) -> None:
    for stock in self.stocks:
      inflow, outflow = 0.0, 0.0
      for flow in self.flows:
        flow.src = [s for s in self.stocks if s.name == flow.src_name][0]
        flow.dst = [s for s in self.stocks if s.name == flow.dst_name][0]
        if flow.dst.name == stock.name:
          inflow += flow.val * flow.pct
        if flow.src.name == stock.name:
          outflow += flow.val * flow.pct
      assert stock.value + inflow > outflow


@dataclass
class SankeyNode:
  label: list[Stock]
  pad: int = Field(default=NODE_PADDING)

  def payload(self) -> dict[str, int | list[str]]:
    return {
      "label": [stock.name for stock in self.label],
      "pad": self.pad,
    }


@dataclass
class SankeyLink:
  source: list[int]
  target: list[int]
  value: list[float]

  def payload(self) -> dict[str, int | list[str]]:
    return {
      "source": self.source,
      "target": self.target,
      "value": self.value,
    }


@dataclass
class SankeyDiagram:
  node: SankeyNode
  link: SankeyLink
  arrangement: str = Field(default="snap")

  @classmethod
  def from_system(cls, system: System) -> "SankeyDiagram":
    node = SankeyNode(label=[s for s in system.stocks])
    index = {stock.name: i for i, stock in enumerate(system.stocks)}
    link = SankeyLink(
      source=[index[flow.src.name] for flow in system.flows],
      target=[index[flow.dst.name] for flow in system.flows],
      value=[flow.val for flow in system.flows],
    )
    return cls(node=node, link=link)

  def figure(self) -> graph_objects.Figure:
    return graph_objects.Figure(
      graph_objects.Sankey(
        node=self.node.payload(),
        link=self.link.payload(),
        arrangement=self.arrangement,
      )
    )
