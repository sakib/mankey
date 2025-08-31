import asyncio
import json

from pydantic import ValidationError
from models import SankeyDiagram, System, Stock, Flow


STOCKS_FILE = "src/data/stocks.json"
FLOWS_FILE = "src/data/flows.json"


def load_data(cls, filename: str) -> list[Stock]:
  with open(filename, "r") as f:
    items = json.load(f)
  return [cls(**item) for item in items]


async def main() -> None:
  # load data
  stocks = load_data(Stock, STOCKS_FILE)
  flows = load_data(Flow, FLOWS_FILE)

  # reconcile data for timestep t=0
  system = System(stocks=stocks, flows=flows)

  # build sankey diagram
  diagram = SankeyDiagram.from_system(system)
  fig = diagram.figure()
  print(fig)
  fig.show()

  # display visualization


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except ValidationError as e:
    print("Validation errors occurred:")
    for error in e.errors():
      print(f"- {error}")
    raise
