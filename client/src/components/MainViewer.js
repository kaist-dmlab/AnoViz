/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Card, Col, Row, Switch, Form } from 'antd'

import Charts from './StreamCharts'


export default (props) => {
    return (
        <React.Fragment>
            <Row gutter={[8, 8]} style={{ width: '100%' }}>
                <Col span={24}>
                    <Card title='Detection Results' bordered={false}
                        extra={
                            <Form layout='horizonal'>
                                <Form.Item label="Data Normalization">
                                    <Switch checkedChildren="Normalized" unCheckedChildren="Raw" defaultChecked={props.isNormalized} onChange={props.onNormalization} />
                                </Form.Item>
                            </Form>
                        }>
                        <Charts setAnomalyID={props.setAnomalyID} chartData={props.displayData}
                            scores={props.scoreData} chartVariables={props.chartVariables} threshold={props.threshold}
                            minDate={props.minDisplayDate} maxDate={props.maxDisplayDate} />
                    </Card>
                </Col>
            </Row>
        </React.Fragment >
    )
}