import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from xsigmamodules.Util import (
    zabrClassicalAnalytics,
    zabrMixtureAnalytics,
    sabrPdeAnalyticsClassic,
    zabr_output_type,
)
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma


class SABRModel:
    def __init__(self, forward, expiry):
        self.forward = forward
        self.expiry = expiry

    def create_controls(self, frame):
        raise NotImplementedError("Subclasses must implement create_controls method")

    def update_plot(self):
        raise NotImplementedError("Subclasses must implement update_plot method")

    def reset_controls(self):
        raise NotImplementedError("Subclasses must implement reset_controls method")


class ZABRClassicModel(SABRModel):
    def __init__(self, forward, expiry):
        super().__init__(forward, expiry)
        self.N = 100
        self.strikes = np.linspace(0.0, 0.2, self.N)
        self.initial_values = {
            "beta": (0.7, 0, 1),
            "shift": (0.0, 0, 0.1),
            "alpha": (0.0873, 0, 0.2),
            "nu": (0.47, 0, 1),
            "rho": (-0.48, -1, 1),
            "gamma": (1.0, 0, 2),
        }
        self.controls = {}

    def create_controls(self, frame):
        for param, (value, min_val, max_val) in self.initial_values.items():
            var = tk.DoubleVar(value=value)
            label = ttk.Label(frame, text=f"{param.capitalize()}:")
            slider = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient="horizontal",
                length=200,
            )
            entry = ttk.Entry(frame, textvariable=var, width=8)

            label.grid(row=len(self.controls), column=0, sticky="e", padx=5, pady=5)
            slider.grid(row=len(self.controls), column=1, sticky="ew", padx=5, pady=5)
            entry.grid(row=len(self.controls), column=2, sticky="w", padx=5, pady=5)

            self.controls[param] = (slider, var, entry)
        return frame

    def update_plot(self):
        obj = zabrClassicalAnalytics(
            self.expiry,
            self.forward,
            self.controls["beta"][1].get(),
            self.controls["shift"][1].get(),
            self.controls["alpha"][1].get(),
            self.controls["nu"][1].get(),
            self.controls["rho"][1].get(),
            self.controls["gamma"][1].get(),
        )

        implied_vol = np.zeros(self.N)
        implied_vol_ = numpyToXsigma(implied_vol)
        price = np.zeros(self.N)
        price_ = numpyToXsigma(price)
        strikes_ = numpyToXsigma(self.strikes)

        obj.values(price_, strikes_, zabr_output_type.PRICES, True)
        obj.density(implied_vol_, price_, strikes_)

        return self.strikes, xsigmaToNumpy(implied_vol_)

    def reset_controls(self):
        for param, (value, _, _) in self.initial_values.items():
            self.controls[param][1].set(value)


class ZABRMixtureModel(SABRModel):
    def __init__(self, forward, expiry):
        super().__init__(forward, expiry)
        self.N = 601
        self.strikes = np.linspace(-0.01, 0.2, self.N)
        self.initial_values = {
            "beta1": (0.2, 0, 1),
            "beta2": (1.55, 0, 2),
            "alpha": (0.014862, 0, 0.1),
            "nu": (0.2654, 0, 1),
            "rho": (-0.3763, -1, 1),
            "gamma": (1.0, 0, 2),
        }
        self.controls = {}
        self.fixed_params = {
            "d": 0.0005,
            "high_strike_transition": 0.1,
            "asymptotic_volatility_low": 0.0001,
            "low_strike_transition": 0.02,
            "forward_cut_off": 0.02,
            "smoothing_factor": 0.001,
        }

    def create_controls(self, frame):
        for param, (value, min_val, max_val) in self.initial_values.items():
            var = tk.DoubleVar(value=value)
            label = ttk.Label(frame, text=f"{param.capitalize()}:")
            slider = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient="horizontal",
                length=200,
            )
            entry = ttk.Entry(frame, textvariable=var, width=8)

            label.grid(row=len(self.controls), column=0, sticky="e", padx=5, pady=5)
            slider.grid(row=len(self.controls), column=1, sticky="ew", padx=5, pady=5)
            entry.grid(row=len(self.controls), column=2, sticky="w", padx=5, pady=5)

            self.controls[param] = (slider, var, entry)
        return frame

    def update_plot(self):
        obj = zabrMixtureAnalytics(
            self.expiry,
            self.forward,
            self.controls["alpha"][1].get(),
            self.controls["beta1"][1].get(),
            self.controls["beta2"][1].get(),
            self.fixed_params["d"],
            self.fixed_params["asymptotic_volatility_low"],
            self.controls["nu"][1].get(),
            self.controls["rho"][1].get(),
            self.controls["gamma"][1].get(),
            self.fixed_params["high_strike_transition"],
            self.fixed_params["low_strike_transition"],
            self.fixed_params["forward_cut_off"],
            self.fixed_params["smoothing_factor"],
        )

        implied_vol = np.zeros(self.N)
        implied_vol_ = numpyToXsigma(implied_vol)
        price = np.zeros(self.N)
        price_ = numpyToXsigma(price)
        strikes_ = numpyToXsigma(self.strikes)

        obj.values(price_, strikes_, zabr_output_type.PRICES, True)
        obj.density(implied_vol_, price_, strikes_)

        return self.strikes, xsigmaToNumpy(implied_vol_)

    def reset_controls(self):
        for param, (value, _, _) in self.initial_values.items():
            self.controls[param][1].set(value)


class SABRPDEModel(SABRModel):
    def __init__(self, forward, expiry):
        super().__init__(forward, expiry)
        self.initial_values = {
            "alpha": (0.014862, 0, 0.1),
            "beta": (0.5, 0, 1),
            "nu": (0.2654, 0, 1),
            "rho": (-0.3763, -1, 1),
            "shift": (0.01, 0, 0.1),
            "N": (100, 50, 200),
            "timesteps": (5, 1, 20),
            "nd": (3, 1, 5),
        }
        self.controls = {}

    def create_controls(self, frame):
        for param, (value, min_val, max_val) in self.initial_values.items():
            if param in ["N", "timesteps", "nd"]:
                var = tk.IntVar(value=int(value))
            else:
                var = tk.DoubleVar(value=value)
            label = ttk.Label(frame, text=f"{param.capitalize()}:")
            slider = ttk.Scale(
                frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient="horizontal",
                length=200,
            )
            entry = ttk.Entry(frame, textvariable=var, width=8)

            label.grid(row=len(self.controls), column=0, sticky="e", padx=5, pady=5)
            slider.grid(row=len(self.controls), column=1, sticky="ew", padx=5, pady=5)
            entry.grid(row=len(self.controls), column=2, sticky="w", padx=5, pady=5)

            self.controls[param] = (slider, var, entry)
        return frame

    def update_plot(self):
        obj = sabrPdeAnalyticsClassic(
            self.expiry,
            self.forward,
            self.controls["alpha"][1].get(),
            self.controls["beta"][1].get(),
            self.controls["nu"][1].get(),
            self.controls["rho"][1].get(),
            self.controls["shift"][1].get(),
            int(self.controls["N"][1].get()),
            int(self.controls["timesteps"][1].get()),
            int(self.controls["nd"][1].get()),
        )

        implied_vol = xsigmaToNumpy(obj.density())
        strikes = xsigmaToNumpy(obj.strikes())

        return strikes, implied_vol

    def reset_controls(self):
        for param, (value, _, _) in self.initial_values.items():
            self.controls[param][1].set(value)


class SABRModelsGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("SABR Models GUI")
        self.master.geometry("1200x800")

        self.style = ttkb.Style()
        self.style.configure("TNotebook.Tab", padding=[10, 5])

        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        forward = 0.0325
        expiry = 10

        self.models = {
            "ZABR Classic": ZABRClassicModel(forward, expiry),
            "ZABR Mixture": ZABRMixtureModel(forward, expiry),
            "SABR PDE": SABRPDEModel(forward, expiry),
        }

        for name, model in self.models.items():
            frame = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(frame, text=name)
            self.setup_model_tab(frame, model)

        # Theme selection
        self.theme_var = tk.StringVar(value=self.style.theme.name)
        self.theme_label = ttk.Label(self.master, text="Theme:")
        self.theme_label.pack(side=tk.LEFT, padx=(10, 0))
        self.theme_dropdown = ttk.Combobox(
            self.master, textvariable=self.theme_var, values=self.style.theme_names()
        )
        self.theme_dropdown.pack(side=tk.LEFT, padx=(0, 10))
        self.theme_dropdown.bind("<<ComboboxSelected>>", self.change_theme)

    def setup_model_tab(self, frame, model):
        plot_frame = ttk.Frame(frame)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        fig, ax = plt.subplots(figsize=(10, 6))
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        controls_frame = ttk.Frame(frame, padding=10)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

        model.create_controls(controls_frame)

        for slider, var, entry in model.controls.values():
            slider.config(command=lambda _: self.update_plot(ax, canvas, model))
            entry.bind("<Return>", lambda _: self.update_plot(ax, canvas, model))

        reset_button = ttk.Button(
            controls_frame,
            text="Reset",
            style="info.TButton",
            command=lambda: self.reset_model(model, ax, canvas),
        )
        reset_button.grid(row=len(model.controls), column=0, columnspan=3, pady=10)

        self.update_plot(ax, canvas, model)

    def update_plot(self, ax, canvas, model):
        ax.clear()
        strikes, implied_vol = model.update_plot()

        # Excel-like styling
        ax.plot(strikes, implied_vol, linewidth=2, color="#4472C4")  # Excel blue color
        ax.set_xlabel("Strikes", fontsize=12)
        ax.set_ylabel("Implied Volatility", fontsize=12)
        ax.set_title(f"{model.__class__.__name__} Implied Volatility", fontsize=14)
        ax.grid(True, linestyle="--", alpha=0.7, color="#D9D9D9")  # Light gray grid
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(
            axis="both", which="both", bottom=False, top=False, left=False, right=False
        )

        # Set background color to light gray
        ax.set_facecolor("#F2F2F2")

        # Add subtle gridlines
        ax.grid(True, linestyle="-", alpha=0.5, color="white")

        canvas.draw()

    def reset_model(self, model, ax, canvas):
        model.reset_controls()
        self.update_plot(ax, canvas, model)

    def change_theme(self, event):
        selected_theme = self.theme_var.get()
        self.style.theme_use(selected_theme)


if __name__ == "__main__":
    root = ttkb.Window(themename="flatly")
    app = SABRModelsGUI(root)
    root.mainloop()
