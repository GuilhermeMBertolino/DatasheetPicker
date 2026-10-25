from bisect import bisect_right


def interpolate_pixel_curve(points, pixel_x0, pixel_xf, total_points):
    if len(points) < 2:
        raise ValueError("At least two points are required for interpolation.")
    if total_points < 2:
        raise ValueError("The total number of points must be at least two.")

    sorted_points = sorted(points, key=lambda point: point.pixel_x)
    x_values = [point.pixel_x for point in sorted_points]
    generated = []

    for index in range(total_points):
        ratio = index / (total_points - 1)
        pixel_x = pixel_x0 + ratio * (pixel_xf - pixel_x0)
        pixel_y = _interpolate_y(sorted_points, x_values, pixel_x)
        generated.append((pixel_x, pixel_y))

    return generated


def _interpolate_y(points, x_values, x_value):
    if x_value <= x_values[0]:
        left = 0
        right = 1
    elif x_value >= x_values[-1]:
        left = len(points) - 2
        right = len(points) - 1
    else:
        right = bisect_right(x_values, x_value)
        left = right - 1

    x_left = points[left].pixel_x
    x_right = points[right].pixel_x
    y_left = points[left].pixel_y
    y_right = points[right].pixel_y

    if x_left == x_right:
        return y_left

    ratio = (x_value - x_left) / (x_right - x_left)
    return y_left + ratio * (y_right - y_left)
