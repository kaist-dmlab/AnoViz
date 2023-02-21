/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Area } from '@ant-design/plots'

export default ({ chartData, minDate, maxDate, currentRange, threshold }) => {
    const data = chartData

    const config = {
        data,
        height: 100,
        xField: 'date',
        yField: 'score',
        xAxis: {
            type: 'time',
            tickCount: currentRange,
            min: minDate,
            max: maxDate,
            mask: 'YYYY-MM-DD HH:mm',
        },
        yAxis: {
            max: threshold * 3
        },
        color: '#F6AA92',
        smooth: true,
        annotations: [
            {
                type: 'line',
                start: ['min', threshold],
                end: ['max', threshold],
                style: {
                    lineDash: [4, 4],
                    stroke: 'red'
                }
            }
        ],
        limitInPlot: true,
    };

    return <Area {...config} />
}