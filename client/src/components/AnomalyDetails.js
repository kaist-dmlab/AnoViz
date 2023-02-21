/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import moment from 'moment'
import { Row, PageHeader, Radio, Col, Card, Space, Typography, Spin, Switch, Form, Tooltip, Tag } from 'antd';
import * as dfd from 'danfojs'

import ClosePatternChart from './ClosePatternChart'
import PastClosePattern from './PastClosePattern';
import ViolinChart from './ViolinChart';
import ScoreHeatMap from './ScoreHeatMap';
import RawScoreChart from './RawScoreChart';

const { Text, Title } = Typography

// for a selected anomaly --> additionally select pre 7 records + post 7 records --> 15 records in total hourly? 30 for daily?
export default ({ onNormalization, scaler, isLoadDetail, isLoadVariableChart, anomalyID, pastChartData, displayData, chartData, closePatternData, chartVariables, outliers, currentRange, heatMapData, selectCloseVar, setSelectCloseVar, threshold }) => {

    const currentMaxDate = moment(anomalyID).add(Math.ceil((currentRange - 1) / 2) * 10, 'minutes')
    const currentMinDate = moment(anomalyID).subtract(Math.floor((currentRange - 1) / 2) * 10, 'minutes')
    const pastMaxDate = moment(Math.max.apply(Math, pastChartData.map(o => new Date(o.date))))
    const pastMinDate = moment(Math.min.apply(Math, pastChartData.map(o => new Date(o.date))))

    const [isNormalized, setIsNormalized] = React.useState(false)
    let [displayOutliers, setDisplayOutliers] = React.useState(outliers)
    let [displayPastPatterns, setDisplayPastPatterns] = React.useState(pastChartData)
    let [displayCurrentPatterns, setDisplayCurrentPatterns] = React.useState(displayData)

    const pastScaler = new dfd.MinMaxScaler()

    const onChange = e => {
        setSelectCloseVar(e.target.value, 3);
    };

    const normalizateData = data => {
        const normalizedData = JSON.parse(JSON.stringify(data)).map(d => {
            chartVariables.map((var_name, var_idx) => {
                if (d.name === var_name) {
                    d.value = scaler.transform([d.value])[var_idx]
                }
                return null
            })
            return d
        })
        return normalizedData
    }

    const onNormalizeOutliers = value => {
        setIsNormalized(value)
        onNormalization(value)
        if (value) {
            const normalizedOutliers = normalizateData(outliers)
            setDisplayOutliers(normalizedOutliers)
        } else {
            setDisplayOutliers(outliers)
        }
    }

    const onNormalizePastClosePatters = value => {
        setIsNormalized(value)
        onNormalization(value)
        if (value) {
            const dates = new Set(pastChartData.map(d => d.date))
            const datasets = Array.from(dates).map(date => {
                return pastChartData.filter(d => d.date === date).map(dd => dd.value)
            })

            const df = new dfd.DataFrame(datasets, { columns: chartVariables })
            pastScaler.fit(df)


            const normalizedPastChartData = JSON.parse(JSON.stringify(pastChartData)).map(d => {
                chartVariables.map((var_name, var_idx) => {
                    if (d.name === var_name) {
                        d.value = pastScaler.transform([d.value])[var_idx]
                    }
                    return null
                })
                return d
            })

            const normalizedCurrentPatterns = normalizateData(chartData)
            setDisplayPastPatterns(normalizedPastChartData)
            setDisplayCurrentPatterns(normalizedCurrentPatterns)
        } else {
            setDisplayPastPatterns(pastChartData)
            setDisplayCurrentPatterns(chartData)
        }
    }

    return (
        <Spin tip='Aggregating and Loading Anomaly Details' spinning={isLoadDetail} size='large'>
            <PageHeader title="Anomaly Details"
                subTitle={
                    <Tooltip placement="bottom" title='detected reference point'>
                        <Tag color='blue'>{anomalyID}</Tag>
                    </Tooltip>
                } />
            <Row gutter={[8, 32]}>
                <Col span={3}>
                    <Card title="Select Variable" bordered={false} className='var-card'>
                        <Radio.Group onChange={onChange} value={selectCloseVar}>
                            <Space direction="vertical">
                                {
                                    chartVariables.map((item, i) =>
                                        <Radio value={item} key={i}>{item}</Radio>
                                    )
                                }
                            </Space>
                        </Radio.Group>
                    </Card>
                </Col>
                <Col span={21}>
                    <Spin tip='Loading Close Pattern Chart Data' spinning={isLoadVariableChart}>
                        <Card title={`Close Patterns of "${selectCloseVar}"`} bordered={false}>
                            <ClosePatternChart chartData={closePatternData} chartVariables={chartVariables} currentVar={selectCloseVar} threshold={threshold} />
                        </Card>
                    </Spin>
                </Col>
                <Col span={24}>
                    <Card title='Close Patterns in the Past' bordered={false} extra={
                        <Form layout='horizonal'>
                            <Form.Item label="Data Normalization">
                                <Switch checkedChildren="Normalized" unCheckedChildren="Raw" defaultChecked={isNormalized} onChange={value => onNormalizePastClosePatters(value)} />
                            </Form.Item>
                        </Form>
                    }>
                        <Row gutter={[64, 0]}>
                            <Col span={12}>
                                <PastClosePattern chartData={displayPastPatterns} chartVariables={chartVariables} minDate={pastMinDate} maxDate={pastMaxDate.subtract(10, 'minutes')} threshold={threshold} />
                                <Title style={{ textAlign: 'center' }} level={3}>Past Patterns</Title>
                            </Col>
                            <Col span={12} >
                                <PastClosePattern chartData={displayCurrentPatterns} chartVariables={chartVariables} minDate={currentMinDate} maxDate={currentMaxDate} threshold={threshold} />
                                <Title style={{ textAlign: 'center' }} level={3}>Current Patterns</Title>
                            </Col>
                        </Row>
                    </Card>
                </Col>
                <Col span={24}>
                    <Card title='Possible Anomalies in Data Distributions' bordered={false} extra={
                        <Form layout='horizonal'>
                            <Form.Item label="Data Normalization">
                                <Switch checkedChildren="Normalized" unCheckedChildren="Raw" defaultChecked={isNormalized} onChange={value => onNormalizeOutliers(value)} />
                            </Form.Item>
                        </Form>
                    }>
                        <ViolinChart chartData={displayData} outlierData={displayOutliers} chartVariables={chartVariables} />
                    </Card>
                </Col>
                <Col span={24}>
                    <Card title='Heatmap' bordered={false}>
                        <ScoreHeatMap chartData={heatMapData} chartVariables={chartVariables} />
                    </Card>
                </Col>
                <Col span={24}>
                    <Card title='Raw Scores' bordered={false}>
                        {
                            chartVariables.map((item, i) =>
                                <Row justify='center' align='middle' key={i} gutter={[16, 0]} style={{ marginBottom: 8 }}>
                                    <Col span={2} style={{ textAlign: 'center' }}>
                                        <Text strong>{item}</Text>
                                    </Col>
                                    <Col span={22}>
                                        <RawScoreChart threshold={threshold} chartData={chartData.filter(data => data.name === item)} minDate={currentMinDate} maxDate={currentMaxDate} currentRange={currentRange} />
                                    </Col>
                                </Row>
                            )
                        }
                    </Card>
                </Col>
            </Row>
        </Spin>
    )
}
