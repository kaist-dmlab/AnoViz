/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Line } from '@ant-design/plots'

export default ({ chartData, minDate, maxDate, threshold }) => {

    let labelAnnotations = []

    if (chartData) {
        const dates = Array.from(new Set(chartData.map(d => d.date)))
        for (const date of dates) {
            let sum_scores = 0
            const dateData = chartData.filter(d => d.date === date)

            dateData.forEach(d => {
                sum_scores += d.score
            })

            if (sum_scores / dateData.length > threshold) {
                labelAnnotations.push({
                    type: 'line',
                    start: [date, 'min'],
                    end: [date, 'max'],
                    style: {
                        stroke: 'red',
                        strokeOpacity: 0.5
                    }
                })
            }
        }
    }
    const config = {
        data: chartData,
        xField: 'date',
        yField: 'value',
        seriesField: 'name',
        xAxis: {
            type: 'time',
            tickCount: 24,
            min: minDate,
            max: maxDate,
            mask: 'YYYY-MM-DD HH:mm',
            animate: false
        },
        legend: {
            layout: 'horizontal',
            position: 'bottom'
        },
        tooltip: {
            formatter: (datum) => {
                return { name: datum.name, value: datum.value.toFixed(2) };
            },
        },
        smooth: true,
        limitInPlot: true,
        annotations: labelAnnotations,
    };

    return <Line {...config} />

}