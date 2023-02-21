import React from 'react'
import { Statistic, Row, Col, Typography } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';


const { Text } = Typography

const Statistics = ({ stats }) => {
    return <Col span={16}>
        <Row gutter={[0, 32]}>
            <Col span={4}>
                {
                    stats ?
                        <>
                            <Statistic key={'total_anomaly'} title={<strong>Timestamp Anomalies</strong>} value={stats.total.n} />
                            {
                                (stats.total.percent) === 0
                                    ? <Text type="info"><MinusOutlined /> {(stats.total.percent).toFixed(2)}%</Text>
                                    : stats.total.percent > 0
                                        ? <Text type="danger"><ArrowUpOutlined /> {(stats.total.percent).toFixed(2)}%</Text>
                                        : <Text type="success"><ArrowDownOutlined /> {(stats.total.percent).toFixed(2)}%</Text>
                            }
                        </> : null
                }
            </Col>
            <Col span={4}>
                {
                    stats ?
                        <>
                            <Statistic key={'variable_total_anomalies'} title={<strong>Variable-wise Anomalies</strong>} value={stats.total.n_var} />
                            {
                                (stats.total.percent_var) === 0
                                    ? <Text type="info"><MinusOutlined /> {(stats.total.percent_var).toFixed(2)}%</Text>
                                    : stats.total.percent_var > 0
                                        ? <Text type="danger"><ArrowUpOutlined /> {(stats.total.percent_var).toFixed(2)}%</Text>
                                        : <Text type="success"><ArrowDownOutlined /> {(stats.total.percent_var).toFixed(2)}%</Text>
                            }
                        </> : null
                }
            </Col>
            {
                stats ?
                    stats.variables.map((variable, i) =>
                        <Col key={i} span={4}>
                            <Statistic key={i} title={variable.name} value={variable.n} />
                            {
                                (variable.percent) === 0
                                    ? <Text type="info"><MinusOutlined /> {(variable.percent).toFixed(2)}%</Text>
                                    : variable.percent > 0
                                        ? <Text type="danger"><ArrowUpOutlined /> {(variable.percent).toFixed(2)}%</Text>
                                        : <Text type="success"><ArrowDownOutlined /> {(variable.percent).toFixed(2)}%</Text>
                            }
                        </Col>
                    ) : null
            }
        </Row>
    </Col>
}

export default Statistics