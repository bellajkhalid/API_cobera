import numpy as np
import matplotlib.pyplot as plt
from ipywidgets import (
    FloatSlider,
    IntSlider,
    Button,
    ToggleButton,
    HBox,
    VBox,
    Layout,
    Output,
    Checkbox,
)
from IPython.display import display
from xsigmamodules.Util import (
    zabrMixtureAnalytics,
    zabrClassicalAnalytics,
    sabrPdeAnalyticsClassic,
    zabr_output_type,
    density_smoothing_type,
    bachelier,
)
from xsigmamodules.util.numpy_support import xsigmaToNumpy, numpyToXsigma


def get_parameter_range(param):
    ranges = {
        "expiry": (0.003, 30, 1),
        "forward": (0.0, 0.2, 0.0001),
        "alpha": (0.00001, 0.1, 0.0001),
        "beta": (0.00001, 1, 0.01),
        "beta1": (0.00001, 1, 0.01),
        "beta2": (0.00001, 5, 0.1),
        "nu": (0.00001, 2, 0.01),
        "rho": (-0.9999, 0.9999, 0.01),
        "gamma": (0.0001, 2, 0.01),
        "use_vol_adjustement": (True, False, None),
        "shift": (-0.01, 0.0, 0.0001),
        "vol_low": (0.00001, 0.01, 0.0001),
        "high_strike": (0.00001, 1, 0.01),
        "low_strike": (0.00001, 0.1, 0.001),
        "forward_cut_off": (0.000001, 0.1, 0.001),
        "smothing_factor": (0.000001, 0.1, 0.0001),
        "N": (50, 500, 1),
        "timesteps": (1, 100, 1),
        "nd": (1, 10, 1),
    }
    return ranges.get(param, (0, 1, 0.001))  # Default range if param not found


def create_sliders(initial_values):
    sliders = {}
    for param, value in initial_values.items():
        min_val, max_val, step = get_parameter_range(param)
        if isinstance(value, bool):
            sliders[param] = Checkbox(
                value=value,
                description=param.capitalize(),
                style={"description_width": "initial"},
            )
        elif isinstance(value, float):
            sliders[param] = FloatSlider(
                min=min_val,
                max=max_val,
                step=step,
                value=value,
                description=param.capitalize(),
                style={"description_width": "initial"},
            )
        elif isinstance(value, int):
            sliders[param] = IntSlider(
                min=int(min_val),
                max=int(max_val),
                step=int(step),
                value=value,
                description=param.capitalize(),
                style={"description_width": "initial"},
            )
    return sliders


def create_ui(sliders, reset_func, night_mode_func):
    reset_button = Button(
        description="Reset", layout=Layout(width="auto", height="40px")
    )
    reset_button.on_click(reset_func)

    night_mode_toggle = ToggleButton(
        value=False,
        description="Night Mode",
        layout=Layout(width="auto", height="40px"),
    )
    night_mode_toggle.observe(night_mode_func, names="value")

    slider_rows = [
        HBox(list(sliders.values())[i : i + 3]) for i in range(0, len(sliders), 3)
    ]
    return VBox(slider_rows + [HBox([reset_button, night_mode_toggle])])


def plot_volatility(
    x_initial, x_dynamic, y_initial, y_dynamic, title, is_night_mode, x_min, x_max
):
    plt.figure(figsize=(12, 6))
    style = "dark_background" if is_night_mode else "default"
    plt.style.use(style)

    plt.plot(
        x_initial,
        y_initial,
        label="Initial",
        color="cyan" if is_night_mode else "blue",
        linestyle="--",
    )
    plt.plot(
        x_dynamic,
        y_dynamic,
        label="Dynamic",
        color="yellow" if is_night_mode else "orange",
        linestyle="-",
    )

    plt.title(title, fontsize=16, color="white" if is_night_mode else "black")
    plt.xlabel("Strikes", fontsize=14, color="white" if is_night_mode else "black")
    plt.ylabel(
        "Implied Volatility", fontsize=14, color="white" if is_night_mode else "black"
    )
    plt.grid(
        True, linestyle="--", alpha=0.6, color="white" if is_night_mode else "gray"
    )
    plt.legend(fontsize=12)
    plt.xlim(x_min, x_max)
    # Filter data within x_min to x_max range
    mask = (
        (x_initial >= x_min)
        & (x_initial <= x_max)
        & (x_dynamic >= x_min)
        & (x_dynamic <= x_max)
    )
    y_initial_filtered = y_initial[mask]
    y_dynamic_filtered = y_dynamic[mask]

    # Auto-fit y-axis based on filtered data
    y_min = min(np.min(y_initial_filtered), np.min(y_dynamic_filtered))
    y_max = max(np.max(y_initial_filtered), np.max(y_dynamic_filtered))
    y_range = y_max - y_min
    plt.ylim(max(0, y_min - 0.1 * y_range), y_max + 0.1 * y_range)

    plt.show()


def create_volatility_plotter(
    model_class, initial_values, x_values, x_min, x_max, title
):
    sliders = create_sliders(initial_values)
    output = Output()
    is_night_mode = False
    current_values = initial_values.copy()

    def create_model(values):
        if model_class == zabrClassicalAnalytics:
            return model_class(
                values["expiry"],
                values["forward"],
                values["beta"],
                values["shift"],
                values["alpha"],
                values["nu"],
                values["rho"],
                values["gamma"],
                values["use_vol_adjustement"],
            )
        elif model_class == zabrMixtureAnalytics:
            high_strike = max(
                values["high_strike"], values["smothing_factor"] + values["low_strike"]
            )
            return model_class(
                values["expiry"],
                values["forward"],
                values["alpha"],
                values["beta1"],
                values["beta2"],
                values["d"],
                values["vol_low"],
                values["nu"],
                values["rho"],
                values["gamma"],
                values["use_vol_adjustement"],
                high_strike,
                values["low_strike"],
                values["forward_cut_off"],
                values["smothing_factor"],
            )
        elif model_class == sabrPdeAnalyticsClassic:
            return model_class(
                values["expiry"],
                values["forward"],
                values["alpha"],
                values["beta"],
                values["nu"],
                values["rho"],
                values["shift"],
                values["N"],
                values["timesteps"],
                values["nd"],
            )

    obj_initial = create_model(initial_values)
    x_initial = x_values
    if isinstance(obj_initial, sabrPdeAnalyticsClassic):
        x_initial = xsigmaToNumpy(obj_initial.strikes())
    y_initial = compute_density(obj_initial, x_initial)

    def update_plot(change=None):
        nonlocal is_night_mode
        with output:
            output.clear_output(wait=True)
            obj_dynamic = create_model(current_values)
            if isinstance(obj_initial, sabrPdeAnalyticsClassic):
                x_dynamic = xsigmaToNumpy(obj_dynamic.strikes())
            y_dynamic = compute_density(obj_dynamic, x_values)
            x_dynamic = x_values
            plot_volatility(
                x_initial,
                x_dynamic,
                y_initial,
                y_dynamic,
                title,
                is_night_mode,
                x_min,
                x_max,
            )

    def slider_changed(change):
        param = change["owner"].description.lower()
        current_values[param] = change["new"]
        update_plot()

    def reset_sliders(event):
        for name, slider in sliders.items():
            slider.value = initial_values[name]
        current_values.update(initial_values)
        update_plot()

    def toggle_night_mode(change):
        nonlocal is_night_mode
        is_night_mode = change["new"]
        update_plot()

    for slider in sliders.values():
        slider.observe(slider_changed, names="value")

    ui = create_ui(sliders, reset_sliders, toggle_night_mode)
    display(ui, output)
    update_plot()


def compute_density(obj, x_values):
    if isinstance(obj, sabrPdeAnalyticsClassic):
        implied_vol = vol_model = np.zeros_like(
            x_values
        )  # xsigmaToNumpy(obj.density())
        forward = obj.forward()
        T = obj.expiry()
        for i, K in enumerate(x_values):
            is_call = 1.0
            if K <= forward:
                is_call = -1.0
            p = obj.price(K, True, density_smoothing_type.LINEAR)
            p = p - max(is_call * (forward - K), 0.0)
            vol = bachelier.implied_volatility(forward, K, T, p, 1.0, is_call)
            implied_vol[i] = vol
        return implied_vol
    else:
        implied_vol = np.zeros(len(x_values))
        implied_vol_ = numpyToXsigma(implied_vol)
        strikes_ = numpyToXsigma(x_values)
        obj.values(implied_vol_, strikes_, zabr_output_type.IMPLIED_VOLATILITY, False)
        return implied_vol
