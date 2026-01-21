import time
import datetime as dt

from orca_python import (
    Processor,
    WindowType,
    ValueResult,
    StructResult,
    MetadataField,
    ExecutionParams,
    lookback,
)

proc = Processor("ml")

# E.g. you have you have a fleet of busses, where every bus has a particular
# ID and runs a particular route
route_id = MetadataField(name="route_id", description="The unique ID of the route")
bus_id = MetadataField(name="bus_id", description="The unique ID of the bus")

Every30Second = WindowType(
    name="Every30Second",
    version="1.0.0",
    description="Triggers every 30 seconds",
    metadataFields=[route_id, bus_id],
)


@proc.algorithm("MyAlgo", "1.0.0", Every30Second, description="Does nothing")
def my_algorithm(params: ExecutionParams) -> StructResult:
    """A simple algorithms that does nothing interesting"""
    route_id = params.window.metadata.get("route_id", None)
    bus_id = params.window.metadata.get("bus_id", None)
    print(route_id, bus_id)

    time.sleep(5)
    return StructResult({"result": 42})


@proc.algorithm(
    "NewSuperDuperAlgo",
    "2.0.0",
    Every30Second,
    description="Depends on other",
    depends_on=[lookback(my_algorithm, td=dt.timedelta(days=10))],
)
def second_algorithm(params: ExecutionParams) -> ValueResult:
    if params.dependencies is None:
        raise Exception("could not get dependencies")
    dependencyResults = params.dependencies.get_result(my_algorithm)

    if dependencyResults is None:
        return ValueResult(10)

    value = 0
    for res in dependencyResults.results:
        if not isinstance(res.result, dict):
            raise Exception("Bad result received")
        _res = res.result.get("result", None)
        if _res is None:
            continue
        value += _res

    return ValueResult(value)


if __name__ == "__main__":
    proc.Register()
    proc.Start()
