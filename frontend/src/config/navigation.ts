
import {
  LayoutDashboard,
  Route,
  ChartColumnIncreasing,
  type LucideIcon,
} from "lucide-react";

export type PageId =
  | "operations"
  | "recovery-planner"
  | "performance-lab";

export interface NavigationItem {
  id: PageId;
  label: string;
  icon: LucideIcon;
}

export const navigationItems: NavigationItem[] = [
  {
    id: "operations",
    label: "Operations",
    icon: LayoutDashboard,
  },
  {
    id: "recovery-planner",
    label: "Simulation Scenarios",
    icon: Route,
  },
  {
    id: "performance-lab",
    label: "Performance Lab",
    icon: ChartColumnIncreasing,
  },
];
