"""Plan schema: candidate/optimized schedules produced by the optimizer.

A Plan is a list of trip assignments (which vehicle serves which trip at what
departure time) plus any extra dispatches. It is consumed by the validator,
simulator, and API.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TripAssignment(BaseModel):
    trip_id: str
    route_id: str
    vehicle_id: str
    departure_min: int


class Plan(BaseModel):
    plan_type: str                            
    assignments: list[TripAssignment]
    extra_trips: list[TripAssignment] = Field(default_factory=list)
    unassigned_trip_ids: list[str] = Field(default_factory=list)
    solver_status: str = "OK"                                       
