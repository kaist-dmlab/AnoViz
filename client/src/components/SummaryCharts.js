import React from 'react'
import { Typography, Row, Col } from 'antd';

import VariableChart from './VariableChart';
import TimeCharts from './TimeCharts';

const { Text } = Typography

const SummaryCharts = ({ variable_chart, hourly_chart, weekly_chart }) => {
    return (
        <Col span={8}>
            <Row justify="left" align="middle">
                <Col span={24} style={{ maxHeight: 128 }}>
                    <VariableChart chartData={variable_chart} />
                </Col>
                <Col span={12} style={{ textAlign: 'center', maxHeight: 128 }}>
                    <Text strong>Hourly Information</Text>
                    <TimeCharts chartData={hourly_chart} />
                </Col>
                <Col span={12} style={{ textAlign: 'center', maxHeight: 128 }}>
                    <Text strong>Weekly Information</Text>
                    <TimeCharts chartData={weekly_chart} />
                </Col>
            </Row>
        </Col>
    )
}

export default SummaryCharts