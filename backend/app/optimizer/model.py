"""OR-Tools CP-SAT model (planned upgrade from the greedy baseline).

The greedy dispatcher in ``solve.py`` is the working baseline. This module
documents the CP-SAT formulation that will replace it once OR-Tools is added.

Decision variables (from ``Wild Bugs.md``):
- ``x_tv`` : vehicle ``v`` assigned to trip ``t`` (binary)
- ``d_t``  : departure time of trip ``t`` (integer, minutes)
- ``y_pt`` : passengers from demand group ``p`` assigned to trip ``t``

Hard constraints:
- one vehicle per trip (``sum_v x_tv == 1``)
- vehicle compatibility + availability windows
- capacity on every route segment (onboard load <= capacity)
- departure within trip window (``a_t <= d_t <= b_t``)
- no overlapping trips + turnaround for a vehicle
- transfer buffers for connections

Objective (minimize): ``w1*W + w2*U + w3*D + w4*L``
  W = waiting, U = unserved, D = distance, L = delay
"""


def build_cp_sat_model():
    """Build and return the CP-SAT model (requires ``ortools``)."""
    raise NotImplementedError("TODO(optimizer): implement CP-SAT model with ortools")
