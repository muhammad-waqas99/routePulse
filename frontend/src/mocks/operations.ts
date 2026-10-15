import type { OperationsData } from "../types/operations";

export const operationsMockData: OperationsData = {
  routes: [
    {
      id: "R1",
      name: "Route 1 – North & North-East",
      stopIds: ["S02", "S03", "S04", "S01"],
      status: "active",
    },
    {
      id: "R2",
      name: "Route 2 – East & South-East",
      stopIds: ["S05", "S06", "S07", "S08", "S01"],
      status: "delayed",
    },
    {
      id: "R3",
      name: "Route 3 – South",
      stopIds: ["S09", "S10", "S11", "S01"],
      status: "active",
    },
    {
      id: "R4",
      name: "Route 4 – West & North-West",
      stopIds: ["S12", "S13", "S14", "S15", "S01"],
      status: "active",
    },
  ],

  stops: [
    { id: "S01", name: "IIMB Main Gate, Bannerghatta Road", latitude: 12.8952, longitude: 77.5994 },


    { id: "S02", name: "Silk Board Junction", latitude: 12.9172, longitude: 77.6228 },
    { id: "S03", name: "BTM Layout 2nd Stage", latitude: 12.9166, longitude: 77.6101 },
    { id: "S04", name: "Jayadeva Hospital Junction", latitude: 12.9177, longitude: 77.5993 },

 
    { id: "S05", name: "Hongasandra Main Road", latitude: 12.8885, longitude: 77.6290 },
    { id: "S06", name: "Begur Lake Road", latitude: 12.8730, longitude: 77.6230 },
    { id: "S07", name: "Hulimavu Junction", latitude: 12.8790, longitude: 77.6090 },
    { id: "S08", name: "Arekere Lake Road Junction", latitude: 12.8870, longitude: 77.6050 },


    { id: "S09", name: "Gottigere, Bannerghatta Road", latitude: 12.8617, longitude: 77.5904 },
    { id: "S10", name: "Meenakshi Mall Junction", latitude: 12.8765, longitude: 77.5963 },
    { id: "S11", name: "Arekere Gate Junction", latitude: 12.8890, longitude: 77.5985 },


    { id: "S12", name: "Jayanagar 4th Block", latitude: 12.9250, longitude: 77.5838 },
    { id: "S13", name: "JP Nagar 2nd Phase", latitude: 12.9085, longitude: 77.5850 },
    { id: "S14", name: "JP Nagar 7th Phase", latitude: 12.8890, longitude: 77.5650 },
    { id: "S15", name: "Konanakunte Cross Metro Area", latitude: 12.8903, longitude: 77.5798 },
  ],
  vehicles: [
    { id: "BUS01", capacity: 40, status: "available" },
    { id: "BUS02", capacity: 40, status: "in-service", routeId: "R1", currentStopId: "S02" },
    { id: "BUS03", capacity: 30, status: "in-service", routeId: "R2", currentStopId: "S05" },
    { id: "BUS04", capacity: 30, status: "unavailable" },
    { id: "BUS05", capacity: 30, status: "in-service", routeId: "R3", currentStopId: "S09" },
    { id: "BUS06", capacity: 40, status: "in-service", routeId: "R4", currentStopId: "S12" },
  ],

  trips: [
    { id: "T001", routeId: "R1", vehicleId: "BUS02", departureTime: "08:00", status: "scheduled" },
    { id: "T002", routeId: "R2", vehicleId: "BUS03", departureTime: "08:15", status: "scheduled" },
    { id: "T003", routeId: "R3", vehicleId: "BUS05", departureTime: "08:30", status: "scheduled" },
    { id: "T004", routeId: "R4", vehicleId: "BUS06", departureTime: "08:45", status: "scheduled" },
  ],

  demand: [
    { stopId: "S01", time: "08:00", passengerCount: 32 },
    { stopId: "S02", time: "08:00", passengerCount: 24 },
    { stopId: "S03", time: "08:00", passengerCount: 15 },
    { stopId: "S04", time: "08:00", passengerCount: 28 },
    { stopId: "S05", time: "08:15", passengerCount: 18 },
    { stopId: "S06", time: "08:15", passengerCount: 12 },
    { stopId: "S07", time: "08:15", passengerCount: 14 },
    { stopId: "S08", time: "08:15", passengerCount: 20 },
    { stopId: "S09", time: "08:30", passengerCount: 10 },
    { stopId: "S10", time: "08:30", passengerCount: 22 },
    { stopId: "S11", time: "08:30", passengerCount: 16 },
    { stopId: "S12", time: "08:45", passengerCount: 19 },
    { stopId: "S13", time: "08:45", passengerCount: 25 },
    { stopId: "S14", time: "08:45", passengerCount: 11 },
    { stopId: "S15", time: "08:45", passengerCount: 17 },
  ],

  etas: [
    
    { tripId: "T001", stopId: "S02", scheduledArrival: "08:05", estimatedArrival: "08:07" },
    { tripId: "T001", stopId: "S03", scheduledArrival: "08:13", estimatedArrival: "08:15" },
    { tripId: "T001", stopId: "S04", scheduledArrival: "08:20", estimatedArrival: "08:22" },
    { tripId: "T001", stopId: "S01", scheduledArrival: "08:30", estimatedArrival: "08:32" },

  
    { tripId: "T002", stopId: "S05", scheduledArrival: "08:20", estimatedArrival: "08:26" },
    { tripId: "T002", stopId: "S06", scheduledArrival: "08:28", estimatedArrival: "08:35" },
    { tripId: "T002", stopId: "S07", scheduledArrival: "08:35", estimatedArrival: "08:42" },
    { tripId: "T002", stopId: "S08", scheduledArrival: "08:41", estimatedArrival: "08:48" },
    { tripId: "T002", stopId: "S01", scheduledArrival: "08:50", estimatedArrival: "08:57" },

    { tripId: "T003", stopId: "S09", scheduledArrival: "08:35", estimatedArrival: "08:35" },
    { tripId: "T003", stopId: "S10", scheduledArrival: "08:42", estimatedArrival: "08:42" },
    { tripId: "T003", stopId: "S11", scheduledArrival: "08:48", estimatedArrival: "08:48" },
    { tripId: "T003", stopId: "S01", scheduledArrival: "08:55", estimatedArrival: "08:55" },

    
    { tripId: "T004", stopId: "S12", scheduledArrival: "08:50", estimatedArrival: "08:50" },
    { tripId: "T004", stopId: "S13", scheduledArrival: "08:57", estimatedArrival: "08:57" },
    { tripId: "T004", stopId: "S14", scheduledArrival: "09:04", estimatedArrival: "09:05" },
    { tripId: "T004", stopId: "S15", scheduledArrival: "09:10", estimatedArrival: "09:11" },
    { tripId: "T004", stopId: "S01", scheduledArrival: "09:18", estimatedArrival: "09:18" },
  ],
  alerts: [
    {
      id: "A001",
      title: "Route 2 delay",
      description: "The trip is running behind its scheduled arrival.",
      severity: "warning",
      status: "active",
      routeId: "R2",
    },
  ],
};