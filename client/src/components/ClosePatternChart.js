/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Line } from '@ant-design/plots'

export default ({ chartData, currentVar }) => {
    const selectClosePatternData = chartData.filter(item => item.name === currentVar)

    let labelAnnotations = []
    for (const d of selectClosePatternData) {
        if (d.label === 1) {
            labelAnnotations.push({
                type: 'line',
                start: [d.date, 'min'],
                end: [d.date, 'max'],
                style: {
                    stroke: 'red',
                    strokeOpacity: 0.5
                }
            })
        }
    }

    const config = {
        data: selectClosePatternData,
        xField: 'date',
        yField: 'value',
        seriesField: 'range',
        xAxis: {
            title: { text: 'timestamp' },
            animate: false
        },
        limitInPlot: true,
        legend: {
            layout: 'vertical',
            position: 'right'
        },
        smooth: true,
        lineStyle: ({ range }) => {
            if (range !== 'range with anomaly') {
                return {
                    lineDash: [4, 4],
                    opacity: 0.5
                }
            }
            return {
                opacity: 1
            }

        },
        color: ({ range }) => {
            if (range === 'range with anomaly') {
                return 'red'
            }
            const colorList = [
                '#FF6B3B',
                '#626681',
                '#FFC100',
                '#9FB40F',
                '#76523B',
                '#DAD5B5',
                '#0E8E89',
                '#E19348',
                '#F383A2',
                '#247FEA',
            ]

            return colorList[Math.floor(Math.random() * colorList.length)]
        },
        annotations: labelAnnotations,
    };

    return <Line {...config} />
}