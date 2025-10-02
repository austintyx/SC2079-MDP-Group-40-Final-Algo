from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from arena.map import Map
from arena.obstacle import Obstacle

from common.consts import SNAP_COORD
from common.types import Position
from common.utils import _mappings as Int_to_Direction_mappings

from math import pi

from path_finding.hamiltonian_path import HamiltonianSearch, AlgoType

from robot.stm_commands import convert_segments_to_commands

import multiprocessing as mp
import time

""" -------------------------------------- """
""" ---------- Endpoint Schemas ---------- """
""" -------------------------------------- """

# Input


class AlgoInputMode(Enum):
    SIMULATOR = "simulator"
    LIVE = "live"


class AlgoInputValueObstacle(BaseModel):
    id: int  # obstacle_id
    x: int   # grid_format
    y: int   # grid_format
    d: int   # direction of obstacle; follow the Direction ENUM in common.enums.py

class AlgoInputValue(BaseModel):
  obstacles: list[AlgoInputValueObstacle]
  mode: Optional[int] = 0 # (0: Task 1); (1: Task 2)

class AlgoInput(BaseModel):
    cat: str = "obstacles"
    value: AlgoInputValue
    server_mode: Optional[AlgoInputMode] = AlgoInputMode.LIVE
    algo_type: Optional[AlgoType] = AlgoType.EXHAUSTIVE_ASTAR

# Output


class AlgoOutputSimulatorPosition(BaseModel):
    x: int  # in cm
    y: int  # in cm
    theta: float  # in radian


class AlgoOutputSimulator(BaseModel):
    positions: list[AlgoOutputSimulatorPosition]
    runtime: str


class AlgoOutputLivePosition(BaseModel):
    x: int  # in cm
    y: int  # in cm
    d: str  # Robot Face -> 1: North; 2: South; 3: East; 4: West


class AlgoOutputLiveCommand(BaseModel):
    #cat: str = "control"
    value: str
    end_position: AlgoOutputLivePosition


class AlgoOutputLive(BaseModel):
    commands: list[AlgoOutputLiveCommand]


class AlgoPositionhNew(BaseModel):
    x: int  # in cm
    y: int  # in cm
    d: int


class AlgoOutputLiveResponseNew(BaseModel):
    commands: list[str]  # changed this to sring array
    path: list[AlgoPositionhNew]  # return path


class ImageDetectionResponse(BaseModel):
    detection_status: str = "Objects detected"
    objects: list[str]


""" -------------------------------------- """
""" ----------- Main Functions ----------- """
""" -------------------------------------- """
if __name__ == '__main__':
    mp.freeze_support()  # Needed to run child processes (multiprocessing)


def main(algo_input: AlgoInput, include_both: bool = False):
    # Algorithm Server Mode -> 'simulator' or 'live'
    algo_server_mode = algo_input["server_mode"]

    # Algorithm Task Mode -> 0: Task 1; 1: Task 2
    # algo_task_mode = algo_input["value"]["mode"]

    # Obstacles
    obstacles = _extract_obstacles_from_input(
        algo_input["value"]["obstacles"], algo_server_mode)

    # Start Position
    start_position = Position(x=0, y=0, theta=pi/2)

    # Map
    map = Map(obstacles=obstacles)

    # Algorithm
    algo_type = algo_input["algo_type"]
    print("Algorithm: ", algo_type)
    algo = HamiltonianSearch(map=map, src=start_position, algo_type=algo_type)

    # Algorithm Search⭐
    min_perm, paths = algo.search()

    # Generate Simulator Output
    if algo_server_mode == AlgoInputMode.SIMULATOR:
        simulator_algo_output = [] # Array of positions
        for path in paths:
            for node in path:
                # Convert Position to dict
                simulator_algo_output.append({
                    "x": node.pos.x,
                    "y": node.pos.y,
                    "theta": node.pos.theta
                })
                #print("Node:", node)
            # Position configuration to represent scanning (*only for simulator)
            simulator_algo_output.append({"x": -1, "y": -1, "theta": -2})
            simulator_algo_output.append({"x": -1, "y": -1, "theta": -1})
            # TEST
        current_perm = 1
        stm_commands = []
        commands = convert_segments_to_commands(path)
        stm_commands.extend(commands)
        stm_commands.append([f"SNAP{min_perm[current_perm]}", commands[-1][1]])
        algoOutputLiveCommands: list[AlgoOutputLiveCommand] = [] # Array of commands
        for command in stm_commands:
            algoOutputLiveCommands.append(AlgoOutputLiveCommand(
                cat="control",
                value=command[0],
                #value='test',
                #end_position='test'
                end_position=command[1]
            ))
        print(algoOutputLiveCommands)
        algoOutputLiveCommands.append(AlgoOutputLiveCommand(
        cat="control",
        value="FIN",
        end_position=algoOutputLiveCommands[-1].end_position
        ))
        return simulator_algo_output
    
    
    if algo_server_mode == AlgoInputMode.LIVE:
        #print("TEST")
        current_perm = 1
        stm_commands = []

        for path in paths:
            commands = convert_segments_to_commands(path)
            stm_commands.extend(commands)

            # Add SNAP1 command after each path (from one obstacle to another) (For Raspberry Pi Team to know when to scan the image)
            stm_commands.append([f"SNAP{min_perm[current_perm]}", commands[-1][1]])
            current_perm += 1 # Increment by current_perm to access the next obstacle_id
        
        
        algoOutputLiveCommands: list[AlgoOutputLiveCommand] = [] # Array of commands
        for command in stm_commands:
            algoOutputLiveCommands.append(AlgoOutputLiveCommand(
                # cat="control",
                value=command[0],
                end_position=command[1]
            ))
        
        # Add FIN as the last command (For Raspberry Pi Team to know that the algorithm has ended)
        algoOutputLiveCommands.append(AlgoOutputLiveCommand(
        # cat="control",
        value="FIN",
        end_position=algoOutputLiveCommands[-1].end_position
        ))
        
        
        print("Commands:", algoOutputLiveCommands)

        return algoOutputLiveCommands


def _extract_obstacles_from_input(input_obstacles, algo_server_mode):
    """
    Helper function to convert input obstacles to `Obstacle` object accepted by the algorithm
    """
    obstacles = []

    grid_pos_to_c_pos_multiplier = SNAP_COORD
    if algo_server_mode == AlgoInputMode.LIVE:
        # Live mode uses 10cm grid format (so need to *2 to align with algo's 5cm grid format)
        grid_pos_to_c_pos_multiplier *= 2

    for obstacle in input_obstacles:
        obstacles.append(Obstacle(
            x=obstacle["x"] * grid_pos_to_c_pos_multiplier,
            y=obstacle["y"] * grid_pos_to_c_pos_multiplier,
            facing=Int_to_Direction_mappings[str(obstacle["d"])]
        ))

    return obstacles


""" -------------------------------------- """
""" ------ FastAPI (API Endpoints) ------- """
""" -------------------------------------- """

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/algo/simulator/simple-test", tags=["Algorithm"])
async def algo_simulator_test():
    """To test algo and endpoint on the server without starting up the web simulator"""
    # Basic Mock Data
    simulator_algo_input: AlgoInput = {
        "cat": "obstacles",
        "obstacles": [
            {"id": 1, "x": 30, "y": 20, "d": 4},  # 5cm grid (x, y)
            {"id": 2, "x": 2, "y": 36, "d": 2},  # 5cm grid (x, y)
        ],
        "server_mode": AlgoInputMode.SIMULATOR,
        "algo_type": AlgoType.EXHAUSTIVE_ASTAR,
    }

    positions = main(simulator_algo_input)

    return {"positions": positions}


@app.post("/algo/simulator", response_model=AlgoOutputSimulator, tags=["Algorithm"])
async def algo_simulator(algo_input: AlgoInput):
    """Main endpoint for simulator"""
    start_time = time.time()
    if hasattr(algo_input, "model_dump"):
     algo_input = algo_input.model_dump()
    else:
     algo_input = algo_input.dict()

    positions = main(algo_input)

    runtime = time.time() - start_time  # in seconds

    # Convert position objects to dicts for FastAPI serialization
    

    runtime = time.time() - start_time
    return {"positions": positions, "runtime": "{:.4f} seconds".format(runtime)}


@app.get("/algo/live/simple-test", response_model=AlgoOutputLive, tags=["Algorithm"])
async def algo_live_test():
    """To test algo and endpoint on the server in live mode"""
    # Basic Mock Data
    live_algo_input: AlgoInput = {
        "cat": "obstacles",
        "obstacles": [
            {"id": 1, "x": 15, "y": 10, "d": 4},  # 10cm grid (x, y)
            {"id": 2, "x": 1, "y": 18, "d": 2},  # 10cm grid (x, y)
        ],
        "server_mode": AlgoInputMode.LIVE,
        "algo_type": AlgoType.EXHAUSTIVE_ASTAR,
    }
    commands = main(live_algo_input)

    return {"commands": commands}


@app.post("/optimal", response_model=AlgoOutputLiveResponseNew, tags=["Algorithm"])
async def algo_live(algo_input: AlgoInput):
    """Main endpoint for live mode"""
    # Get both outputs from main using the include_both flag
    result = main(algo_input.dict(), include_both=True)
    commands = result["live"]
    positions = result["simulator"]

    # Convert theta to d in positions and ensure integers.
    # New scheme: 0 -> East, 1 -> North, 2 -> West, 3 -> South.
    for pos in positions:
        # Normalize theta to the [0, 2pi) range.
        theta = pos.theta % (2 * pi)
        if theta < 0:
            theta += 2 * pi

        # Mapping based on radian values:
        if abs(theta) < 0.01 or abs(theta - 2 * pi) < 0.01:
            pos.d = 0
        elif abs(theta - pi / 2) < 0.01:
            pos.d = 1
        elif abs(theta - pi) < 0.01:
            pos.d = 2
        elif abs(theta - 3 * pi / 2) < 0.01:
            pos.d = 3
        else:
            pos.d = 0  # Default case if no conditions match

        # Remove the theta attribute as it is no longer needed
        delattr(pos, 'theta')

    # Extract only the command strings, excluding the final FIN command.
    command_values = [cmd.value for cmd in commands]
    print(f"Commands: {command_values}")
    return {"commands": command_values, "path": positions}

@app.post("/algo/live", response_model=AlgoOutputLive, tags=["Algorithm"])
async def algo_live(algo_input: AlgoInput):
  """Main endpoint for live mode"""
  if hasattr(algo_input, "model_dump"):
     algo_input = algo_input.model_dump()
  else:
     algo_input = algo_input.dict()
  commands = main(algo_input)

  return { "commands": commands }
