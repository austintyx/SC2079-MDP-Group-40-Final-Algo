import math
from typing import List
from common.types import Position
from path_finding.hybrid_astar import Node
from common.consts import (
    TURNING_RADIUS,
    DIST_BL,
    DIST_BR,
    DIST_FL,
    DIST_FR
)


def backtracking_smooth_path(
    path: List["Node"]
) -> List[str]:
    if not path:
        return []

    merged = []
    for node in path[1:]:
        if not node.d:
            continue
        if merged and can_merge_nodes(merged[-1], node):
            merged[-1].d += node.d
        else:
            merged.append(node.clone())
    return convert_segments_to_commands(merged)


def _backtracking_smooth_path(
    path: List["Node"]
) -> List[str]:
    if not path:
        return []

    # Initialize the list of contiguous segments of smooth motion
    smooth_segments = []
    # current_segment = []

    # Iterate through the path nodes and group them into segments

    current_node = path[-1]

    while current_node.parent:
        prev_node = current_node.parent

        # Check if the current node can be added to the current segment
        if can_merge_nodes(prev_node, current_node):
            current_node.pos = prev_node.pos
            current_node.c_pos = prev_node.c_pos
            current_node.parent = prev_node.parent
    # TODO: Confirm that the node.g is the cost to travel from starting point to node and not from parent node to child node
    # TODO: Do I need to edit the costs of the nodes?
            # current_node.g = prev_node.g
            current_node.d += prev_node.d
        else:
            # If not, start a new segment
            smooth_segments.append(current_node)
            current_node = prev_node

    # Add the last segment to the list
    smooth_segments.append(current_node)

    # Convert segments to motion commands
    motion_commands = convert_segments_to_commands(smooth_segments[::-1])

    return motion_commands


def can_merge_nodes(
    parentNode: Node,
    childNode: Node
) -> bool:
    if not parentNode:
        return False
    # if childNode.v != parentNode.v:
    #     return False
    if childNode.v == parentNode.v and childNode.s == 0 and parentNode.s == 0:
        return True
    return False


def convert_segments_to_commands(
    segments: List["Node"]
) -> list[str]:
    '''
        Converts Path Segments to Commands

        Returns:
            [command, AlgoOutputLIvePosition (end_position of robot after executing the command)]
    '''
    result = []
    from main import AlgoOutputLivePosition

    # Old Version
    GRID_CELL_CM = 10
    for segment in segments:
        if segment.v == 1:
            if segment.s == -1:
                result.append([
                    "L",
                    AlgoOutputLivePosition(
                        x = segment.pos.x // GRID_CELL_CM,
                        y = segment.pos.y // GRID_CELL_CM,
                        d = convertThetatoNumericDirection(segment.pos.theta)
                    )
                ])
            elif segment.s == 0:
                if int(segment.d) > 0:
                    result.append([
                        "F," + str(int(segment.d)),
                        AlgoOutputLivePosition(
                            x = segment.pos.x // GRID_CELL_CM,
                            y = segment.pos.y // GRID_CELL_CM,
                            d = convertThetatoNumericDirection(segment.pos.theta)
                        )
                    ])
            elif segment.s == 1:
                result.append([
                    "R",
                    AlgoOutputLivePosition(
                        x = segment.pos.x // GRID_CELL_CM,
                        y = segment.pos.y // GRID_CELL_CM,
                        d = convertThetatoNumericDirection(segment.pos.theta)
                    )
                ])
        elif segment.v == -1:
            if segment.s == -1:
                result.append([
                    "BL",
                    AlgoOutputLivePosition(
                        x = segment.pos.x // GRID_CELL_CM,
                        y = segment.pos.y // GRID_CELL_CM,
                        d = convertThetatoNumericDirection(segment.pos.theta)
                    )
                ])
            elif segment.s == 0:
                result.append([
                    "B," + str(int(segment.d)),
                    AlgoOutputLivePosition(
                        x = segment.pos.x // GRID_CELL_CM,
                        y = segment.pos.y // GRID_CELL_CM,
                        d = convertThetatoNumericDirection(segment.pos.theta)
                    )
                ])
            elif segment.s == 1:
                result.append([
                    "BR",
                    AlgoOutputLivePosition(
                        x = segment.pos.x // GRID_CELL_CM,
                        y = segment.pos.y // GRID_CELL_CM,
                        d = convertThetatoNumericDirection(segment.pos.theta)
                    )
                ])

    # [Merge Commands] Combine similar commands together to reduce the number of commands (to improve Robot Execution time)
    resultCombined = []
    n = 0
    for i in range(len(result)):
        string = result[i][0].split(',')
        if i == 0:
            resultCombined.append(result[i])
            n = 0
        elif string[0] == "L" or string[0] == "R" or string[0] == "BL" or string[0] == "BR":
            resultCombined.append(result[i])
            n += 1
        else:
            prevstr = resultCombined[n][0].split(',')
            if string[0] == prevstr[0]:
                new = string[0]+','+str(int(string[1])+int(prevstr[1]))
                resultCombined[n] = [new, result[i][1]]
            else:
                resultCombined.append(result[i])
                n += 1
    
    def _get_translated_straight_distance(direction: str, distance: int) -> int:
        """
            To stop the robot's straight movement slightly later to get the actual desired distance to be travelled by the robot.
            Value (in cm) is measured via trial and error

            Parameter:
                direction: Robot's direction
                distance: Distance that the Robot should travel physically.
        """
        # For Stop Command
        if distance == 0:
            return 0
        
        if direction == "F":
            return distance-1
        elif direction == "B":
            if distance < 50:
                return distance
            else:
                return distance+2
    
    # Get translated straight distance to early/late stop the robot to get desired distance travelled
    for i in range(len(resultCombined)):
        result = resultCombined[i][0]
        split_result = result.split(",")

        # Skip if command is a turn command
        if split_result[0] == "L" or split_result[0] == "R" or split_result[0] == "BL" or split_result[0] == "BR":
            continue

        direction, distance = split_result[0], int(split_result[1])
        split_result[1] = str(_get_translated_straight_distance(direction, distance))
        resultCombined[i][0] = ",".join(split_result)
    
    return resultCombined


def merge_cmds(cmds: List[List[str]]) -> str:
    '''
        Senior's code: Not Used
    '''
    s = ''
    for i, seg in enumerate(cmds):
        if not seg:
            continue
        s += ','.join(seg) + '-'

    return s.strip('-')


# def convertThetatoNumericDirection(theta):
#     '''
#         Converts Robot's Theta to Numeric Representation of Robot's Direction

#         Returns:
#             1: North
#             2: South
#             3: East
#             4: West
#     '''
#     # East
#     if -math.pi / 4 <= theta and theta < math.pi / 4:
#         return 3
#     # North
#     elif math.pi / 4 <= theta and theta <= 3 * math.pi / 4:
#         return 1
#     # West
#     elif (3 * math.pi / 4 < theta and theta <= math.pi) or (-math.pi <= theta and theta < -3 * math.pi / 4):
#         return 4
#     # South
#     elif (-3 * math.pi / 4 <= theta and theta <= -math.pi / 4):
#         return 2

#     # Default: North
#     return 1

def convertThetatoNumericDirection(theta):
    '''
        Converts Robot's Theta to Numeric Representation of Robot's Direction

        Returns:
            1: North
            2: South
            3: East
            4: West
    '''
    if theta >= math.pi or theta <= -math.pi:
        theta = theta - (2*math.pi)
    else:
        theta = theta
    # East
    if -math.pi / 4 <= theta and theta < math.pi / 4:
        return 'E' #3
    # North
    elif math.pi / 4 <= theta and theta <= 3 * math.pi / 4:
        return 'N' #1
    # West
    elif (3 * math.pi / 4 < theta and theta <= math.pi) or (-math.pi <= theta and theta < -3 * math.pi / 4):
        return 'W' #4
    # South
    elif (-3 * math.pi / 4 <= theta and theta <= -math.pi / 4):
        return 'S' #2
    
    # Default: North
    return theta

