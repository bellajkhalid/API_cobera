import numpy as np
import matplotlib.pyplot as plt
from xsigmamodules.Util import (
    blackScholes,
    sigmaVolatilityInspired,
    volatility_type,
)
from xsigmamodules.Market import volatilityModelExtendedSvi
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma
from ipywidgets import interactive, FloatSlider, Button, HBox, VBox, Checkbox, Layout
import ipywidgets as widgets


def generate_sample_data(num_points=39, strike_range=(1800, 2700)):
    y_values = (
        np.array(
            [
                140.00,
                136.62,
                133.02,
                129.02,
                124.96,
                120.55,
                115.67,
                110.16,
                106.32,
                102.75,
                96.93,
                91.39,
                85.85,
                79.70,
                73.11,
                68.25,
                62.71,
                57.30,
                49.97,
                44.55,
                41.58,
                43.20,
                47.41,
                51.92,
                56.99,
                60.46,
                64.68,
                68.47,
                72.31,
                76.14,
                79.63,
                83.10,
                86.15,
                89.14,
                91.85,
                94.70,
                97.06,
                99.70,
                101.03,
            ]
        )
        / 100.0
    )

    strikes = np.linspace(strike_range[0], strike_range[1], num_points)
    spread = np.random.uniform(0, 0.01, num_points)
    bid_values = (
        np.interp(
            strikes, np.linspace(strike_range[0], strike_range[1], num_points), y_values
        )
        - spread
    )
    ask_values = (
        np.interp(
            strikes, np.linspace(strike_range[0], strike_range[1], num_points), y_values
        )
        + spread
    )
    mid_values = 0.5 * (bid_values + ask_values)

    return strikes, bid_values, ask_values, mid_values


def plot_volatility_smile(
    calibration_strikes, strikes, bid_values, ask_values, mid_values, vols
):
    plt.figure(figsize=(12, 8))
    plt.scatter(calibration_strikes, mid_values, label="Mid", color="blue", s=10)
    plt.scatter(calibration_strikes, bid_values, label="Bid", color="green", s=10)
    plt.scatter(calibration_strikes, ask_values, label="Ask", color="red", s=10)
    plt.plot(strikes, vols, label="Calibrated Vol", color="purple", linewidth=2)
    plt.xlabel("Strike")
    plt.ylabel("Implied Volatility")
    plt.title("Volatility Smile")
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_density(obj, strikes, spot, expiry):
    n = len(strikes)
    arrays = {
        "vols": np.zeros(n),
        "atm_sensitivity": np.zeros(n),
        "skew_sensitivity": np.zeros(n),
        "smile_sensitivity": np.zeros(n),
        "put_sensitivity": np.zeros(n),
        "call_sensitivity": np.zeros(n),
        "strike_sensitivity": np.zeros(n),
        "ref_sensitivity": np.zeros(n),
        "atm2_sensitivity": np.zeros(n),
        "ref2_sensitivity": np.zeros(n),
        "strike2_sensitivity": np.zeros(n),
    }

    obj.sensitivities(
        expiry, numpyToXsigma(strikes), *[numpyToXsigma(arr) for arr in arrays.values()]
    )

    density = [
        blackScholes.density(spot, strike, expiry, vol, strike_sens, strike2_sens)
        for strike, vol, strike_sens, strike2_sens in zip(
            strikes,
            arrays["vols"],
            arrays["strike_sensitivity"],
            arrays["strike2_sensitivity"],
        )
    ]

    plt.figure(figsize=(10, 6))
    plt.plot(strikes, density, "b-", label="Density")
    plt.xlabel("Strike")
    plt.ylabel("Density")
    plt.title("Density in terms of Strike")
    plt.legend()
    plt.grid(True)
    plt.show()


def calculate_vols_and_density(
    forward, params, model_type="asv", legacy_parametrisation=False
):
    n = 400
    strikes = np.linspace(0.5 * params["fwd"], 2.0 * params["fwd"], n)

    if model_type == "asv":
        obj = volatilityModelExtendedSvi(
            params["fwd"],
            params["ctrl_p"],
            params["ctrl_c"],
            params["atm"],
            params["skew"],
            params["smile"],
            params["put"],
            params["call"],
        )

        arrays = {
            "vols": np.zeros(n),
            "atm_sensitivity": np.zeros(n),
            "skew_sensitivity": np.zeros(n),
            "smile_sensitivity": np.zeros(n),
            "put_sensitivity": np.zeros(n),
            "call_sensitivity": np.zeros(n),
            "strike_sensitivity": np.zeros(n),
            "ref_sensitivity": np.zeros(n),
            "atm2_sensitivity": np.zeros(n),
            "ref2_sensitivity": np.zeros(n),
            "strike2_sensitivity": np.zeros(n),
        }

        obj.sensitivities(
            params["time"],
            numpyToXsigma(strikes),
            *[numpyToXsigma(arr) for arr in arrays.values()],
        )

        vols = arrays["vols"]
        density = np.array(
            [
                blackScholes.density(
                    params["fwd"],
                    strike,
                    params["time"],
                    vol,
                    strike_sens,
                    strike2_sens,
                )
                for strike, vol, strike_sens, strike2_sens in zip(
                    strikes,
                    vols,
                    arrays["strike_sensitivity"],
                    arrays["strike2_sensitivity"],
                )
            ]
        )

    elif model_type == "svi":
        obj = sigmaVolatilityInspired(
            params["fwd"], params["b"], params["m"], params["sigma"]
        )
        vols = np.zeros(n)
        obj.svi(numpyToXsigma(vols), numpyToXsigma(strikes))
        density = np.exp(-0.5 * ((strikes - params["fwd"]) / vols) ** 2) / (
            vols * np.sqrt(2 * np.pi)
        )

    else:
        raise ValueError("Invalid model type. Choose 'asv' or 'svi'.")

    return strikes, vols, density


def plot_volatility_smile_and_density(
    initial_values, current_params, model_type="asv", legacy_parametrisation=False
):
    # Calculate for initial values
    initial_strikes, initial_vols, initial_density = calculate_vols_and_density(
        initial_values["fwd"], initial_values, model_type, legacy_parametrisation
    )

    # Calculate for current parameters
    current_strikes, current_vols, current_density = calculate_vols_and_density(
        initial_values["fwd"], current_params, model_type, legacy_parametrisation
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

    # Plot volatility smile
    ax1.plot(initial_strikes, initial_vols, label="Initial Volatility", linestyle="--")
    ax1.plot(current_strikes, current_vols, label="Current Volatility")
    ax1.set_xlabel("Strike")
    ax1.set_ylabel("Implied Volatility")
    ax1.set_title("Volatility Smile")
    ax1.legend()
    ax1.grid(True)

    # Plot density
    ax2.plot(initial_strikes, initial_density, label="Initial Density", linestyle="--")
    ax2.plot(current_strikes, current_density, label="Current Density")
    ax2.set_xlabel("Strike")
    ax2.set_ylabel("Density")
    ax2.set_title("Density")
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plt.show()


def create_interactive_model(
    initial_values, model_type="asv", legacy_parametrisation=False
):
    slider_layout = Layout(width="400px")
    sliders = {}

    if model_type == "asv":
        slider_specs = {
            "fwd": (0.25, 5.0, 0.01),
            "time": (0.1, 10.0, 0.001),
            "ctrl_p": (0.05, 1.0, 0.01),
            "ctrl_c": (0.05, 1.0, 0.01),
            "atm": (0.0001, 1.0, 0.0001),
            "skew": (-0.95, 0.95, 0.00001),
            "smile": (-2.0, 2.0, 0.00001),
            "put": (-2.0, 2.0, 0.00001),
            "call": (-2.0, 2.0, 0.00001),
        }
    elif model_type == "svi":
        slider_specs = {
            "fwd": (0.25, 2.5, 0.01),
            "time": (0.1, 10.0, 0.001),
            "b": (0.01, 1.0, 0.01),
            "m": (-5.0, 5.0, 0.001),
            "sigma": (-1.0, 1.0, 0.01),
        }
    else:
        raise ValueError("Invalid model type. Choose 'asv' or 'svi'.")

    for key, (min_val, max_val, step) in slider_specs.items():
        sliders[key] = FloatSlider(
            min=min_val * (initial_values[key] if key == "fwd" else 1),
            max=max_val * (initial_values[key] if key == "fwd" else 1),
            step=step,
            value=initial_values[key],
            description=f"{key.capitalize()}:",
            layout=slider_layout,
        )

    reset_button = Button(description="Reset to Initial Values")

    def on_reset_button_clicked(b):
        for key, slider in sliders.items():
            slider.value = initial_values[key]

    reset_button.on_click(on_reset_button_clicked)

    # Use a wrapper function to ensure all parameters are passed
    def update_plot(**kwargs):
        plot_volatility_smile_and_density(
            initial_values, kwargs, model_type, legacy_parametrisation
        )

    interactive_plot = interactive(update_plot, **sliders)

    # Fix: Convert generator to list before creating VBox
    slider_columns = [
        VBox([sliders[k] for k in col])
        for col in np.array_split(list(sliders.keys()), 3)
    ]
    slider_grid = HBox(slider_columns)

    return VBox([slider_grid, reset_button, interactive_plot.children[-1]])

    # Fix: Convert generator to list before creating VBox
    slider_columns = [
        VBox([sliders[k] for k in col])
        for col in np.array_split(list(sliders.keys()), 3)
    ]
    slider_grid = HBox(slider_columns)

    return VBox([slider_grid, reset_button, interactive_plot.children[-1]])
