/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Typography, Row, Col, Button, Statistic, Alert, Progress, Badge } from 'antd';

const { Title, Text } = Typography;

export default ({ tooltip, threshold, setAnomalyID }) => {

    let sum_scores = 0
    let is_anomaly = false
    let anomaly_id = tooltip.dataPoints[0].raw['date']
    let anomalous_precents = []
    tooltip.dataPoints.forEach(item => {
        sum_scores += item.raw.score
    })

    const avg_scores = sum_scores / tooltip.dataPoints.length

    if (avg_scores > threshold) {
        is_anomaly = true
    }

    tooltip.dataPoints.forEach(item => {
        anomalous_precents.push({ name: item.raw.name, percent: item.raw.score / sum_scores * 100, backgroundColor: item.dataset.backgroundColor })
    })
    anomalous_precents = anomalous_precents.sort((a, b) => b.percent - a.percent).slice(0, 5)

    const onHover = e => {
        document.getElementById('chartjs-tooltip').style.opacity = 1
        document.getElementById('chartjs-tooltip').style.visibility = 'visible'
    }

    const onLeave = e => {
        document.getElementById('chartjs-tooltip').remove()
    }

    const onClickDetail = () => {
        onLeave()
        setAnomalyID(anomaly_id, 12, 3)
    }

    return (
        <div id='chartjs-tooltip-details' style={{ height: 450, overflowY: 'auto' }} onMouseOver={onHover} onMouseEnter={onHover} onMouseLeave={onLeave}>
            <Alert type={is_anomaly ? "error" : 'info'} message={is_anomaly ? "Potential Anomaly!" : "Normal Data"} banner />
            <div style={{ padding: '8px 24px 24px 24px' }}>
                <Title level={4}>{tooltip.title}</Title>
                <Row>
                    <Col style={{ textAlign: 'right' }} span={24}>
                        <Statistic title={<Text strong>Anomaly Score</Text>} precision={7} value={avg_scores} valueStyle={{ color: is_anomaly ? 'red' : '#4A87E3', fontWeight: 700 }} />
                    </Col>
                </Row>
                {
                    is_anomaly
                        ?
                        <>
                            <Row gutter={[0, 16]}>
                                <Col style={{ textAlign: 'left' }} span={24}>
                                    <Text style={{ fontSize: 14 }} strong>Top-5 Contributions</Text>
                                </Col>
                                {
                                    anomalous_precents.map((item, idx) =>
                                        <Col key={idx} span={24}>
                                            <Row gutter={[4, 0]}>
                                                <Col span={12}>
                                                    <Badge key={idx} color={item.backgroundColor} text={<span><Text style={{ fontSize: 14 }} strong>{item.name}</Text></span>} />
                                                </Col>
                                                <Col span={12}><Progress steps={30} size='small' strokeWidth={16} strokeColor='red' percent={item.percent.toFixed(1)} /></Col>
                                            </Row>
                                        </Col>
                                    )
                                }
                                <Col span={24}>
                                    <Button onClick={onClickDetail} type="primary" ghost block>More Details</Button>
                                </Col>
                            </Row>
                        </>
                        :
                        <>
                            <Row gutter={[0, 16]}>
                                <Col style={{ textAlign: 'left' }} span={24}>
                                    <Text style={{ fontSize: 14 }} strong>Variable Values</Text>
                                </Col>
                                {
                                    tooltip.dataPoints.map((item, idx) =>
                                        <Col key={idx} span={24}>
                                            <Badge key={idx} color={item.dataset.backgroundColor} text={<span><Text style={{ fontSize: 16 }} strong>{item.raw.name}</Text>: <Text style={{ fontSize: 16 }}>{item.raw.value.toFixed(2)}</Text></span>} />
                                        </Col>
                                    )
                                }
                            </Row>
                        </>
                }
            </div>
        </div>
    )
}