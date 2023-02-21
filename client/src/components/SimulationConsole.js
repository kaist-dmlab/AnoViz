/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { Typography, Select, Button, Row, Col, message, Progress } from 'antd'
import { onSnapshot, getDocs, query, orderBy, limit } from 'firebase/firestore'
import axios from 'axios'
import moment from 'moment'
import config from '../config'

const { Title } = Typography;

const { Option } = Select

const limitOptions = []
for (const op of [36, 36 * 2, 36 * 3, 36 * 4, 36 * 5, 36 * 6, 36 * 7, 36 * 8, 36 * 9, 36 * 10, 36 * 11, 36 * 12]) {
    limitOptions.push(<Option key={op} value={op}>{op} samples</Option>)
}

const nameOptions = []
for (const op of ['data_streams']) {
    nameOptions.push(<Option key={op} value={op}>{op}</Option>)
}

export default (props) => {
    const [simulationLimit, setSimulationLimit] = React.useState(36)
    const [collectionName, setCollectionName] = React.useState('data_streams')
    const [isRunning, setIsRunning] = React.useState(false)
    let [currentSample, setCurrentSample] = React.useState(0)

    React.useEffect(() => {
    }, [currentSample])


    const onRunSimulation = async () => {
        setIsRunning(true)

        const qMaxDate = await getDocs(query(props.dbRef, orderBy('date', 'desc'), limit(1)))
        const maxDate = moment(qMaxDate.docs[0].data().date)

        const unsubscribe = onSnapshot(props.dbRef, async (snapshot) => {
            snapshot.docChanges().forEach((change) => {
                if (change.doc.id > maxDate.format(config.DATE_FORMAT) && change.type === "added") {
                    currentSample = currentSample + 1
                    setCurrentSample(currentSample)
                }
            });
        })

        const { data } = await axios.get(`${config.SERVER_PATH}/simulator/append?collection_name=${collectionName}&limit=${simulationLimit}`)

        if (data.status === 200) {
            message.success(`Successfully appending ${simulationLimit} samples.`)
            setIsRunning(false)
            props.setIsOpenSetting(false)
            props.onChangeRange(props.currentRange)
        } else {
            message.error('Error appending data stream!');
        }

        props.setGlobalDates([props.minDate, moment(maxDate).add(simulationLimit * 10, 'minutes')])
        setCurrentSample(0)
        unsubscribe()
    }

    return (
        <React.Fragment>

            <Col span={24}>
                <Row justify="left" align="middle" gutter={[8, 8]}>
                    <Col>
                        <Title level={5}>Collection Name</Title>
                        <Select style={{ width: 256 }} onChange={value => setCollectionName(value)} value={collectionName} defaultValue={collectionName} size='large'>
                            {nameOptions}
                        </Select>
                    </Col>
                    <Col>
                        <Title level={5}>Limit</Title>
                        <Select style={{ width: 164 }} onChange={value => setSimulationLimit(value)} value={simulationLimit} defaultValue={simulationLimit} size='large'>
                            {limitOptions}
                        </Select>
                    </Col>
                    <Col>
                        <Title level={5}>Action</Title>
                        <Button type='primary' size='large' onClick={onRunSimulation} loading={isRunning}>{isRunning ? `Appending Data` : `Run Simulation`}</Button>
                    </Col>
                </Row>
                {
                    isRunning ?
                        <Row>
                            <Progress status="active" strokeColor={{ '0%': '#108ee9', '100%': '#87d068', }} percent={(currentSample / simulationLimit * 100).toFixed(2)} />
                        </Row> : null
                }
            </Col>
        </React.Fragment>
    )
}
