"use client";

import * as React from "react";

const MAX_HISTORY = 50;

export function useUndoRedo<T>(externalValue: T, resetKey?: string) {
  const [present, setPresent] = React.useState(externalValue);
  const [canUndo, setCanUndo] = React.useState(false);
  const [canRedo, setCanRedo] = React.useState(false);
  const pastRef = React.useRef<T[]>([]);
  const futureRef = React.useRef<T[]>([]);

  const syncFlags = () => {
    setCanUndo(pastRef.current.length > 0);
    setCanRedo(futureRef.current.length > 0);
  };

  React.useEffect(() => {
    setPresent(externalValue);
    pastRef.current = [];
    futureRef.current = [];
    syncFlags();
  }, [resetKey]);

  const commit = React.useCallback((next: T) => {
    setPresent((current) => {
      pastRef.current = [...pastRef.current.slice(-MAX_HISTORY + 1), current];
      futureRef.current = [];
      syncFlags();
      return next;
    });
  }, []);

  const undo = React.useCallback((): T => {
    let result = present;
    setPresent((current) => {
      const prev = pastRef.current.pop();
      if (prev === undefined) {
        result = current;
        return current;
      }
      futureRef.current.push(current);
      result = prev;
      syncFlags();
      return prev;
    });
    return result;
  }, [present]);

  const redo = React.useCallback((): T => {
    let result = present;
    setPresent((current) => {
      const next = futureRef.current.pop();
      if (next === undefined) {
        result = current;
        return current;
      }
      pastRef.current.push(current);
      result = next;
      syncFlags();
      return next;
    });
    return result;
  }, [present]);

  return { present, commit, undo, redo, canUndo, canRedo };
}
