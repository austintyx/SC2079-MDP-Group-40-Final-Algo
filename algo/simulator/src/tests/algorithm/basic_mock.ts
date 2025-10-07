import { AlgoTestDataInterface } from ".";
import { Obstacle, ObstacleDirection } from "../../schemas/obstacle";

const obstacles: Obstacle[] = [
  // { id: 1, x: 15, y: 10, d: ObstacleDirection.W },
  // { id: 2, x: 1, y: 18, d: ObstacleDirection.S },
  { id: 1, x: 1, y: 15, d: ObstacleDirection.E },
  { id: 2, x: 5, y: 11, d: ObstacleDirection.S },
  { id: 3, x: 7, y: 5, d: ObstacleDirection.N },
  { id: 4, x: 12, y: 14, d: ObstacleDirection.N },
  { id: 5, x: 12, y: 2, d: ObstacleDirection.E },
  { id: 6, x: 16, y: 19, d: ObstacleDirection.S },
  { id: 7, x: 19, y: 8, d: ObstacleDirection.W },
];

export const AlgoTestBasicMock: AlgoTestDataInterface = {
  obstacles: obstacles,
};
