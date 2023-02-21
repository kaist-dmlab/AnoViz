import React from 'react'
import { Row, Col, Card } from 'antd';

import Statistics from './Statistics'
import SummaryCharts from './SummaryCharts';

const Dashboard = ({ stats, variable_chart, hourly_chart, weekly_chart }) => {
    return (
        <Col span={24}>
            <Card title="Dashboard Statistics">
                <Row justify="center" align="middle" gutter={[8, 8]}>
                    <Statistics stats={stats} />
                    <SummaryCharts variable_chart={variable_chart} hourly_chart={hourly_chart} weekly_chart={weekly_chart} />
                </Row>
            </Card>
        </Col>
    )
}

export default Dashboard