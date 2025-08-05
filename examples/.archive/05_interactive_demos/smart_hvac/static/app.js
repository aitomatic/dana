/**
 * Smart HVAC Demo - Frontend JavaScript
 * 
 * Handles real-time WebSocket communication and chart visualization
 * for side-by-side HVAC system comparison.
 */

class HVACDemo {
    constructor() {
        this.ws = null;
        this.charts = {};
        this.connected = false;
        this.basicAdjustments = 0;
        
        // Chart data
        this.chartData = {
            basic: {
                temperatures: [],
                energy: [],
                comfort: [],
                timestamps: []
            },
            smart: {
                temperatures: [],
                energy: [],
                comfort: [],
                timestamps: []
            }
        };
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeCharts();
        this.connectWebSocket();
    }
    
    initializeElements() {
        // Buttons
        this.startBtn = document.getElementById('startBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.weatherSelect = document.getElementById('weatherSelect');
        
        // Basic system controls
        this.basicTempInput = document.getElementById('basicTempInput');
        this.basicTempDown = document.getElementById('basicTempDown');
        this.basicTempUp = document.getElementById('basicTempUp');
        this.basicSetTemp = document.getElementById('basicSetTemp');
        
        // Smart system controls
        this.smartTooCold = document.getElementById('smartTooCold');
        this.smartComfortable = document.getElementById('smartComfortable');
        this.smartTooHot = document.getElementById('smartTooHot');
        
        // Status elements
        this.basicStatus = document.getElementById('basicStatus');
        this.smartStatus = document.getElementById('smartStatus');
    }
    
    setupEventListeners() {
        // Control buttons
        this.startBtn.addEventListener('click', () => this.startDemo());
        this.resetBtn.addEventListener('click', () => this.resetDemo());
        
        // Basic system controls
        this.basicTempDown.addEventListener('click', () => {
            const current = parseFloat(this.basicTempInput.value);
            this.basicTempInput.value = Math.max(60, current - 0.5);
        });
        
        this.basicTempUp.addEventListener('click', () => {
            const current = parseFloat(this.basicTempInput.value);
            this.basicTempInput.value = Math.min(85, current + 0.5);
        });
        
        this.basicSetTemp.addEventListener('click', () => {
            const temp = parseFloat(this.basicTempInput.value);
            this.setBasicTemperature(temp);
        });
        
        // Smart system comfort controls
        this.smartTooCold.addEventListener('click', () => {
            this.sendComfortFeedback('too_cold');
            this.animateButton(this.smartTooCold);
        });
        
        this.smartComfortable.addEventListener('click', () => {
            this.sendComfortFeedback('comfortable');
            this.animateButton(this.smartComfortable);
        });
        
        this.smartTooHot.addEventListener('click', () => {
            this.sendComfortFeedback('too_hot');
            this.animateButton(this.smartTooHot);
        });
        
        // Weather control
        this.weatherSelect.addEventListener('change', () => {
            this.setWeather(this.weatherSelect.value);
        });
    }
    
    initializeCharts() {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    display: false
                },
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        padding: 15
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.3
                },
                point: {
                    radius: 2
                }
            }
        };
        
        // Temperature Chart
        this.charts.temperature = new Chart(
            document.getElementById('temperatureChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Basic HVAC',
                            data: [],
                            borderColor: '#7c3aed',
                            backgroundColor: 'rgba(124, 58, 237, 0.1)',
                            borderWidth: 2
                        },
                        {
                            label: 'POET HVAC',
                            data: [],
                            borderColor: '#059669',
                            backgroundColor: 'rgba(5, 150, 105, 0.1)',
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    ...chartOptions,
                    scales: {
                        ...chartOptions.scales,
                        y: {
                            beginAtZero: false,
                            min: 65,
                            max: 80,
                            title: {
                                display: true,
                                text: 'Temperature (°F)'
                            }
                        }
                    }
                }
            }
        );
        
        // Energy Chart
        this.charts.energy = new Chart(
            document.getElementById('energyChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Basic HVAC',
                            data: [],
                            borderColor: '#7c3aed',
                            backgroundColor: 'rgba(124, 58, 237, 0.1)',
                            borderWidth: 2
                        },
                        {
                            label: 'POET HVAC',
                            data: [],
                            borderColor: '#059669',
                            backgroundColor: 'rgba(5, 150, 105, 0.1)',
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    ...chartOptions,
                    scales: {
                        ...chartOptions.scales,
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Power (kW)'
                            }
                        }
                    }
                }
            }
        );
        
        // Comfort Chart
        this.charts.comfort = new Chart(
            document.getElementById('comfortChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Basic HVAC',
                            data: [],
                            borderColor: '#7c3aed',
                            backgroundColor: 'rgba(124, 58, 237, 0.1)',
                            borderWidth: 2
                        },
                        {
                            label: 'POET HVAC',
                            data: [],
                            borderColor: '#059669',
                            backgroundColor: 'rgba(5, 150, 105, 0.1)',
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    ...chartOptions,
                    scales: {
                        ...chartOptions.scales,
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Comfort Score'
                            }
                        }
                    }
                }
            }
        );
        
        // Cumulative Energy Chart
        this.charts.cumulative = new Chart(
            document.getElementById('cumulativeChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Basic HVAC',
                            data: [],
                            borderColor: '#7c3aed',
                            backgroundColor: 'rgba(124, 58, 237, 0.1)',
                            borderWidth: 2,
                            fill: true
                        },
                        {
                            label: 'POET HVAC',
                            data: [],
                            borderColor: '#059669',
                            backgroundColor: 'rgba(5, 150, 105, 0.1)',
                            borderWidth: 2,
                            fill: true
                        }
                    ]
                },
                options: {
                    ...chartOptions,
                    scales: {
                        ...chartOptions.scales,
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Energy (kWh)'
                            }
                        }
                    }
                }
            }
        );
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.connected = true;
            this.updateConnectionStatus();
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this.updateConnectionStatus();
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.connected = false;
            this.updateConnectionStatus();
        };
    }
    
    handleWebSocketMessage(data) {
        if (data.type === 'state_update') {
            this.updateSystemStates(data.systems);
            this.updateCharts(data.metrics);
            this.updatePOETStatus(data.poet_status);
            this.updateSummaryStats();
        }
    }
    
    updateSystemStates(systems) {
        // Update basic system
        const basic = systems.basic;
        if (basic) {
            document.getElementById('basicCurrentTemp').textContent = `${basic.current_temp}°F`;
            document.getElementById('basicTargetTemp').textContent = `${basic.target_temp}°F`;
            document.getElementById('basicOutsideTemp').textContent = `${basic.outside_temp}°F`;
            document.getElementById('basicMode').textContent = basic.mode;
            document.getElementById('basicHeating').textContent = `${basic.heating_output.toFixed(0)}%`;
            document.getElementById('basicCooling').textContent = `${basic.cooling_output.toFixed(0)}%`;
            document.getElementById('basicFan').textContent = `${basic.fan_speed.toFixed(0)}%`;
            document.getElementById('basicEnergyRate').textContent = `${basic.energy_usage.toFixed(1)} kW`;
            document.getElementById('basicTotalEnergy').textContent = `${basic.total_energy.toFixed(3)} kWh`;
            document.getElementById('basicComfort').textContent = basic.comfort_score;
        }
        
        // Update smart system
        const smart = systems.smart;
        if (smart) {
            document.getElementById('smartCurrentTemp').textContent = `${smart.current_temp}°F`;
            document.getElementById('smartTargetTemp').textContent = `${smart.target_temp}°F`;
            document.getElementById('smartOutsideTemp').textContent = `${smart.outside_temp}°F`;
            document.getElementById('smartMode').textContent = smart.mode;
            document.getElementById('smartHeating').textContent = `${smart.heating_output.toFixed(0)}%`;
            document.getElementById('smartCooling').textContent = `${smart.cooling_output.toFixed(0)}%`;
            document.getElementById('smartFan').textContent = `${smart.fan_speed.toFixed(0)}%`;
            document.getElementById('smartEnergyRate').textContent = `${smart.energy_usage.toFixed(1)} kW`;
            document.getElementById('smartTotalEnergy').textContent = `${smart.total_energy.toFixed(3)} kWh`;
            document.getElementById('smartComfort').textContent = smart.comfort_score;
        }
    }
    
    updateCharts(metrics) {
        const maxPoints = 20;
        
        // Update chart data
        ['basic', 'smart'].forEach(system => {
            const data = metrics[system];
            if (!data || !data.timestamps) return;
            
            // Store data
            this.chartData[system].temperatures = data.temperatures.slice(-maxPoints);
            this.chartData[system].energy = data.energy_usage.slice(-maxPoints);
            this.chartData[system].comfort = data.comfort_scores.slice(-maxPoints);
            this.chartData[system].timestamps = data.timestamps.slice(-maxPoints);
        });
        
        // Update temperature chart
        const tempLabels = this.chartData.basic.timestamps.map(t => 
            new Date(t).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
        );
        
        this.charts.temperature.data.labels = tempLabels;
        this.charts.temperature.data.datasets[0].data = this.chartData.basic.temperatures;
        this.charts.temperature.data.datasets[1].data = this.chartData.smart.temperatures;
        this.charts.temperature.update('none');
        
        // Update energy chart
        this.charts.energy.data.labels = tempLabels;
        this.charts.energy.data.datasets[0].data = this.chartData.basic.energy;
        this.charts.energy.data.datasets[1].data = this.chartData.smart.energy;
        this.charts.energy.update('none');
        
        // Update comfort chart
        this.charts.comfort.data.labels = tempLabels;
        this.charts.comfort.data.datasets[0].data = this.chartData.basic.comfort;
        this.charts.comfort.data.datasets[1].data = this.chartData.smart.comfort;
        this.charts.comfort.update('none');
        
        // Update cumulative energy chart
        const basicCumulative = this.calculateCumulative(this.chartData.basic.energy);
        const smartCumulative = this.calculateCumulative(this.chartData.smart.energy);
        
        this.charts.cumulative.data.labels = tempLabels;
        this.charts.cumulative.data.datasets[0].data = basicCumulative;
        this.charts.cumulative.data.datasets[1].data = smartCumulative;
        this.charts.cumulative.update('none');
    }
    
    updatePOETStatus(poetStatus) {
        if (!poetStatus) return;
        
        document.getElementById('poetAlgorithm').textContent = 
            poetStatus.learning_algorithm || 'statistical';
        
        if (poetStatus.poe_metrics) {
            document.getElementById('poetExecutions').textContent = 
                poetStatus.poe_metrics.total_executions || 0;
            
            const successRate = (poetStatus.poe_metrics.success_rate || 1) * 100;
            document.getElementById('poetSuccessRate').textContent = 
                `${successRate.toFixed(1)}%`;
        }
        
        // Update recommendations
        const recommendations = document.getElementById('poetRecommendations');
        if (poetStatus.recommendations && poetStatus.recommendations.length > 0) {
            recommendations.innerHTML = poetStatus.recommendations
                .slice(0, 2)
                .map(rec => `<small>• ${rec}</small>`)
                .join('<br>');
        }
    }
    
    updateSummaryStats() {
        // Calculate averages
        const basicAvgComfort = this.calculateAverage(this.chartData.basic.comfort);
        const smartAvgComfort = this.calculateAverage(this.chartData.smart.comfort);
        
        const basicTotalEnergy = this.calculateSum(this.chartData.basic.energy);
        const smartTotalEnergy = this.calculateSum(this.chartData.smart.energy);
        
        // Update basic summary
        document.getElementById('basicAvgComfort').textContent = 
            basicAvgComfort ? basicAvgComfort.toFixed(1) : '--';
        document.getElementById('basicSummaryEnergy').textContent = 
            basicTotalEnergy ? `${basicTotalEnergy.toFixed(3)} kWh` : '--';
        document.getElementById('basicAdjustments').textContent = this.basicAdjustments;
        
        // Update smart summary
        document.getElementById('smartAvgComfort').textContent = 
            smartAvgComfort ? smartAvgComfort.toFixed(1) : '--';
        document.getElementById('smartSummaryEnergy').textContent = 
            smartTotalEnergy ? `${smartTotalEnergy.toFixed(3)} kWh` : '--';
        
        // Calculate energy savings
        if (basicTotalEnergy && smartTotalEnergy && basicTotalEnergy > 0) {
            const savings = ((basicTotalEnergy - smartTotalEnergy) / basicTotalEnergy) * 100;
            document.getElementById('energySavings').textContent = 
                `${savings.toFixed(1)}%`;
        } else {
            document.getElementById('energySavings').textContent = '--';
        }
    }
    
    calculateCumulative(array) {
        const cumulative = [];
        let sum = 0;
        for (const value of array) {
            sum += value || 0;
            cumulative.push(sum);
        }
        return cumulative;
    }
    
    calculateAverage(array) {
        if (!array || array.length === 0) return null;
        const sum = array.reduce((a, b) => a + (b || 0), 0);
        return sum / array.length;
    }
    
    calculateSum(array) {
        if (!array || array.length === 0) return null;
        return array.reduce((a, b) => a + (b || 0), 0);
    }
    
    updateConnectionStatus() {
        const color = this.connected ? '#059669' : '#dc2626';
        this.basicStatus.style.color = color;
        this.smartStatus.style.color = color;
    }
    
    // Control Methods
    startDemo() {
        fetch('/api/start', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log('Demo started:', data);
                this.startBtn.textContent = 'Running...';
                this.startBtn.disabled = true;
            })
            .catch(error => console.error('Error starting demo:', error));
    }
    
    resetDemo() {
        fetch('/api/reset', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log('Demo reset:', data);
                this.basicAdjustments = 0;
                
                // Clear charts
                Object.values(this.charts).forEach(chart => {
                    chart.data.labels = [];
                    chart.data.datasets.forEach(dataset => {
                        dataset.data = [];
                    });
                    chart.update();
                });
                
                // Reset chart data
                this.chartData = {
                    basic: {
                        temperatures: [],
                        energy: [],
                        comfort: [],
                        timestamps: []
                    },
                    smart: {
                        temperatures: [],
                        energy: [],
                        comfort: [],
                        timestamps: []
                    }
                };
                
                this.startBtn.textContent = 'Start Demo';
                this.startBtn.disabled = false;
            })
            .catch(error => console.error('Error resetting demo:', error));
    }
    
    setBasicTemperature(temp) {
        const message = {
            type: 'user_input',
            data: {
                system_id: 'basic',
                action: 'set_temp',
                value: temp
            }
        };
        
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(message));
            this.basicAdjustments++;
            this.animateButton(this.basicSetTemp);
        }
    }
    
    sendComfortFeedback(feedback) {
        const message = {
            type: 'user_input',
            data: {
                system_id: 'smart',
                action: feedback
            }
        };
        
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify(message));
        }
    }
    
    setWeather(pattern) {
        // This would send weather change to backend
        console.log('Weather changed to:', pattern);
    }
    
    animateButton(button) {
        button.classList.add('highlight');
        setTimeout(() => {
            button.classList.remove('highlight');
        }, 500);
    }
}

// Initialize the demo when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HVACDemo();
});