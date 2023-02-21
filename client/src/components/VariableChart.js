/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Chart, registerables } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import autocolors from 'chartjs-plugin-autocolors';

Chart.register(...registerables, autocolors);
export default ({ chartData }) => {

    let data = chartData
    let options = {}

    if (chartData) {
        data = {
            labels: chartData.map(d => d.name),
            datasets: [
                { label: '', data: chartData.map(d => d.value) }
            ]
        }

        options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    title: {
                        display: true,
                        text: 'Variables'
                    },
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12
                    }
                },
                autocolors: {
                    mode: 'data'
                }
            },
        }
    }


    return <>
        {
            chartData ? <Doughnut data={data} options={options} /> : null
        }
    </>
}