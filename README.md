# RoutePulse

<p align="center">
  <strong>Campus Transportation Operations and Recovery Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19.2.8-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-6.0-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Vite-8.3-646CFF?style=flat-square&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-4.3-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Recharts-22C55E?style=flat-square" alt="Recharts" />
  <img src="https://img.shields.io/badge/Leaflet-199900?style=flat-square&logo=leaflet&logoColor=white" alt="Leaflet" />
  <img src="https://img.shields.io/badge/Hackathon-Wild_Bugs_2026-orange?style=flat-square" alt="Wild Bugs 2026 Hackathon" />
</p>

## Overview

RoutePulse is a campus transportation decision-support platform designed to monitor bus operations, analyze passenger demand, and generate recovery plans when disruptions affect routes, schedules, or vehicle availability.

Built for the **Wild Bugs 2026 Hackathon**, RoutePulse brings transportation monitoring, scenario-based optimization, constraint validation, simulation, and performance evaluation into one platform.

## Features

- Operations dashboard for routes, stops, buses, demand, capacity, and service alerts
- Interactive campus transportation map
- Scenario management for normal operations, demand spikes, and vehicle unavailability
- Route and schedule recovery optimization
- Vehicle assignment and trip scheduling
- Independent constraint validation
- Passenger boarding and waiting simulation
- Baseline versus optimized performance comparison
- Waiting time, unserved passenger, missed connection, and fleet utilization metrics
- ETA estimation and transportation performance visualization

## Frontend

The frontend provides the interface for monitoring transportation operations, selecting scenarios, running optimization workflows, and reviewing results.

**Technologies**
- React
- TypeScript
- Vite
- Tailwind CSS
- Axios
- Recharts
- Leaflet and React-Leaflet
- Lucide React

**Main sections**

- **Operations Dashboard:** Network overview, bus and route status, demand and capacity charts, stop inspection, and service alerts.
- **Recovery Planner:** Scenario selection, optimization progress, timetable comparison, and constraint validation results.
- **Performance Lab:** Baseline and optimized metrics, fleet utilization charts, evaluation history, and key findings.

## Backend

The Python backend uses FastAPI to expose REST APIs for transportation network data, scenario processing, optimization, validation, and evaluation.

**Technologies**
- Python
- FastAPI
- Pydantic request and response schemas
- REST APIs

**Core components**

- **Network Management:** Provides transportation network information, including routes, stops, and vehicles.
- **Scenario Management:** Supplies the scenario data and operational conditions used by the system.
- **Optimization Engine:** Generates alternative trip schedules and vehicle assignments using the implemented optimization logic.
- **Constraint Validation:** Checks proposed plans against defined operational constraints, such as vehicle availability, capacity, departure windows, and turnaround requirements.
- **Simulation Engine:** Models passenger queues, boarding, waiting, and transportation outcomes under a selected plan.
- **Evaluation Engine:** Compares baseline and optimized results using transportation performance metrics.
- **Run Management:** Retrieves optimization run results where supported by the backend implementation.

## How It Works

```text
Frontend Dashboard
        |
        v
Scenario Selection
        |
        v
API Request
        |
        v
Backend Scenario Processing
        |
        v
Optimization Engine
        |
        v
Constraint Validation
        |
        v
Baseline and Optimized Simulation
        |
        v
Performance Evaluation
        |
        v
Results Displayed in Frontend
```

## Screenshots

### Operations Dashboard

![RoutePulse Operations Dashboard](<img width="1913" height="1040" alt="Screenshot 2026-10-16 220615" src="https://github.com/user-attachments/assets/c7e48086-39d7-4b26-a81a-5df72dc33706" />)



## Tech Stack

| Area | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |
| API Client | Axios |
| Data Visualization | Recharts |
| Mapping | Leaflet, React-Leaflet, OpenStreetMap |
| Backend | Python, FastAPI |
| Data Validation | Pydantic |
| Road Geometry | OSRM |
| Version Control | Git, GitHub |

## Project Structure

```text
routepulse/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── config/
│   │   ├── data/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── services/
│   │   ├── schemas/
│   │   └── main.py
│   └── requirements.txt
│
└── README.md
```

## Getting Started

### Prerequisites

- Node.js and npm
- Python 3
- pip

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server using the actual application import path. For example, if the application is exposed as `app.main:app`:

```bash
uvicorn app.main:app --reload
```

The frontend API base URL should point to the backend server using the environment variable configured in the project.

## Project Status

RoutePulse is undergoing continued development after the Wild Bugs 2026 Hackathon. Current improvement goals include reliable backend execution, correct frontend-backend integration, and verification of optimization, simulation, and evaluation results.

The transportation network currently uses synthetic data. Live GPS integration and expanded scheduling capabilities may be explored in future iterations.

## Hackathon

Developed as a team project for the **Wild Bugs 2026 Hackathon**, focusing on campus transportation operations, disruption recovery, and route and schedule optimization.

## License

See the repository's `LICENSE` file for licensing terms.
