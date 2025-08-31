from pydantic.dataclasses import dataclass, Field
from plotly import graph_objects
from enum import Enum

NODE_ALIGN = "left"
NODE_PADDING = 10  # pixels
NODE_THICKNESS = 20  # pixels
LINK_ARROWLEN = 0  # pixels
COLOR_STRINGS = {
  "Magenta": "rgba(255, 0, 255, 0.4)",
  "Cyan": "rgba(0, 255, 255, 0.4)",
  "LimeGreen": "rgba(0, 255, 0, 0.4)",
  "Orange": "rgba(255, 165, 0, 0.4)",
  "RoyalBlue": "rgba(65, 105, 225, 0.4)",
  "Crimson": "rgba(220, 20, 60, 0.4)",
  "Gold": "rgba(255, 215, 0, 0.4)",
  "Violet": "rgba(148, 0, 211, 0.4)",
  "Teal": "rgba(0, 128, 128, 0.4)",
  "SlateGray": "rgba(112, 128, 144, 0.4)",
  "DeepPink": "rgba(255, 20, 147, 0.4)",
  "Turquoise": "rgba(64, 224, 208, 0.4)",
  "Chartreuse": "rgba(127, 255, 0, 0.4)",
  "Tomato": "rgba(255, 99, 71, 0.4)",
  "SteelBlue": "rgba(70, 130, 180, 0.4)",
  "Indigo": "rgba(75, 0, 130, 0.4)",
  "HotPink": "rgba(255, 105, 180, 0.4)",
  "DodgerBlue": "rgba(30, 144, 255, 0.4)",
  "FireBrick": "rgba(178, 34, 34, 0.4)",
  "MediumSeaGreen": "rgba(60, 179, 113, 0.4)",
  "DarkOrange": "rgba(255, 140, 0, 0.4)",
  "Orchid": "rgba(218, 112, 214, 0.4)",
  "SpringGreen": "rgba(0, 255, 127, 0.4)",
  "DeepSkyBlue": "rgba(0, 191, 255, 0.4)",
  "YellowGreen": "rgba(154, 205, 50, 0.4)",
  "Maroon": "rgba(128, 0, 0, 0.4)",
  "DarkCyan": "rgba(0, 139, 139, 0.4)",
  "Sienna": "rgba(160, 82, 45, 0.4)",
  "LightCoral": "rgba(240, 128, 128, 0.4)",
  "MediumPurple": "rgba(147, 112, 219, 0.4)",
  "PaleVioletRed": "rgba(219, 112, 147, 0.4)",
  "DarkSlateBlue": "rgba(72, 61, 139, 0.4)",
}


# TODO implement configurable cadence
class Cadence(Enum):
  MONTHLY = "monthly"


@dataclass
class Stock:
  name: str
  units: str
  value: float = Field(default=0.0)
  inf: bool = Field(default=False)
  color: str = Field(default="SlateGray")

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
  color: str = Field(default="SlateGray")
  label: str = Field(default_factory=str)

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
          flow.color = stock.color
      # TODO: generalize this to stock types
      if "PNC" in stock.name and stock.value + inflow < outflow:
        raise Exception(f"DANGER! Unbalanced flow: {stock.name}, {inflow=}, {outflow=}")


@dataclass
class SankeyNode:
  stocks: list[Stock]
  pad: int = Field(default=NODE_PADDING)
  align: str = Field(default=NODE_ALIGN)
  thickness: int = Field(default=NODE_THICKNESS)

  def payload(self) -> dict[str, int | list[str]]:
    return {
      "label": [stock.name for stock in self.stocks],
      "color": [COLOR_STRINGS[stock.color] for stock in self.stocks],
      "pad": self.pad,
      "align": self.align,
      "thickness": self.thickness,
    }


@dataclass
class SankeyLink:
  stocks: list[Stock]
  flows: list[Flow]
  arrowlen: int = Field(default=LINK_ARROWLEN)

  def payload(self) -> dict[str, int | list[str]]:
    index = {stock.name: i for i, stock in enumerate(self.stocks)}
    return {
      "arrowlen": self.arrowlen,
      "source": [index[flow.src.name] for flow in self.flows],
      "target": [index[flow.dst.name] for flow in self.flows],
      "value": [flow.val * flow.pct for flow in self.flows],
      "color": [COLOR_STRINGS[flow.color] for flow in self.flows],
      "label": [flow.label for flow in self.flows],
    }


@dataclass
class SankeyDiagram:
  node: SankeyNode
  link: SankeyLink
  arrangement: str = Field(default="snap")

  @classmethod
  def from_system(cls, system: System) -> "SankeyDiagram":
    node = SankeyNode(system.stocks)
    link = SankeyLink(stocks=system.stocks, flows=system.flows)
    return cls(node=node, link=link)

  def figure(self) -> graph_objects.Figure:
    return graph_objects.Figure(
      graph_objects.Sankey(
        node=self.node.payload(),
        link=self.link.payload(),
        arrangement=self.arrangement,
      )
    )
