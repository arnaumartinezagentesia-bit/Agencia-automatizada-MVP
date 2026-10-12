import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import Page from "../app/page";

test("shows project identity and states analysis is not implemented", () => {
  render(<Page />);
  expect(screen.getByRole("heading", { name: "Agencia Automatizada" })).toBeTruthy();
  expect(screen.getByText(/analysis functionality is not implemented yet/i)).toBeTruthy();
});

test("renders no controls", () => {
  render(<Page />);
  expect(screen.queryAllByRole("button")).toHaveLength(0);
});
