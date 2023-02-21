/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Chart, registerables } from 'chart.js';
import { Radar } from 'react-chartjs-2';

Chart.register(...registerables);
export default ({ chartData }) => {

    let data = chartData
    let options = {}

    if (chartData) {
        data = {
            labels: chartData.map(d => d.time.slice(0, 2)),
            datasets: [
                { label: '', data: chartData.map(d => d.value) }
            ]
        }

        options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: false,
            },
            borderWidth: 4,
            pointRadius: 1,
            tension: 0.3,
            scales: {
                r: {
                    angleLines: {
                        color: 'lightgray'
                    },
                    ticks: {
                        color: 'red',
                    },
                    pointLabels: {
                        color: 'black'
                    }
                }
            }
        }
    }



    return <>
        {
            chartData ? <Radar data={data} options={options} /> : null
        }
    </>
}