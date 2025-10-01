"""Tkinter based UI for the Blackjack counting helper."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from .logic import CountingMode, CountingSession


class BlackjackCounterApp:
    """Application controller that wires the Tkinter views together."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Blackjack Counter")
        self.root.minsize(900, 600)
        self.root.resizable(True, True)

        self._session: Optional[CountingSession] = None

        self._content = ttk.Frame(self.root, padding=24)
        self._content.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self._running_count_var = tk.StringVar(value="0.0")
        self._true_count_var = tk.StringVar(value="0.0")

        self._history_listbox: Optional[tk.Listbox] = None
        self._mode_label_var = tk.StringVar(value="")

        self.show_main_menu()

    # ------------------------------------------------------------------
    # Screen transitions
    # ------------------------------------------------------------------
    def clear_content(self) -> None:
        for widget in self._content.winfo_children():
            widget.destroy()
        self._history_listbox = None

    def show_main_menu(self) -> None:
        self._session = None
        self._running_count_var.set("0.0")
        self._true_count_var.set("0.0")
        self.clear_content()

        wrapper = ttk.Frame(self._content)
        wrapper.pack(expand=True)

        title = ttk.Label(wrapper, text="Blackjack Counter", font=("Helvetica", 24, "bold"))
        title.pack(pady=(0, 32))

        new_game_button = ttk.Button(wrapper, text="New Game", command=self.show_mode_selection)
        new_game_button.pack(ipadx=16, ipady=8)

    def show_mode_selection(self) -> None:
        self.clear_content()

        wrapper = ttk.Frame(self._content)
        wrapper.pack(expand=True, fill=tk.BOTH)

        title = ttk.Label(wrapper, text="Choose a counting system", font=("Helvetica", 20, "bold"))
        title.pack(pady=(0, 24))

        buttons = ttk.Frame(wrapper)
        buttons.pack()

        ttk.Button(
            buttons,
            text="HiLo",
            command=lambda: self.start_session(CountingMode.HILO),
        ).grid(row=0, column=0, padx=12)

        ttk.Button(
            buttons,
            text="Wong Halves",
            command=lambda: self.start_session(CountingMode.WONG_HALVES),
        ).grid(row=0, column=1, padx=12)

    def start_session(self, mode: CountingMode) -> None:
        self._session = CountingSession(mode=mode)
        self._running_count_var.set("0.0")
        self._true_count_var.set("0.0")

        if mode is CountingMode.HILO:
            self.show_hilo_screen()
        else:
            self.show_wong_halves_screen()

    # ------------------------------------------------------------------
    # Counting layouts
    # ------------------------------------------------------------------
    def show_hilo_screen(self) -> None:
        self.clear_content()
        container = ttk.Frame(self._content)
        container.pack(expand=True, fill=tk.BOTH)
        self._mode_label_var.set(CountingMode.HILO.value)

        counting_frame = self._build_counting_panel(container)
        counting_frame.pack(expand=True, fill=tk.BOTH)

    def show_wong_halves_screen(self) -> None:
        self.clear_content()
        container = ttk.Frame(self._content)
        container.pack(expand=True, fill=tk.BOTH)
        self._mode_label_var.set(CountingMode.WONG_HALVES.value)

        outer = ttk.Frame(container)
        outer.pack(expand=True, fill=tk.BOTH)
        outer.columnconfigure(0, weight=3, uniform="outer")
        outer.columnconfigure(1, weight=1, uniform="outer")
        outer.rowconfigure(0, weight=1)

        counting_frame = self._build_counting_panel(outer)
        counting_frame.grid(row=0, column=0, sticky="nsew")

        cards_frame = ttk.LabelFrame(outer, text="Cards")
        cards_frame.grid(row=0, column=1, sticky="sew", padx=(16, 0), pady=16)
        for col in range(4):
            cards_frame.columnconfigure(col, weight=1)

        card_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        for index, label in enumerate(card_labels):
            row = index // 4
            col = index % 4
            ttk.Button(
                cards_frame,
                text=label,
                command=lambda value=label: self._record_action(value.lower()),
            ).grid(row=row, column=col, padx=6, pady=6, sticky="ew")

    def _build_counting_panel(self, parent: tk.Widget) -> ttk.Frame:
        frame = ttk.Frame(parent, padding=16)
        for col, weight in enumerate((1, 2, 1, 2)):
            frame.columnconfigure(col, weight=weight, uniform="panel")
        frame.rowconfigure(0, weight=1)

        controls = ttk.Frame(frame)
        controls.grid(row=0, column=0, sticky="nw", padx=8, pady=8)
        controls.columnconfigure(0, weight=1)

        ttk.Button(controls, text="Reset Shoe", command=self._handle_reset).pack(fill=tk.X, pady=(0, 8))
        ttk.Button(controls, text="Menu", command=self.show_mode_selection).pack(fill=tk.X)

        history_frame = ttk.LabelFrame(frame, text="Previously Counted Numbers")
        history_frame.grid(row=0, column=1, sticky="new", padx=8, pady=8)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(history_frame, height=8)
        listbox.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4, 0))
        self._history_listbox = listbox

        low_button = ttk.Button(frame, text="Low", command=lambda: self._record_action("low"))
        low_button.grid(row=1, column=1, sticky="ew", padx=8, pady=(0, 8))

        true_frame = ttk.LabelFrame(frame, text="True Count")
        true_frame.grid(row=0, column=2, sticky="new", padx=8, pady=8)
        true_label = ttk.Label(
            true_frame,
            textvariable=self._true_count_var,
            font=("Helvetica", 24, "bold"),
            anchor=tk.CENTER,
        )
        true_label.pack(expand=True, fill=tk.X, pady=12)

        ttk.Button(frame, text="Undo", command=self._handle_undo).grid(row=1, column=2, sticky="ew", padx=8, pady=(0, 8))

        running_frame = ttk.LabelFrame(frame, text="Running Count")
        running_frame.grid(row=0, column=3, sticky="new", padx=8, pady=8)
        running_label = ttk.Label(
            running_frame,
            textvariable=self._running_count_var,
            font=("Helvetica", 24, "bold"),
            anchor=tk.CENTER,
        )
        running_label.pack(expand=True, fill=tk.X, pady=12)

        ttk.Button(frame, text="Hi", command=lambda: self._record_action("hi")).grid(
            row=1, column=3, sticky="ew", padx=8, pady=(0, 8)
        )

        mode_badge = ttk.Label(frame, textvariable=self._mode_label_var, anchor=tk.CENTER)
        mode_badge.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        return frame

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def _record_action(self, action: str) -> None:
        if not self._session:
            return
        event = self._session.record_action(action)
        if event is None:
            return
        self._refresh_history()
        self._refresh_counts()

    def _handle_undo(self) -> None:
        if not self._session:
            return
        self._session.undo_last()
        self._refresh_history()
        self._refresh_counts()

    def _handle_reset(self) -> None:
        if not self._session:
            return
        self._session.reset()
        self._refresh_history()
        self._refresh_counts()

    def _refresh_counts(self) -> None:
        if not self._session:
            return
        self._running_count_var.set(f"{self._session.running_count:.2f}")
        self._true_count_var.set(f"{self._session.true_count:.2f}")

    def _refresh_history(self) -> None:
        if not self._history_listbox:
            return
        self._history_listbox.delete(0, tk.END)
        if not self._session:
            return
        for event in self._session.iter_history():
            self._history_listbox.insert(tk.END, event.display_text)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.root.mainloop()


__all__ = ["BlackjackCounterApp"]
