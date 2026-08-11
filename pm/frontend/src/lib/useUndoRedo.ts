"use client";

import { useState, useCallback } from "react";

export function useUndoRedo<T>(initialState: T, maxHistory: number = 20) {
  const [past, setPast] = useState<T[]>([]);
  const [present, setPresent] = useState<T>(initialState);
  const [future, setFuture] = useState<T[]>([]);

  const canUndo = past.length > 0;
  const canRedo = future.length > 0;

  const set = useCallback(
    (newState: T | ((prev: T) => T)) => {
      setPresent((currentPresent) => {
        const computedState =
          typeof newState === "function"
            ? (newState as (prev: T) => T)(currentPresent)
            : newState;

        if (computedState === currentPresent) return currentPresent;

        setPast((prevPast) => {
          const nextPast = [...prevPast, currentPresent];
          if (nextPast.length > maxHistory) {
            return nextPast.slice(nextPast.length - maxHistory);
          }
          return nextPast;
        });

        setFuture([]);
        return computedState;
      });
    },
    [maxHistory]
  );

  const reset = useCallback((newInitialState: T) => {
    setPast([]);
    setPresent(newInitialState);
    setFuture([]);
  }, []);

  const undo = useCallback((): T | null => {
    let resultState: T | null = null;
    setPast((prevPast) => {
      if (prevPast.length === 0) return prevPast;
      const previous = prevPast[prevPast.length - 1];
      const newPast = prevPast.slice(0, prevPast.length - 1);

      setPresent((currentPresent) => {
        setFuture((prevFuture) => [currentPresent, ...prevFuture]);
        resultState = previous;
        return previous;
      });

      return newPast;
    });
    return resultState;
  }, []);

  const redo = useCallback((): T | null => {
    let resultState: T | null = null;
    setFuture((prevFuture) => {
      if (prevFuture.length === 0) return prevFuture;
      const next = prevFuture[0];
      const newFuture = prevFuture.slice(1);

      setPresent((currentPresent) => {
        setPast((prevPast) => [...prevPast, currentPresent]);
        resultState = next;
        return next;
      });

      return newFuture;
    });
    return resultState;
  }, []);

  return {
    state: present,
    set,
    reset,
    undo,
    redo,
    canUndo,
    canRedo,
    historyLength: past.length,
  };
}
