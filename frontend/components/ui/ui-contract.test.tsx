import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { Button, Fold } from "./index";

test("a disabled button never invokes its action", () => {
  let calls = 0;
  render(
    <Button disabled onClick={() => (calls += 1)}>
      Disabled
    </Button>,
  );

  fireEvent.click(screen.getByRole("button"));

  expect(calls).toBe(0);
});

test("the native fold reveals its content when toggled", () => {
  render(<Fold summary="Why">Evidence</Fold>);
  const details = screen.getByText("Evidence").closest("details");

  expect(details).not.toHaveAttribute("open");
  fireEvent.click(screen.getByText("Why"));
  expect(details).toHaveAttribute("open");
});
