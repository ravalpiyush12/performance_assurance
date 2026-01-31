import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, Zap, TrendingUp, Server, Database, Cpu } from 'lucide-react';

const CloudMonitoringDashboard = () => {
  const [metrics, setMetrics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [healingActions, setHealingActions] = useState([]);
  const [systemHealth, setSystemHealth] = useState(95);
  const [isRunning, setIsRunning] = useState(false);

  // Simulated workload generator
  const generateMetrics = () => {
    const timestamp = new Date().toLocaleTimeString();
    const baseLoad = 50;
    const variation = Math.random() * 30;
    const anomaly = Math.random() > 0.85 ? 40 : 0; // 15% chance of anomaly
    
    return {
      timestamp,
      cpuUsage: Math.min(100, baseLoad + variation + anomaly),
      memoryUsage: Math.min(100, 45 + Math.random() * 25 + anomaly * 0.8),
      responseTime: Math.max(50, 200 + Math.random() * 300 + anomaly * 5),
      errorRate: Math.min(15, Math.random() * 3 + anomaly * 0.3),
      requestsPerSec: Math.max(10, 100 + Math.random() * 50 - anomaly * 2)
    };
  };

  // ML-based anomaly detection (simplified isolation forest logic)
  const detectAnomaly = (currentMetrics, historicalMetrics) => {
    if (historicalMetrics.length < 5) return null;
    
    const recent = historicalMetrics.slice(-10);
    const avgCpu = recent.reduce((a, b) => a + b.cpuUsage, 0) / recent.length;
    const avgResponse = recent.reduce((a, b) => a + b.responseTime, 0) / recent.length;
    const avgError = recent.reduce((a, b) => a + b.errorRate, 0) / recent.length;
    
    const cpuDeviation = Math.abs(currentMetrics.cpuUsage - avgCpu) / avgCpu;
    const responseDeviation = Math.abs(currentMetrics.responseTime - avgResponse) / avgResponse;
    const errorDeviation = currentMetrics.errorRate > avgError * 2;
    
    if (cpuDeviation > 0.4 || responseDeviation > 0.5 || errorDeviation) {
      return {
        type: cpuDeviation > 0.4 ? 'HIGH_CPU' : responseDeviation > 0.5 ? 'HIGH_LATENCY' : 'HIGH_ERROR_RATE',
        severity: cpuDeviation > 0.6 || responseDeviation > 0.7 ? 'critical' : 'warning',
        value: currentMetrics.cpuUsage,
        metric: cpuDeviation > 0.4 ? 'CPU' : responseDeviation > 0.5 ? 'Response Time' : 'Error Rate'
      };
    }
    return null;
  };

  // Self-healing actions
  const executeHealing = (anomaly) => {
    const actions = {
      HIGH_CPU: {
        action: 'Auto-scaling',
        description: 'Scaled up 2 additional instances',
        icon: '🔄'
      },
      HIGH_LATENCY: {
        action: 'Cache Optimization',
        description: 'Enabled aggressive caching & CDN',
        icon: '⚡'
      },
      HIGH_ERROR_RATE: {
        action: 'Traffic Rerouting',
        description: 'Redirected to healthy instances',
        icon: '🔀'
      }
    };

    const healing = actions[anomaly.type];
    const newHealing = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      ...healing,
      anomalyType: anomaly.type,
      status: 'executing'
    };

    setHealingActions(prev => [newHealing, ...prev.slice(0, 4)]);
    
    // Simulate healing completion
    setTimeout(() => {
      setHealingActions(prev => 
        prev.map(h => h.id === newHealing.id ? {...h, status: 'completed'} : h)
      );
    }, 3000);

    return healing;
  };

  // Main monitoring loop
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      const newMetric = generateMetrics();
      
      setMetrics(prev => {
        const updated = [...prev, newMetric].slice(-20);
        
        // Detect anomalies
        const anomaly = detectAnomaly(newMetric, updated);
        
        if (anomaly) {
          const alert = {
            id: Date.now(),
            timestamp: new Date().toLocaleTimeString(),
            ...anomaly
          };
          
          setAlerts(prev => [alert, ...prev.slice(0, 9)]);
          executeHealing(anomaly);
          setSystemHealth(prev => Math.max(60, prev - 5));
        } else {
          setSystemHealth(prev => Math.min(98, prev + 1));
        }
        
        return updated;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isRunning]);

  const startMonitoring = () => {
    setIsRunning(true);
    setMetrics([]);
    setAlerts([]);
    setHealingActions([]);
  };

  const stopMonitoring = () => {
    setIsRunning(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            AI-Driven Self-Healing Cloud Platform
          </h1>
          <p className="text-slate-400">Real-time performance assurance with automated remediation</p>
        </div>

        {/* Control Panel */}
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-slate-600'}`}></div>
                <span className="text-sm font-medium">{isRunning ? 'Monitoring Active' : 'Monitoring Stopped'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-400" />
                <span className="text-2xl font-bold">{systemHealth}%</span>
                <span className="text-sm text-slate-400">System Health</span>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={startMonitoring}
                disabled={isRunning}
                className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
              >
                Start Monitoring
              </button>
              <button
                onClick={stopMonitoring}
                disabled={!isRunning}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
              >
                Stop
              </button>
            </div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'CPU Usage', value: metrics[metrics.length - 1]?.cpuUsage.toFixed(1) || '0', unit: '%', icon: Cpu, color: 'blue' },
            { label: 'Memory', value: metrics[metrics.length - 1]?.memoryUsage.toFixed(1) || '0', unit: '%', icon: Database, color: 'purple' },
            { label: 'Response Time', value: metrics[metrics.length - 1]?.responseTime.toFixed(0) || '0', unit: 'ms', icon: Zap, color: 'yellow' },
            { label: 'Error Rate', value: metrics[metrics.length - 1]?.errorRate.toFixed(2) || '0', unit: '%', icon: AlertTriangle, color: 'red' }
          ].map((metric, idx) => (
            <div key={idx} className="bg-slate-800 rounded-lg p-4 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400 text-sm">{metric.label}</span>
                <metric.icon className={`w-5 h-5 text-${metric.color}-400`} />
              </div>
              <div className="text-2xl font-bold">
                {metric.value}<span className="text-lg text-slate-400">{metric.unit}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              CPU & Memory Usage
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Legend />
                <Line type="monotone" dataKey="cpuUsage" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="memoryUsage" stroke="#a855f7" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-green-400" />
              Response Time & Errors
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                <Legend />
                <Area type="monotone" dataKey="responseTime" stroke="#eab308" fill="#eab30830" strokeWidth={2} />
                <Area type="monotone" dataKey="errorRate" stroke="#ef4444" fill="#ef444430" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts and Healing Actions */}
        <div className="grid grid-cols-2 gap-6">
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-400" />
              Detected Anomalies
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {alerts.length === 0 ? (
                <p className="text-slate-500 text-sm">No anomalies detected</p>
              ) : (
                alerts.map(alert => (
                  <div key={alert.id} className={`p-3 rounded-lg border ${
                    alert.severity === 'critical' ? 'bg-red-900/20 border-red-700' : 'bg-yellow-900/20 border-yellow-700'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-sm">{alert.metric} Anomaly</span>
                      <span className="text-xs text-slate-400">{alert.timestamp}</span>
                    </div>
                    <span className={`text-xs ${alert.severity === 'critical' ? 'text-red-400' : 'text-yellow-400'}`}>
                      {alert.type.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-400" />
              Self-Healing Actions
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {healingActions.length === 0 ? (
                <p className="text-slate-500 text-sm">No healing actions required</p>
              ) : (
                healingActions.map(action => (
                  <div key={action.id} className="p-3 rounded-lg bg-green-900/20 border border-green-700">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm flex items-center gap-2">
                        <span>{action.icon}</span>
                        {action.action}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        action.status === 'completed' ? 'bg-green-600' : 'bg-yellow-600 animate-pulse'
                      }`}>
                        {action.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">{action.description}</p>
                    <span className="text-xs text-slate-500">{action.timestamp}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CloudMonitoringDashboard;