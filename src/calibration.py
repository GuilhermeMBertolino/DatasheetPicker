import math


def pixel_to_data_coordinates(
    point_x,
    point_y,
    axis_positions,
    axis_values,
    x_logarithmic=False,
    y_logarithmic=False,
):
    x1_pixel, _ = axis_positions["X1"]
    x2_pixel, _ = axis_positions["X2"]
    _, y1_pixel = axis_positions["Y1"]
    _, y2_pixel = axis_positions["Y2"]

    x_ratio = _ratio(point_x, x1_pixel, x2_pixel)
    y_ratio = _ratio(point_y, y1_pixel, y2_pixel)

    return (
        _interpolate(
            axis_values["X1"],
            axis_values["X2"],
            x_ratio,
            x_logarithmic,
        ),
        _interpolate(
            axis_values["Y1"],
            axis_values["Y2"],
            y_ratio,
            y_logarithmic,
        ),
    )


def data_to_pixel_coordinates(
    value_x,
    value_y,
    axis_positions,
    axis_values,
    x_logarithmic=False,
    y_logarithmic=False,
):
    x1_pixel, _ = axis_positions["X1"]
    x2_pixel, _ = axis_positions["X2"]
    _, y1_pixel = axis_positions["Y1"]
    _, y2_pixel = axis_positions["Y2"]

    x_ratio = _inverse_interpolate(
        axis_values["X1"],
        axis_values["X2"],
        value_x,
        x_logarithmic,
    )
    y_ratio = _inverse_interpolate(
        axis_values["Y1"],
        axis_values["Y2"],
        value_y,
        y_logarithmic,
    )

    return (
        x1_pixel + x_ratio * (x2_pixel - x1_pixel),
        y1_pixel + y_ratio * (y2_pixel - y1_pixel),
    )


def _ratio(value, start, end):
    if math.isclose(start, end):
        raise ValueError("The calibration points cannot have the same pixel value.")
    return (value - start) / (end - start)


def _interpolate(start, end, ratio, logarithmic):
    if not logarithmic:
        return start + ratio * (end - start)

    if start <= 0 or end <= 0:
        raise ValueError("Logarithmic calibration values must be greater than zero")

    return math.exp(math.log(start) + ratio * (math.log(end) - math.log(start)))


def _inverse_interpolate(start, end, value, logarithmic):
    if logarithmic:
        if start <= 0 or end <= 0 or value <= 0:
            raise ValueError("Logarithmic calibration values must be greater than zero")
        return (math.log(value) - math.log(start)) / (math.log(end) - math.log(start))

    if math.isclose(start, end):
        raise ValueError("The calibration values cannot be equal.")
    return (value - start) / (end - start)
