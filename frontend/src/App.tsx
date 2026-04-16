import { useState } from "react";
import MergeTab        from "./tabs/MergeTab";
import MaxMinTab       from "./tabs/MaxMinTab";
import AvgTab          from "./tabs/AvgTab";
import ASRTab          from "./tabs/ASRTab";
import ValidationTab   from "./tabs/ValidationTab";
import PlotTab         from "./tabs/PlotTab";
import CycleViewerTab  from "./tabs/CycleViewerTab";
import FuelSystemsTab  from "./tabs/FuelSystemsTab";

const TABS = [
  { id: "merge",        label: "TDMS → Cycles",          component: MergeTab        },
  { id: "maxmin",       label: "Max/Min",                 component: MaxMinTab       },
  { id: "avg",          label: "Averages",                component: AvgTab          },
  { id: "asr",          label: "ASR Validation",          component: ASRTab          },
  { id: "validation",   label: "Validation & QC",         component: ValidationTab   },
  { id: "plot",         label: "Data Viz",                component: PlotTab         },
  { id: "cycle-viewer", label: "Cycle Viewer",            component: CycleViewerTab  },
  { id: "fuel-systems", label: "Fuel Systems",            component: FuelSystemsTab  },
];

export default function App() {
  const [active, setActive] = useState(TABS[0].id);
  const ActiveComponent = TABS.find((t) => t.id === active)!.component;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-surface border-b border-gray-700 px-6 py-3 flex items-center gap-4">
        <span className="text-blue-400 font-bold text-lg tracking-wide">Jerry</span>
        <span className="text-gray-500 text-sm">Powertech Analysis Tools · Surrey, BC</span>
      </header>

      {/* Tab bar */}
      <nav className="bg-surface border-b border-gray-700 px-4 flex gap-1 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${
              active === t.id
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-gray-400 hover:text-gray-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Content */}
      <main className="flex-1 p-6 overflow-auto">
        <ActiveComponent />
      </main>
    </div>
  );
}
