import { renderHook, act } from "@testing-library/react";
import { useUndoRedo } from "./useUndoRedo";

describe("useUndoRedo", () => {
  it("initializes with initial state", () => {
    const { result } = renderHook(() => useUndoRedo("initial"));
    expect(result.current.state).toBe("initial");
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(false);
  });

  it("pushes state and enables undo", () => {
    const { result } = renderHook(() => useUndoRedo("state1"));

    act(() => {
      result.current.set("state2");
    });

    expect(result.current.state).toBe("state2");
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(false);
  });

  it("undoes state change correctly", () => {
    const { result } = renderHook(() => useUndoRedo("state1"));

    act(() => {
      result.current.set("state2");
    });

    act(() => {
      result.current.undo();
    });

    expect(result.current.state).toBe("state1");
    expect(result.current.canUndo).toBe(false);
    expect(result.current.canRedo).toBe(true);
  });

  it("redoes state change correctly", () => {
    const { result } = renderHook(() => useUndoRedo("state1"));

    act(() => {
      result.current.set("state2");
    });

    act(() => {
      result.current.undo();
    });

    act(() => {
      result.current.redo();
    });

    expect(result.current.state).toBe("state2");
    expect(result.current.canUndo).toBe(true);
    expect(result.current.canRedo).toBe(false);
  });
});
