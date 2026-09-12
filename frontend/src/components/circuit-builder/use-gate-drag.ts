"use client";
import {
  useEffect,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
  type MouseEvent,
} from "react";
import type { GateDragSource, GateDropTarget } from "./edit-circuit";

type Drag = {
  source: GateDragSource;
  x: number;
  y: number;
  target: GateDropTarget | null;
};

/** Pointer capture provides the same direct manipulation for mouse, pen, and touch. */
export function useGateDrag(
  disabled: boolean,
  onDrop: (source: GateDragSource, target: GateDropTarget) => void,
) {
  const [drag, setDrag] = useState<Drag | null>(null);
  const pending = useRef<{
    source: GateDragSource;
    x: number;
    y: number;
    pointerId: number;
    element: HTMLElement;
    moved: boolean;
  } | null>(null);
  const suppressClick = useRef(false);
  const marked = useRef<HTMLElement | null>(null);

  function clear() {
    const current = pending.current;
    pending.current = null;
    if (current?.element.hasPointerCapture(current.pointerId))
      current.element.releasePointerCapture(current.pointerId);
    marked.current?.removeAttribute("data-drop-target");
    marked.current = null;
    setDrag(null);
  }
  useEffect(() => {
    function escape(event: KeyboardEvent) {
      if (event.key === "Escape" && pending.current) {
        suppressClick.current = pending.current.moved;
        clear();
      }
    }
    window.addEventListener("keydown", escape);
    return () => {
      window.removeEventListener("keydown", escape);
      marked.current?.removeAttribute("data-drop-target");
    };
  }, []);

  function targetAt(x: number, y: number): GateDropTarget | null {
    const element =
      document
        .elementFromPoint(x, y)
        ?.closest<HTMLElement>("[data-circuit-qubit][data-circuit-column]") ||
      null;
    if (marked.current !== element) {
      marked.current?.removeAttribute("data-drop-target");
      element?.setAttribute("data-drop-target", "true");
      marked.current = element;
    }
    return element
      ? {
          qubit: Number(element.dataset.circuitQubit),
          column: Number(element.dataset.circuitColumn),
        }
      : null;
  }

  return {
    drag,
    suppressDragClick(event: MouseEvent) {
      if (suppressClick.current) {
        event.preventDefault();
        event.stopPropagation();
        suppressClick.current = false;
      }
    },
    bind(source: GateDragSource) {
      return {
        onPointerDown(event: ReactPointerEvent<HTMLElement>) {
          if (disabled || event.button !== 0 || !event.isPrimary) return;
          suppressClick.current = false;
          pending.current = {
            source,
            x: event.clientX,
            y: event.clientY,
            pointerId: event.pointerId,
            element: event.currentTarget,
            moved: false,
          };
          event.currentTarget.setPointerCapture(event.pointerId);
        },
        onPointerMove(event: ReactPointerEvent<HTMLElement>) {
          const current = pending.current;
          if (!current || event.pointerId !== current.pointerId) return;
          if (
            !current.moved &&
            Math.hypot(event.clientX - current.x, event.clientY - current.y) < 6
          )
            return;
          current.moved = true;
          const edge = 64;
          if (event.clientY < edge) window.scrollBy(0, -16);
          else if (event.clientY > window.innerHeight - edge)
            window.scrollBy(0, 16);
          const canvas = document.querySelector<HTMLElement>(
            ".circuit-stage > div",
          );
          if (canvas) {
            const bounds = canvas.getBoundingClientRect();
            if (event.clientY >= bounds.top && event.clientY <= bounds.bottom) {
              if (event.clientX < bounds.left + 32) canvas.scrollLeft -= 16;
              else if (event.clientX > bounds.right - 32)
                canvas.scrollLeft += 16;
            }
          }
          setDrag({
            source: current.source,
            x: event.clientX,
            y: event.clientY,
            target: targetAt(event.clientX, event.clientY),
          });
        },
        onPointerUp(event: ReactPointerEvent<HTMLElement>) {
          const current = pending.current;
          if (!current || current.pointerId !== event.pointerId) return;
          if (current.moved) {
            suppressClick.current = true;
            // Mouse clicks follow pointerup in this turn; touch drags may emit
            // no click at all. Do not swallow the user's next toolbar action.
            window.setTimeout(() => {
              suppressClick.current = false;
            }, 0);
            const target = targetAt(event.clientX, event.clientY);
            if (target && !disabled) onDrop(current.source, target);
          }
          clear();
        },
        onPointerCancel() {
          suppressClick.current = !!pending.current?.moved;
          clear();
        },
        onLostPointerCapture() {
          if (pending.current) {
            suppressClick.current = pending.current.moved;
            clear();
          }
        },
        onDragStart(event: React.DragEvent) {
          event.preventDefault();
        },
      };
    },
  };
}
