/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import ReactDOM from 'react-dom';
import { Chart, registerables } from 'chart.js';
import { Line } from 'react-chartjs-2';
import StreamingPlugin from 'chartjs-plugin-streaming'
import autocolors from 'chartjs-plugin-autocolors';
import annotationPlugin from 'chartjs-plugin-annotation';
import 'chartjs-adapter-moment';
import AnomalyScoreCard from './AnomalyScoreCard'

Chart.register(...registerables, StreamingPlugin, autocolors, annotationPlugin);
export default ({ chartData, scores, threshold, minDate, maxDate, setAnomalyID, chartVariables }) => {
    const chartRef = React.useRef(null)
    const subRef = React.useRef(null)

    let anomalyAnnotations = {}
    if (chartData) {
        const dates = Array.from(new Set(chartData.map(d => d.date)))
        for (const date of dates) {
            let sum_scores = 0
            const dateData = chartData.filter(d => d.date === date)

            dateData.forEach(d => {
                sum_scores += d.score
            })

            if (sum_scores / dateData.length > threshold) {
                anomalyAnnotations[`anomaly_${date}`] = {
                    type: 'box',
                    xMin: date,
                    xMax: date,
                    backgroundColor: 'rgba(255, 0, 0, 0.1)',
                    borderColor: 'rgba(255, 0, 0, 0.3)',
                    borderWidth: 3,
                }
            }
        }
    }

    const mainOptions = {
        responsive: true,
        normalized: true,
        updateMode: 'quiet',
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    boxWidth: 24,
                    boxHeight: 6,
                    font: {
                        size: 16
                    }
                }
            },
            annotation: {
                annotations: anomalyAnnotations
            },
            tooltip: {
                enabled: false,
                external: function (context) {
                    let { chart, tooltip } = context
                    let tooltipEl = document.getElementById('chartjs-tooltip');

                    if (!tooltipEl) {
                        tooltipEl = document.createElement('div')
                        tooltipEl.id = 'chartjs-tooltip'
                        document.body.appendChild(tooltipEl);
                        tooltipEl.style.background = 'rgba(255, 255, 255, 0.92)';
                        tooltipEl.style.borderRadius = '3px';
                        tooltipEl.style.opacity = 1;
                        tooltipEl.style.position = 'absolute';
                        tooltipEl.style.transform = 'translate(-50%, 0)';
                        tooltipEl.style.transition = 'all .1s ease';
                        tooltipEl.style.width = '360px'
                        tooltipEl.style.maxHeight = '520px'
                        tooltipEl.style.boxShadow = 'rgb(174, 174, 174) 0px 0px 10px'
                        tooltipEl.style.zIndex = 8
                    }

                    // Hide if no tooltip
                    if (tooltip.opacity === 0) {
                        tooltipEl.style.opacity = 0;
                        return
                    } else {
                        const position = chart.canvas.getBoundingClientRect();
                        // Display, position, and set styles for font
                        tooltipEl.style.opacity = 1;
                        tooltipEl.style.left = position.left + window.pageXOffset + tooltip.caretX - 100 + 'px';
                        tooltipEl.style.top = position.top + window.pageYOffset - 50 + 'px';
                        tooltipEl.style.font = tooltip.options.bodyFont.string;
                        ReactDOM.render(<AnomalyScoreCard tooltip={tooltip} setAnomalyID={setAnomalyID} threshold={threshold} />, document.getElementById('chartjs-tooltip'))
                    }
                }
            }
        },
        parsing: {
            xAxisKey: 'date',
            yAxisKey: 'value'
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    displayFormats: {
                        hour: 'YYYY-MM-DD HH:mm'
                    },
                    unit: 'hour',
                    stepSize: 1,
                },
                min: minDate,
                max: maxDate,
                title: {
                    display: true,
                    text: 'Date'
                },
                ticks: {
                    source: 'data',
                    minRotation: 15
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Sensor Values'
                },
                ticks: {
                    // Include a dollar sign in the ticks
                    callback: function (value, index, ticks) {
                        if (value > 1) {
                            return value / 1000 + 'K';
                        } else {
                            return value.toFixed(2)
                        }
                    }
                }
            }
        },
        hoverBorderWidth: 10,
        borderWidth: 2,
        tension: 0.3,
        pointRadius: 0
    }

    let mainData = chartData
    if (chartData && chartVariables) {
        mainData = {
            datasets: chartVariables.map(varname => {
                return { label: varname, data: chartData.filter(d => d.name === varname) }
            }),
        }
    }

    let thresholdLine = {
        line1: {
            type: 'line',
            yMin: threshold,
            yMax: threshold,
            borderColor: 'rgba(255, 0, 0, 0.7)',
            borderDash: [9, 10]
        },
        label1: {
            type: 'label',
            yValue: threshold * 3,
            content: `Anomaly Threshold (${threshold.toFixed(7)})`,
            color: 'red',
            font: {
                size: 14
            },
            textAlign: 'start'
        }
    }

    const subOptions = {
        responsive: true,
        normalized: true,
        updateMode: 'quiet',
        parsing: {
            xAxisKey: 'date',
            yAxisKey: 'score'
        },
        maintainAspectRation: false,
        plugins: {
            legend: false,
            autocolors: {
                enabled: false
            },
            annotation: {
                annotations: thresholdLine
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        let label = context.dataset.label || '';

                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            label += context.parsed.y.toFixed(7);
                        }
                        return label;
                    }
                }
            }
        },
        interaction: {
            intersect: false,
            mode: 'index',
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    displayFormats: {
                        hour: 'YYYY-MM-DD HH:mm'
                    },
                    unit: 'hour',
                    stepSize: 1,
                },
                min: minDate,
                max: maxDate,
                title: {
                    display: true,
                    text: 'Date'
                },
                ticks: {
                    source: 'data',
                    minRotation: 15
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Anomaly Scores'
                },
                ticks: {
                    // Include a dollar sign in the ticks
                    callback: function (value, index, ticks) {
                        return value.toFixed(2)
                    }
                },
                max: 0.05
            }
        },
        fill: true,
        tension: 0.3,
        backgroundColor: 'rgba(0, 0, 0, 0.3)',
        borderColor: 'rgba(0, 0, 0, 0.7)',
        borderWidth: 0,
        pointRadius: 0
    }

    let subData = scores
    if (scores) {
        subData = {
            datasets: [
                { label: 'Anomaly Scores', data: scores }
            ]
        }
    }



    return <>
        {chartData ? <Line height={100} ref={chartRef} options={mainOptions} data={mainData} /> : null}
        {scores ? <Line height={30} ref={subRef} options={subOptions} data={subData} /> : null}
    </>

}