/**
 * Smart Greenhouse Demo - Frontend JavaScript
 */

class GreenhouseDemo {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.isConnected = false;
        this.data = {
            basic: { metrics: { timestamps: [], health_scores: [], growth_rates: [], water_usage: [], yields: [] } },
            smart: { metrics: { timestamps: [], health_scores: [], growth_rates: [], water_usage: [], yields: [] } }
        };
        
        this.initializeDemo();
    }
    
    initializeDemo() {
        this.setupEventListeners();
        this.setupWebSocket();
        this.initializeCharts();
        this.startDemo();
    }
    
    setupEventListeners() {
        // Control buttons
        document.getElementById('startBtn').addEventListener('click', () => this.startDemo());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetDemo());
        
        // Growth feedback buttons for POET system
        const feedbackButtons = ['thriving', 'healthy', 'stressed', 'wilting'];
        feedbackButtons.forEach(feedback => {
            const btn = document.getElementById(`smart${feedback.charAt(0).toUpperCase() + feedback.slice(1)}`);
            if (btn) {
                btn.addEventListener('click', () => this.sendGrowthFeedback(feedback));
            }
        });
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.setupWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'state_update') {
            this.updateSystemDisplays(data.systems);
            this.updatePOETStatus(data.poet_status);
            this.updateMetrics(data.metrics);
            this.updateCharts();
            this.updateSummaryStats();
        }
    }
    
    updateSystemDisplays(systems) {
        // Update basic greenhouse
        if (systems.basic) {
            this.updateSystemDisplay('basic', systems.basic);
        }
        
        // Update smart greenhouse
        if (systems.smart) {
            this.updateSystemDisplay('smart', systems.smart);
        }
    }
    
    updateSystemDisplay(systemId, systemData) {
        // Plant visual and info
        const plantVisual = document.getElementById(`${systemId}PlantVisual`);
        if (plantVisual) {
            plantVisual.textContent = this.getPlantEmoji(systemData.growth_stage, systemData.plant_health);
            plantVisual.className = `plant-visual ${systemData.growth_stage}`;
        }
        
        // Growth stage
        const stageElement = document.getElementById(`${systemId}GrowthStage`);
        if (stageElement) {
            stageElement.textContent = systemData.growth_stage;
        }
        
        // Plant health
        const healthElement = document.getElementById(`${systemId}PlantHealth`);
        if (healthElement) {
            healthElement.textContent = `${systemData.plant_health}%`;
            healthElement.className = `value ${this.getHealthClass(systemData.plant_health)}`;
        }
        
        // Plant size
        const sizeElement = document.getElementById(`${systemId}PlantSize`);
        if (sizeElement) {
            sizeElement.textContent = `${systemData.size}x`;
        }
        
        // Environment data
        this.updateElement(`${systemId}Temperature`, `${systemData.temperature}°F`);
        this.updateElement(`${systemId}Moisture`, `${systemData.soil_moisture}%`);
        this.updateElement(`${systemId}Light`, `${systemData.light_level}%`);
        this.updateElement(`${systemId}Humidity`, `${systemData.humidity}%`);
        
        // Metrics
        this.updateElement(`${systemId}WaterUsage`, `${(systemData.water_usage || 0).toFixed(1)} L`);
        this.updateElement(`${systemId}EnergyUsage`, `${(systemData.energy_usage || 0).toFixed(2)} kWh`);
        this.updateElement(`${systemId}Yield`, `${systemData.total_yield} kg`);
        this.updateElement(`${systemId}Stress`, `${systemData.stress_level}%`);
    }
    
    updatePOETStatus(poetStatus) {
        if (!poetStatus) return;
        
        // Algorithm
        this.updateElement('poetAlgorithm', poetStatus.learning_algorithm || 'botanical_optimization');
        
        // Metrics
        if (poetStatus.poe_metrics) {
            this.updateElement('poetExecutions', poetStatus.poe_metrics.total_executions || 0);
            this.updateElement('poetSuccessRate', `${Math.round((poetStatus.poe_metrics.success_rate || 1) * 100)}%`);
        }
        
        // Recommendations
        if (poetStatus.recommendations && poetStatus.recommendations.length > 0) {
            const recommendationsElement = document.getElementById('poetRecommendations');
            if (recommendationsElement) {
                recommendationsElement.innerHTML = poetStatus.recommendations
                    .map(rec => `<small>• ${rec}</small>`)
                    .join('<br>');
            }
        }
    }
    
    updateMetrics(metricsData) {
        if (metricsData.basic) {
            this.data.basic.metrics = metricsData.basic;
        }
        if (metricsData.smart) {
            this.data.smart.metrics = metricsData.smart;
        }
    }
    
    updateCharts() {
        // Update health chart
        if (this.charts.health) {
            this.updateChart(this.charts.health, 'health_scores', '%');
        }
        
        // Update growth chart
        if (this.charts.growth) {
            this.updateChart(this.charts.growth, 'growth_rates', 'x');
        }
        
        // Update water chart
        if (this.charts.water) {
            this.updateChart(this.charts.water, 'water_usage', 'L');
        }
        
        // Update yield chart
        if (this.charts.yield) {
            this.updateChart(this.charts.yield, 'yields', 'kg');
        }
    }
    
    updateChart(chart, dataKey, unit) {
        const basicData = this.data.basic.metrics[dataKey] || [];
        const smartData = this.data.smart.metrics[dataKey] || [];
        const timestamps = this.data.basic.metrics.timestamps || [];
        
        // Keep only recent data points for performance
        const maxPoints = 20;
        const recentLabels = timestamps.slice(-maxPoints).map((timestamp, index) => {
            const date = new Date(timestamp);
            return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        });
        
        chart.data.labels = recentLabels;
        chart.data.datasets[0].data = basicData.slice(-maxPoints);
        chart.data.datasets[1].data = smartData.slice(-maxPoints);
        
        // Update y-axis title with unit
        chart.options.scales.y.title.text = `Value (${unit})`;
        
        chart.update('none'); // No animation for performance
    }
    
    updateSummaryStats() {
        const basicMetrics = this.data.basic.metrics;
        const smartMetrics = this.data.smart.metrics;
        
        if (basicMetrics.health_scores && basicMetrics.health_scores.length > 0) {
            // Basic system stats
            const basicAvgHealth = this.average(basicMetrics.health_scores);
            const basicTotalWater = this.sum(basicMetrics.water_usage);
            const basicTotalEnergy = this.sum(basicMetrics.energy_usage);
            const basicFinalYield = basicMetrics.yields[basicMetrics.yields.length - 1] || 0;
            
            this.updateElement('basicAvgHealth', `${basicAvgHealth.toFixed(1)}%`);
            this.updateElement('basicTotalWater', `${basicTotalWater.toFixed(1)} L`);
            this.updateElement('basicTotalEnergy', `${basicTotalEnergy.toFixed(2)} kWh`);
            this.updateElement('basicFinalYield', `${basicFinalYield.toFixed(2)} kg`);
            
            // Smart system stats and comparisons
            if (smartMetrics.health_scores && smartMetrics.health_scores.length > 0) {
                const smartAvgHealth = this.average(smartMetrics.health_scores);
                const smartTotalWater = this.sum(smartMetrics.water_usage);
                const smartTotalEnergy = this.sum(smartMetrics.energy_usage);
                const smartFinalYield = smartMetrics.yields[smartMetrics.yields.length - 1] || 0;
                
                this.updateElement('smartAvgHealth', `${smartAvgHealth.toFixed(1)}%`);
                
                // Calculate improvements (avoid division by zero)
                const waterSavings = basicTotalWater > 0 ? 
                    ((basicTotalWater - smartTotalWater) / basicTotalWater * 100).toFixed(1) : '0.0';
                const energySavings = basicTotalEnergy > 0 ? 
                    ((basicTotalEnergy - smartTotalEnergy) / basicTotalEnergy * 100).toFixed(1) : '0.0';
                const yieldImprovement = basicFinalYield > 0 ? 
                    ((smartFinalYield - basicFinalYield) / basicFinalYield * 100).toFixed(1) : '0.0';
                
                this.updateElement('waterSavings', `${waterSavings}%`);
                this.updateElement('energySavings', `${energySavings}%`);
                this.updateElement('yieldImprovement', `${yieldImprovement}%`);
            }
        }
    }
    
    initializeCharts() {
        const chartConfig = {
            type: 'line',
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                elements: {
                    point: {
                        radius: 3,
                        hoverRadius: 5
                    },
                    line: {
                        borderWidth: 2
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        display: true,
                        title: {
                            display: true,
                            text: 'Value'
                        },
                        grid: {
                            display: true,
                            color: 'rgba(0,0,0,0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        };
        
        // Health chart
        this.charts.health = new Chart(document.getElementById('healthChart'), {
            ...chartConfig,
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Basic Greenhouse',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'POET Greenhouse',
                        data: [],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            }
        });
        
        // Growth chart
        this.charts.growth = new Chart(document.getElementById('growthChart'), {
            ...chartConfig,
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Basic Greenhouse',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'POET Greenhouse',
                        data: [],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            }
        });
        
        // Water usage chart
        this.charts.water = new Chart(document.getElementById('waterChart'), {
            ...chartConfig,
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Basic Greenhouse',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'POET Greenhouse',
                        data: [],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            }
        });
        
        // Yield chart
        this.charts.yield = new Chart(document.getElementById('yieldChart'), {
            ...chartConfig,
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Basic Greenhouse',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        fill: false
                    },
                    {
                        label: 'POET Greenhouse',
                        data: [],
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4,
                        fill: false
                    }
                ]
            }
        });
    }
    
    // Utility methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    getPlantEmoji(stage, health) {
        const healthLevel = health > 80 ? 'high' : health > 50 ? 'medium' : 'low';
        
        const emojis = {
            seedling: { high: '🌱', medium: '🌱', low: '🥀' },
            vegetative: { high: '🌿', medium: '🌿', low: '🍂' },
            flowering: { high: '🌸', medium: '🌼', low: '🥀' },
            fruiting: { high: '🍅', medium: '🟡', low: '🟤' }
        };
        
        return emojis[stage]?.[healthLevel] || '🌱';
    }
    
    getHealthClass(health) {
        if (health > 80) return 'high-health';
        if (health > 50) return 'medium-health';
        return 'low-health';
    }
    
    updateConnectionStatus(connected) {
        const basicStatus = document.getElementById('basicStatus');
        const smartStatus = document.getElementById('smartStatus');
        
        const color = connected ? '#059669' : '#dc2626';
        if (basicStatus) basicStatus.style.color = color;
        if (smartStatus) smartStatus.style.color = color;
    }
    
    sendGrowthFeedback(feedback) {
        if (this.ws && this.isConnected) {
            const message = {
                type: 'user_input',
                data: {
                    system_id: 'smart',
                    action: 'growth_feedback',
                    value: feedback
                }
            };
            
            this.ws.send(JSON.stringify(message));
            
            // Visual feedback
            const btn = document.getElementById(`smart${feedback.charAt(0).toUpperCase() + feedback.slice(1)}`);
            if (btn) {
                btn.classList.add('highlight');
                setTimeout(() => btn.classList.remove('highlight'), 500);
            }
        }
    }
    
    startDemo() {
        fetch('/api/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => console.log('Demo started:', data))
            .catch(error => console.error('Error starting demo:', error));
    }
    
    resetDemo() {
        fetch('/api/reset', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log('Demo reset:', data);
                // Clear charts
                Object.values(this.charts).forEach(chart => {
                    chart.data.labels = [];
                    chart.data.datasets.forEach(dataset => {
                        dataset.data = [];
                    });
                    chart.update();
                });
                
                // Clear data
                this.data.basic.metrics = { timestamps: [], health_scores: [], growth_rates: [], water_usage: [], yields: [] };
                this.data.smart.metrics = { timestamps: [], health_scores: [], growth_rates: [], water_usage: [], yields: [] };
            })
            .catch(error => console.error('Error resetting demo:', error));
    }
    
    // Statistical helper functions
    average(arr) {
        return arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
    }
    
    sum(arr) {
        return arr.reduce((a, b) => a + b, 0);
    }
}

// Initialize demo when page loads
document.addEventListener('DOMContentLoaded', () => {
    new GreenhouseDemo();
}); 