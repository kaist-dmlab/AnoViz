/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { PageHeader, Divider, Radio, Form, Badge, Spin, Select, Space, DatePicker, Tag, Tooltip } from 'antd';
import { CalendarOutlined, DatabaseTwoTone } from '@ant-design/icons';
import moment from 'moment'

import MainViewer from './MainViewer'
import Dashboard from './Dashboard'

const { Option } = Select;
const { RangePicker } = DatePicker;


export default (props) => {
    const modes = [{ label: 'QUERY', value: 'query' }, { label: 'STREAM', value: 'stream' }]

    const onRangeChange = value => {
        if (value !== props.currentRange) {
            props.setCurrentRange(value)
        }
    }

    return (
        <React.Fragment>
            <PageHeader title="Anomaly Detection" style={{ paddingBottom: 0 }}
                subTitle={
                    <Tooltip placement="bottom" title='connected database name'>
                        <Tag color='blue' icon={<DatabaseTwoTone />}>prediction_results</Tag>
                    </Tooltip>
                }
                tags={
                    <Badge status={props.status === 'arriving' ? "processing" : props.status === 'online' ? 'success' : 'default'}
                        text={props.status === 'arriving' ? "New prediction results are arriving..." : props.status === 'online' ? 'Stream On' : 'Stream Off'} />
                }
                extra={
                    <Space direction='horizontal' size={16}>
                        <Form layout='vertical'>
                            <Form.Item label="Data Retrieval Mode">
                                <Radio.Group options={modes} buttonStyle='solid' onChange={props.setMode} value={props.mode} optionType="button" />
                            </Form.Item>
                        </Form>
                        <Form layout='vertical'>
                            <Form.Item label="Data Display Range">
                                <RangePicker format="YYYY-MM-DD HH:mm" minuteStep={10} onChange={onRangeChange} value={[moment(props.minDisplayDate), moment(props.maxDisplayDate)]} showTime disabled={props.mode === 'stream'} />
                                <Select value={props.currentRange} defaultValue={props.currentRange} style={{ width: 172, fontWeight: 'bold', marginLeft: 8 }} onChange={onRangeChange}>
                                    <Option value={6}><CalendarOutlined /> Last 6 Hours</Option>
                                    <Option value={12}><CalendarOutlined /> Last 12 Hours</Option>
                                    <Option value={24}><CalendarOutlined /> Last 24 Hours</Option>
                                    <Option value={24 * 3}><CalendarOutlined /> Last 3 Days</Option>
                                    <Option value={24 * 7}><CalendarOutlined /> Last 7 Days</Option>
                                    {
                                        ![6, 12, 24, 24 * 3, 24 * 7].includes(props.currentRange) ? <Option value={props.currentRange} disabled><CalendarOutlined /> Custom Range</Option> : <></>
                                    }
                                </Select>
                            </Form.Item>
                        </Form>
                    </Space>
                } />
            <Spin tip='Calculating Prediction Statistics' spinning={props.isStatLoad} size='large'>
                <Dashboard stats={props.stats} variable_chart={props.variable_chart} hourly_chart={props.hourly_chart} weekly_chart={props.weekly_chart} />
            </Spin>
            <Divider />
            <Spin tip='Loading Prediction Results' spinning={props.isChartLoad} size='large'>
                <MainViewer initDates={props.initDates} firebase={props.firebase} displayData={props.displayData} chartData={props.chartData} chartLabels={props.chartLabels} maxDisplayDate={props.maxDisplayDate}
                    scoreData={props.scoreData} chartVariables={props.chartVariables} threshold={props.threshold} setAnomalyID={props.setAnomalyID} minDisplayDate={props.minDisplayDate}
                    setStats={props.setStats} setVarChart={props.setVarChart} setHourlyChart={props.setHourlyChart} setWeeklyChart={props.setWeeklyChart} setMinDisplayDate={props.setMinDisplayDate}
                    currentRange={props.currentRange} setCurrentRange={props.setCurrentRange} setMaxDisplayDate={props.setMaxDisplayDate} setInitDates={props.setInitDates}
                    setChartData={props.setChartData} setScoreChart={props.setScoreChart} mode={props.mode} onNormalization={props.onNormalization}
                />
            </Spin>
        </React.Fragment>
    )
}
