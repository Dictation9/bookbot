import customtkinter as ctk

class ScrollableFrame(ctk.CTkFrame):
    """
    Usage:
        frame = ScrollableFrame(parent, width=900, height=700, always_show_scrollbar=True, show_horizontal_scrollbar=True)
        frame.pack(fill='both', expand=True)  # or .grid(..., sticky='nsew')
        # Add widgets to frame.inner
    """
    def __init__(self, parent, width=800, height=600, always_show_scrollbar=False, show_horizontal_scrollbar=False, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = ctk.CTkCanvas(self, width=width, height=height, borderwidth=0, highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.h_scrollbar = None
        if show_horizontal_scrollbar:
            self.h_scrollbar = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        self.inner = ctk.CTkFrame(self.canvas)
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        if self.h_scrollbar:
            self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        if self.h_scrollbar:
            self.h_scrollbar.pack(side="bottom", fill="x")
        # Mousewheel scrolling (local to canvas)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        # Make sure the frame expands with parent
        self.pack_propagate(False)
        self.grid_propagate(False)
        # Optionally force the scrollbar to always show
        if always_show_scrollbar:
            self.canvas.configure(scrollregion=(0, 0, width, height * 2))
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>") 