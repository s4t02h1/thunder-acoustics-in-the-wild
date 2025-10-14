"""
thunder.distance
================

Distance estimation from lightning flash to thunder arrival time.

Formula:
    d ≈ c_air × Δt

where:
    d: distance (meters)
    c_air: speed of sound in air (m/s, temperature-dependent)
    Δt: time delay between flash and thunder (seconds)

Speed of sound:
    c_air = 331.3 + 0.606 × T (m/s, T in Celsius)
"""

import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def speed_of_sound(temperature_celsius: float) -> float:
    """
    Calculate speed of sound in air.

    Parameters
    ----------
    temperature_celsius : float
        Air temperature in Celsius

    Returns
    -------
    speed : float
        Speed of sound in m/s

    Examples
    --------
    >>> speed = speed_of_sound(20)  # 343 m/s @ 20°C
    >>> print(f"Speed of sound: {speed:.1f} m/s")
    """
    return 331.3 + 0.606 * temperature_celsius


def estimate_distance(
    time_delay: float,
    temperature_celsius: float = 20.0,
) -> float:
    """
    Estimate distance from flash-to-thunder delay.

    Parameters
    ----------
    time_delay : float
        Time between flash and thunder (seconds)
    temperature_celsius : float, default=20.0
        Air temperature (Celsius)

    Returns
    -------
    distance : float
        Estimated distance in meters

    Examples
    --------
    >>> distance = estimate_distance(3.0, temperature=20)
    >>> print(f"Distance: {distance:.0f} meters (~{distance / 1000:.1f} km)")
    """
    c_air = speed_of_sound(temperature_celsius)
    distance = c_air * time_delay

    logger.info(
        f"Distance estimation: Δt={time_delay:.2f}s, "
        f"T={temperature_celsius}°C, d={distance:.0f}m"
    )

    return distance


def estimate_distance_with_uncertainty(
    time_delay: float,
    time_delay_uncertainty: float = 0.1,
    temperature_celsius: float = 20.0,
    temperature_uncertainty: float = 5.0,
) -> Tuple[float, float, float]:
    """
    Estimate distance with uncertainty propagation.

    Parameters
    ----------
    time_delay : float
        Time between flash and thunder (seconds)
    time_delay_uncertainty : float, default=0.1
        Uncertainty in time delay (seconds)
    temperature_celsius : float, default=20.0
        Air temperature (Celsius)
    temperature_uncertainty : float, default=5.0
        Uncertainty in temperature (Celsius)

    Returns
    -------
    distance : float
        Best estimate of distance (meters)
    distance_lower : float
        Lower bound (meters)
    distance_upper : float
        Upper bound (meters)

    Examples
    --------
    >>> d, d_low, d_high = estimate_distance_with_uncertainty(3.0, 0.1, 20, 5)
    >>> print(f"Distance: {d:.0f} m (+{d_high - d:.0f}/-{d - d_low:.0f})")
    """
    # Best estimate
    distance = estimate_distance(time_delay, temperature_celsius)

    # Lower bound: shorter time, lower temperature
    c_min = speed_of_sound(temperature_celsius - temperature_uncertainty)
    distance_lower = c_min * (time_delay - time_delay_uncertainty)

    # Upper bound: longer time, higher temperature
    c_max = speed_of_sound(temperature_celsius + temperature_uncertainty)
    distance_upper = c_max * (time_delay + time_delay_uncertainty)

    logger.info(
        f"Distance with uncertainty: {distance:.0f} m "
        f"(+{distance_upper - distance:.0f}/-{distance - distance_lower:.0f})"
    )

    return distance, distance_lower, distance_upper


def estimate_distances_for_events(
    events: list,
    flash_times: Optional[list] = None,
    temperature_celsius: float = 20.0,
) -> list:
    """
    Estimate distances for multiple events.

    Parameters
    ----------
    events : list of dict
        Thunder events with 'start' times
    flash_times : list of float, optional
        Flash timestamps (seconds). If None, distances not computed.
    temperature_celsius : float, default=20.0
        Air temperature

    Returns
    -------
    events_with_distance : list of dict
        Events with added 'distance_m' and 'distance_km' fields

    Examples
    --------
    >>> flash_times = [0.5, 10.2, 25.7]
    >>> events = [{'start': 3.5}, {'start': 13.2}, {'start': 30.1}]
    >>> events = estimate_distances_for_events(events, flash_times, temperature=20)
    """
    if flash_times is None or len(flash_times) == 0:
        logger.warning("No flash times provided. Skipping distance estimation.")
        return events

    events_with_distance = []

    for event in events:
        thunder_time = event["start"]

        # Find closest preceding flash
        preceding_flashes = [f for f in flash_times if f < thunder_time]

        if preceding_flashes:
            flash_time = max(preceding_flashes)
            time_delay = thunder_time - flash_time

            distance = estimate_distance(time_delay, temperature_celsius)

            event_copy = event.copy()
            event_copy["flash_time"] = flash_time
            event_copy["time_delay"] = time_delay
            event_copy["distance_m"] = distance
            event_copy["distance_km"] = distance / 1000
            events_with_distance.append(event_copy)
        else:
            logger.warning(f"No preceding flash for event @ {thunder_time:.2f}s")
            events_with_distance.append(event)

    logger.info(f"Estimated distances for {len(events_with_distance)} events")
    return events_with_distance


def classify_strike_distance(distance_m: float) -> str:
    """
    Classify strike by distance.

    Parameters
    ----------
    distance_m : float
        Distance in meters

    Returns
    -------
    category : str
        Distance category

    Categories
    ----------
    - "very_close": < 1 km (dangerous)
    - "close": 1-5 km
    - "moderate": 5-15 km
    - "distant": > 15 km

    Examples
    --------
    >>> category = classify_strike_distance(500)
    >>> print(f"Strike category: {category}")  # "very_close"
    """
    distance_km = distance_m / 1000

    if distance_km < 1:
        return "very_close"
    elif distance_km < 5:
        return "close"
    elif distance_km < 15:
        return "moderate"
    else:
        return "distant"
