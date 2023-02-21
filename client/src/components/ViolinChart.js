/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Violin } from '@ant-design/plots';

export default ({ chartData, outlierData }) => {
    const pointStyle = {
        fill: 'red',
        stroke: 'red',
        lineWidth: 3,
    }

    let outliers = outlierData.map((outlier, idx) => {
        return {
            type: 'dataMarker',
            position: [outlier.name, outlier.value],
            point: {
                style: pointStyle
            },
            text: {
                content: outlier.value.toFixed(2),
                style: {
                    textAlign: 'start',
                    textBaseline: 'middle',
                    fill: 'red',
                },
            }
        }
    });

    const config = {
        height: 500,
        data: chartData,
        xField: 'name',
        yField: 'value',
        legend: {
            position: 'bottom',
        },
        annotations: outliers
    }

    return <>
        {chartData ? <Violin {...config} /> : null}
    </>
}