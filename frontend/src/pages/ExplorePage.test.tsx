import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { ExplorePage } from "./ExplorePage";
test("explore is truthful when no dataset is available", () => { render(<ExplorePage />); expect(screen.getByText(/No validated data available/i)).toBeTruthy(); expect(screen.queryByText(/Boston|Celtics|Lakers/i)).toBeNull(); });
