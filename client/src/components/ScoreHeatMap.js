/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Heatmap } from '@ant-design/plots'

export default ({ chartData }) => {

    const config = {
        data: chartData,
        xField: 'date',
        yField: 'name',
        colorField: 'score',
        shape: 'square',
        sizeRatio: 0.8,
        reflect: 'y',
        heatmapStyle: {
            radius: 4
        },
        xAxis: {
            mask: 'YYYY-MM-DD HH:mm',
            label: {
                autoHide: false
            }
        },
        color: ['#E9E9E9', '#99E4F4', '#FFD748', '#FF7D61', '#FF3E3E']
    };

    return <Heatmap {...config} />
}