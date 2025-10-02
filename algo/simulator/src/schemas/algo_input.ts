import { Obstacle } from "./obstacle";

export enum AlgoType {
  EXHAUSTIVE_ASTAR = "Exhaustive Astar",
  EUCLIDEAN = "Euclidean",
}

export const AlgoTypeList = [AlgoType.EXHAUSTIVE_ASTAR, AlgoType.EUCLIDEAN];

export interface AlgoInput {
  cat: "obstacles";
  value: {
    obstacles: Obstacle[];
    mode: 0; // 0: Task 1
  };
  server_mode: string;
  algo_type: string;
}
