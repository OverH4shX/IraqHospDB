

document.addEventListener('DOMContentLoaded', function() {
 
    if (Chart) {
        Chart.defaults.color = '#e2e2e2';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        Chart.defaults.plugins.legend.labels.color = '#e2e2e2';
        Chart.defaults.plugins.title.color = '#ffffff';
        
       
        Chart.defaults.plugins.tooltip.rtl = true;
        Chart.defaults.plugins.title.rtl = true;
    }
    
   
    const chartColors = {
        primary: '#0d6efd',
        success: '#198754',
        info: '#0dcaf0',
        warning: '#ffc107',
        danger: '#dc3545',
        secondary: '#6c757d',
        light: '#f8f9fa',
        dark: '#212529',
   
        colors: [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
            '#9966FF', '#FF9F40', '#8AC54B', '#EA526F',
            '#23BFAA', '#8075FF', '#FFD166', '#06D6A0'
        ]
    };
    

    window.createAgeDistributionChart = function(elementId, data) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'عدد المرضى',
                    data: data.data,
                    backgroundColor: chartColors.primary,
                    borderColor: chartColors.primary,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'عدد المرضى'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'الفئة العمرية'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'توزيع أعمار المرضى'
                    }
                }
            }
        });
    };
    
    
    window.createMonthlyRegistrationsChart = function(elementId, data) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'المرضى الجدد',
                    data: data.data,
                    fill: false,
                    borderColor: chartColors.success,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'عدد المرضى الجدد'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'الشهر'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'التسجيلات الشهرية'
                    }
                }
            }
        });
    };
    
 
    window.createChronicDiseasesChart = function(elementId, data) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return;
        
        new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'عدد المرضى',
                    data: data.data,
                    backgroundColor: data.data.map((_, index) => chartColors.colors[index % chartColors.colors.length]),
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'عدد المرضى'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'الأمراض المزمنة الشائعة'
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    };
});
