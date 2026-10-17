
export interface Route {
  id: string;
  name: string;
  stopIds: string[];
  status: "active" | "delayed" | "disrupted" | "inactive";
  segmentTravelMin?: number[];
  segmentDistanceKm?: number[];
}

export interface Stop {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
}

export interface Vehicle {
  id: string;
  capacity: number;
  status: "available" | "in-service" | "unavailable";
  currentStopId?: string;
  routeId?: string;
}

export interface Trip {
  id: string;
  routeId: string;
  vehicleId: string;
  departureTime: string;
  status: "scheduled" | "in-progress" | "completed" | "cancelled";
}

export interface DemandRecord {
  stopId: string;
  time: string;
  passengerCount: number;
}

export interface EtaRecord {
  tripId: string;
  stopId: string;
  scheduledArrival: string;
  estimatedArrival: string;
}

export interface TransportAlert {
  id: string;
  title: string;
  description: string;
  severity: "info" | "warning" | "critical";
  status: "active" | "resolved";
  routeId?: string;
  vehicleId?: string;
}

export interface OperationsData {
  routes: Route[];
  stops: Stop[];
  vehicles: Vehicle[];
  trips: Trip[];
  demand: DemandRecord[];
  etas: EtaRecord[];
  alerts: TransportAlert[];
  dataSource?: string;
  notes?: string[];
}
