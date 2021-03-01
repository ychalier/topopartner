function createElevationProfile(ctx, data) {
    Chart.defaults.global.defaultFontFamily = 'Lato';
    var myChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: "Elevation",
                data: data,
                showLine: true,
                backgroundColor: 'rgba(76, 175, 80, .1)',
                borderColor: 'rgba(76, 175, 80, .8)',
                pointBackgroundColor: 'rgba(76, 175, 80, .01)',
                pointBorderColor: 'rgba(76, 175, 80, .3)',
                pointHoverRadius: 10,
                pointRadius: 8,
            }]
        },
        options: {
            layout: {
                padding: {
                    bottom: -10,
                    left: -10,
                }
            },
            legend: {
                display: false,
            },
            scales: {
                yAxes: [{
                    ticks: {
                        display: false,
                        stepSize: 50,
                    },
                    gridLines: {
                        color: 'rgba(255, 255, 255, .1)',
                    }
                }],
                xAxes: [{
                    type: 'linear',
                    ticks: {
                        display: false,
                        max: data.length > 0 ? data[data.length - 1].x : 0,
                        stepSize: 1000,
                        callback: function(value, index, values) {
                            return (Math.round(.001 * value * 100) / 100);
                        }
                    },
                    gridLines: {
                        color: 'rgba(255, 255, 255, .1)',
                    }
                }],
            },
            tooltips: {
                mode: 'label',
                callbacks: {
                    label: function(tooltipItem, data) {
                        let distance = Math.round(tooltipItem.xLabel * .01) / 10;
                        let elevation = Math.round(tooltipItem.yLabel);
                        trackWrapper.highlighter.setLatLng(trackWrapper.leaflet._latlngs[tooltipItem.index]);
                        let string = elevation + "m at " + distance + "km";
                        if (tooltipItem.index + 1 < data.datasets[tooltipItem.datasetIndex].data.length) {
                            let currentPoint = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
                            let nextPoint = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index + 1];
                            let slope = Math.round(100 * (nextPoint.y - currentPoint.y) / (nextPoint.x - currentPoint.x));
                            string += " (" + slope + "%)";
                        }
                        return string;
                    }
                }
            }
        }
    });

}