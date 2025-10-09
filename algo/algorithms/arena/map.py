from math import pi
import numpy as np
from typing import List

from arena.obstacle import Obstacle
from common.consts import (
    MAP_HEIGHT,
    MAP_WIDTH,
    OBSTACLE_WIDTH,
    ROBOT_HEIGHT,
    ROBOT_WIDTH,
    EDGE_ERR,
    FL_X_BOUND,
    FL_Y_BOUND,
    FR_X_BOUND,
    FR_Y_BOUND,
    BL_X_BOUND,
    BL_Y_BOUND,
    BR_X_BOUND,
    BR_Y_BOUND,
    DIST_FW,
    DIST_BW,
    BUFFER
)
from common.enums import Movement
from common.types import Position
from common.enums import Movement
from common.utils import calc_vector


class Map:
    bounds = {
        Movement.FWD: [
            BUFFER,
            BUFFER + ROBOT_WIDTH,
            BUFFER + DIST_FW + ROBOT_HEIGHT,
            BUFFER
        ],
        Movement.BWD: [
            BUFFER,
            BUFFER + ROBOT_WIDTH,
            BUFFER + ROBOT_HEIGHT,
            BUFFER + DIST_BW
        ],
        Movement.FWD_LEFT: FL_X_BOUND + FL_Y_BOUND,
        Movement.FWD_RIGHT: FR_X_BOUND + FR_Y_BOUND,
        Movement.BWD_LEFT: BL_X_BOUND + BL_Y_BOUND,
        Movement.BWD_RIGHT: BR_X_BOUND + BR_Y_BOUND
    }

    def __init__(self, obstacles: List["Obstacle"]):
        self.obstacles = obstacles

    def _within_bounds(self, x: float, y: float) -> bool:
        """Checks if (x, y) is within the boundary of the Map"""
        return (
            -EDGE_ERR <= x <= MAP_WIDTH + EDGE_ERR
            and -EDGE_ERR <= y <= MAP_HEIGHT + EDGE_ERR
        )

    def is_valid(self, pos: Position, obstacles: List["Obstacle"]) -> bool:
        # Robot
        r_origin = np.array([pos.x, pos.y])
        r_vec_up = calc_vector(pos.theta, ROBOT_HEIGHT)
        r_vec_right = calc_vector(
            pos.theta - pi / 2, ROBOT_WIDTH
        )

        # Check if Robot is within the bound of the map
        if not (
            self._within_bounds(*r_origin)
            and self._within_bounds(*(r_origin + r_vec_up))
            and self._within_bounds(*(r_origin + r_vec_right))
            and self._within_bounds(*(r_origin + r_vec_right + r_vec_up))
        ):
            return False

        # Robot Segments / Edges
        r_segments = [
            (r_origin, r_origin + r_vec_up),  # left edge
            (r_origin, r_origin + r_vec_right),  # btm edge
            (r_origin + r_vec_up, r_origin + r_vec_up + r_vec_right),  # top edge
            (r_origin + r_vec_right, r_origin +
             r_vec_right + r_vec_up),  # right edge
        ]

        # Robot Corners
        r_corners = [
            r_origin,  # btm left
            r_origin + r_vec_right,  # btm right
            r_origin + r_vec_up,  # top left
            r_origin + r_vec_up + r_vec_right,  # top right
        ]

        # For every obstacle, check if any of the 4 obstacle corners lies within the robot
        # To increase the virtual boundary of the obstacle (in cm)
        EXTRA_VIRTUAL_BOUNDARY = 10
        for obs in obstacles:
            # Obstacle bounds with virtual boundary
            o_btm = obs.y + EDGE_ERR - EXTRA_VIRTUAL_BOUNDARY
            o_left = obs.x + EDGE_ERR - EXTRA_VIRTUAL_BOUNDARY
            o_top = obs.y + OBSTACLE_WIDTH - EDGE_ERR + EXTRA_VIRTUAL_BOUNDARY
            o_right = obs.x + OBSTACLE_WIDTH - EDGE_ERR + EXTRA_VIRTUAL_BOUNDARY
            
            # Check 1: Robot corners inside obstacle
            for cx, cy in r_corners:
                if o_left <= cx <= o_right and o_btm <= cy <= o_top:
                    return False
            
            # Check 2: Obstacle corners inside robot (IMPROVED)
            obstacle_corners = [
                np.array([o_left, o_btm]),
                np.array([o_left, o_top]),
                np.array([o_right, o_top]),
                np.array([o_right, o_btm])
            ]
            
            for o_corner in obstacle_corners:
                if self._point_in_rotated_rect(o_corner, r_origin, r_vec_up, r_vec_right):
                    return False
            
            # Check 3: Edge-to-edge intersection (NEW - CRITICAL)
            obstacle_edges = [
                (np.array([o_left, o_btm]), np.array([o_left, o_top])),    # left
                (np.array([o_left, o_top]), np.array([o_right, o_top])),   # top
                (np.array([o_right, o_top]), np.array([o_right, o_btm])),  # right
                (np.array([o_right, o_btm]), np.array([o_left, o_btm]))    # bottom
            ]
            
            for r_seg in r_segments:
                for o_seg in obstacle_edges:
                    if self._segments_intersect(r_seg[0], r_seg[1], o_seg[0], o_seg[1]):
                        return False
        
        return True

    def priority_obs(
        self,
        pos: "Position",
        move: "Movement"
    ) -> List["Obstacle"]:
        """
            This function helps identify obstacles that are potentially in the path of the robot based on
            its current position and movement direction,
            allowing the robot to prioritize its actions accordingly.
        """
        v_t = calc_vector(pos.theta, 1)
        v_r = calc_vector(pos.theta - pi/2, 1)

        bounds = self.bounds[move]
        st = np.array([pos.x, pos.y])
        tl = st + v_t*bounds[2] - v_r*bounds[0]
        br = st - v_t*bounds[3] + v_r*bounds[1]

        x_bounds = sorted([br[0], tl[0]])
        y_bounds = sorted([br[1], tl[1]])

        return list(filter(lambda o: x_bounds[0] < o.middle[0] < x_bounds[1] and y_bounds[0] < o.middle[1] < y_bounds[1], self.obstacles))
    
    def _point_in_rotated_rect(self, point, origin, vec_up, vec_right):
        """Check if point is inside rotated rectangle defined by origin and vectors"""
        v = point - origin
        # Project onto local axes
        proj_right = np.dot(v, vec_right) / np.dot(vec_right, vec_right)
        proj_up = np.dot(v, vec_up) / np.dot(vec_up, vec_up)
        return 0 <= proj_right <= 1 and 0 <= proj_up <= 1

    def _segments_intersect(self, p1, p2, p3, p4):
        """Check if line segment p1-p2 intersects with p3-p4"""
        def ccw(A, B, C):
            return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
        
        return ccw(p1,p3,p4) != ccw(p2,p3,p4) and ccw(p1,p2,p3) != ccw(p1,p2,p4)