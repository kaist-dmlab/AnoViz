/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Line, Area } from '@ant-design/plots'
import moment from 'moment'
import AnomalyScoreCard from './AnomalyScoreCard';
import { ConsoleSqlOutlined } from '@ant-design/icons';

export default ({ chartData, scores, threshold, selectedVariables, minDate, maxDate, currentRange, setCheckDetail, updateChart }) => {
    const [data, setData] = React.useState([])
    const [scoreData, setScoreData] = React.useState([])
    const [thresholdScore, setThresholdScore] = React.useState(0.0)
    const [chartMin, setChartMin] = React.useState('2022-01-01 00:00:00')
    const [chartMax, setChartMax] = React.useState('2022-12-31 00:00:00')

    let tickCount = 0
    switch (currentRange) {
        case '1d':
            tickCount = 24
            break;
        case '2d':
            tickCount = 48
            break;
        case '7d':
            tickCount = 28
            break;
        case '31d':
            tickCount = 31
            break;
        case '3m':
            tickCount = 24
            break;
        default:
            break;
    }

    let labelAnnotations = []
    for (const d of chartData) {
        if (d.label === 1) {
            labelAnnotations.push({
                type: 'line',
                start: [d.date, 'min'],
                end: [d.date, 'max'],
                style: {
                    stroke: 'red',
                    strokeOpacity: 0.07
                }
            })
        }
    }

    let thresholdLine = []

    if (minDate !== 'min' && maxDate !== 'max') {
        thresholdLine = [
            {
                type: 'line',
                start: ['min', threshold],
                end: ['max', threshold],
                top: true,
                text: {
                    content: 'Anomaly Threshold',
                    position: '0%',
                    style: {
                        textAlign: 'left',
                        fill: 'red',
                        fontWeight: 700
                    },
                },
                style: {
                    stroke: 'red',
                    lineWidth: 2,
                    lineDash: [4, 4],
                },
            }
        ]
    }


    React.useEffect(() => {
        if (mainChart) {
            updateChart(mainChart)
        }
    });

    const mainConfig = {
        data: chartData,
        height: 520,
        xField: 'date',
        yField: 'value',
        seriesField: 'name',
        xAxis: {
            type: 'time',
            tickCount: tickCount,
            min: minDate,
            max: maxDate,
            mask: 'YYYY-MM-DD HH:mm',
            animate: false
        },
        localRefresh: true,
        yAxis: {
            label: {
                formatter: (v) => `${v / 1000}K`,
            },
        },
        legend: {
            position: 'bottom',
            selected: selectedVariables
        },
        smooth: true,
        annotations: labelAnnotations,
        limitInPlot: true,
        tooltip: {
            showMarkers: true,
            enterable: true,
            domStyles: {
                'g2-tooltip': {
                    width: '320px',
                    padding: '0',
                    opacity: '1'
                },
            },
            customContent: (title, items) => {
                return <AnomalyScoreCard date={title} items={items} setCheckDetail={setCheckDetail} />
            }
        },
    }

    const subConfig = {
        data: scores,
        height: 100,
        xField: 'date',
        yField: 'score',
        xAxis: {
            type: 'time',
            tickCount: tickCount,
            min: minDate,
            max: maxDate,
            mask: 'YYYY-MM-DD HH:mm',
        },
        smooth: true,
        color: '#F6AA92',
        annotations: thresholdLine,
        limitInPlot: true
    }

    let mainChart

    return <>
        {
            chartData ? <Line {...mainConfig} onReady={(chartInstance) => (mainChart = chartInstance)} /> : null
        }
        {
            scores ? <Area {...subConfig} /> : null
        }
    </>

}