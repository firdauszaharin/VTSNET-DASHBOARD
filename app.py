import { useState } from 'react';
import { Wrench, Package, Menu, X } from 'lucide-react';
import { RealTimeClock } from './components/RealTimeClock';
import { TabButton } from './components/TabButton';
import { MaintenanceTab } from './components/MaintenanceTab';
import { EquipmentTab } from './components/EquipmentTab';
import { useDashboardData } from './hooks/useDashboardData';

type TabType = 'maintenance' | 'equipment';

export function App() {
  const [activeTab, setActiveTab] = useState<TabType>('maintenance');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { maintenanceReports, equipmentInventory, loading, error } = useDashboardData();

  return (
    <div className="min-h-screen gradient-bg">
      {/* Background decorations */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500/30 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -left-40 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-pink-500/20 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="glass-card border-0 border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              {/* Logo & Title */}
              <div className="flex items-center gap-4">
                <img src="/logo.png" alt="GreenFinder Logo" className="h-12" />
                <div>
                  <h1 className="text-xl md:text-2xl font-bold text-white">
                    GreenFinder VTMS Admin & Inventory
                  </h1>
                  <p className="text-white/60 text-sm hidden sm:block">
                    Electronic Data Management System - Going Forward
                  </p>
                </div>
              </div>

              {/* Clock & Mobile Menu */}
              <div className="flex items-center gap-4">
                <div className="hidden md:block">
                  <RealTimeClock />
                </div>
                <button
                  className="md:hidden w-10 h-10 rounded-lg glass-card flex items-center justify-center"
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                >
                  {mobileMenuOpen ? (
                    <X className="w-5 h-5 text-white" />
                  ) : (
                    <Menu className="w-5 h-5 text-white" />
                  )}
                </button>
              </div>
            </div>

            {/* Mobile Clock */}
            <div className="md:hidden mt-4">
              <RealTimeClock />
            </div>

            {/* Tabs */}
            <div className={`mt-4 ${mobileMenuOpen ? 'block' : 'hidden md:block'}`}>
              <div className="flex flex-col md:flex-row gap-2 md:gap-4">
                <TabButton
                  active={activeTab === 'maintenance'}
                  onClick={() => {
                    setActiveTab('maintenance');
                    setMobileMenuOpen(false);
                  }}
                  icon={<Wrench className="w-5 h-5" />}
                >
                  Maintenance Reports
                </TabButton>
                <TabButton
                  active={activeTab === 'equipment'}
                  onClick={() => {
                    setActiveTab('equipment');
                    setMobileMenuOpen(false);
                  }}
                  icon={<Package className="w-5 h-5" />}
                >
                  Equipment Inventory
                </TabButton>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          {loading && (
            <div className="glass-card rounded-2xl p-4 mb-6 text-white/80">
              Sync data VTSNET sedang berjalan...
            </div>
          )}
          {error && !loading && (
            <div className="glass-card rounded-2xl p-4 mb-6 text-amber-200 border border-amber-400/30">
              {error}
            </div>
          )}
          {activeTab === 'maintenance' && <MaintenanceTab maintenanceReports={maintenanceReports} />}
          {activeTab === 'equipment' && <EquipmentTab equipmentInventory={equipmentInventory} />}
        </main>

        {/* Footer */}
        <footer className="glass-card border-0 border-t border-white/10 mt-8">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <p className="text-white/60 text-sm">
                © 2025 GreenFinder VTMS Admin & Inventory Dashboard. All rights reserved.
              </p>
              <div className="flex items-center gap-4">
                <span className="text-white/40 text-xs">Version 2.0</span>
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-green-400 text-xs">Live</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
