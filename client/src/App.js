import React from 'react'
import { Layout, Spin, Button, Modal, Space, Alert, Tabs, message } from 'antd'
import { QuestionCircleTwoTone, SettingTwoTone, GithubFilled } from '@ant-design/icons'
import { collection, getFirestore, onSnapshot, getDocs, query, where, orderBy, limit } from 'firebase/firestore'

import AnomalyDetection from './components/AnomalyDetection'
import AnomalyDetails from './components/AnomalyDetails'
import SimulationConsole from './components/SimulationConsole'
import axios from 'axios'
import moment from 'moment'
import * as dfd from 'danfojs'

import config from './config'
import './App.css';

const { Header, Content, Footer } = Layout;

function App({ firebase }) {
  const db = getFirestore(firebase)
  const predictionResults = collection(db, 'prediction_results')
  const scaler = new dfd.MinMaxScaler()

  const [chartVariables, setChartVariables] = React.useState([])
  const [chartData, setChartData] = React.useState([]);
  const [displayData, setDisplayData] = React.useState([])
  const [scoreChart, setScoreChart] = React.useState([]);
  const [closePatternData, setClosePatternData] = React.useState(null)
  const [pastClosePatterns, setPastClosePatterns] = React.useState(null)
  const [scoreHeatmap, setScoreHeatmap] = React.useState(null)
  const [outliers, setOutliers] = React.useState(null)
  const [varChart, setVarChart] = React.useState(null)
  const [hourlyChart, setHourlyChart] = React.useState(null)
  const [weeklyChart, setWeeklyChart] = React.useState(null)
  const [initDates, setInitDates] = React.useState([])
  const [globalDates, setGlobalDates] = React.useState([])

  const [stats, setStats] = React.useState(null)
  const [anomalyID, setAnomalyID] = React.useState(null)
  const [isFetch, setIsFetch] = React.useState(false)
  const [threshold, setThreshold] = React.useState(0)
  const [selectCloseVar, setSelectCloseVar] = React.useState([])
  const [currentRange, setCurrentRange] = React.useState(6);
  const [minDisplayDate, setMinDisplayDate] = React.useState(moment().format(config.DATE_FORMAT))
  const [maxDisplayDate, setMaxDisplayDate] = React.useState(moment().format(config.DATE_FORMAT))
  const [mode, setMode] = React.useState('query')
  const [status, setStatus] = React.useState('offline')
  const [listener, setListener] = React.useState(null)
  const [isStatLoad, setIsStatLoad] = React.useState(true)
  const [isChartLoad, setIsChartLoad] = React.useState(true)
  const [isLoadVariableChart, setIsLoadVariableChart] = React.useState(true)
  const [isLoadDetail, setIsLoadDetail] = React.useState(false)
  const [isNormalized, setIsNormalized] = React.useState(false)
  const [errorMessage, setErrorMessage] = React.useState('')
  const [isOpenSetting, setIsOpenSetting] = React.useState(false)
  const [isOpenLink, setIsOpenLink] = React.useState(false)

  const updateDashboard = async (length, minDate, maxDate) => {
    setIsStatLoad(true)

    const { data: statData } = await axios.get(`${config.SERVER_PATH}/api/stats?length=${length}&minDate=${minDate}&maxDate=${maxDate}`)
    const { data: hourlyData } = await axios.get(`${config.SERVER_PATH}/api/hourly_chart?length=${length}&minDate=${minDate}&maxDate=${maxDate}`)
    const { data: weeklyData } = await axios.get(`${config.SERVER_PATH}/api/weekly_chart?length=${length}&minDate=${minDate}&maxDate=${maxDate}`)

    const varData = statData.data.variables.map(item => { return { name: item.name, value: item.n } })

    setVarChart(varData)
    setStats(statData.data)
    setHourlyChart(hourlyData.data)
    setWeeklyChart(weeklyData.data)
    setIsStatLoad(false)
  }

  const initialFetch = async () => {
    try {
      // fetch data from firebase and api server
      setIsFetch(true)
      setIsChartLoad(true)

      const { data: initData } = await axios.get(`${config.SERVER_PATH}/init`)
      const { threshold, var_names } = initData.data
      setThreshold(threshold)
      setChartVariables(var_names)
      setSelectCloseVar(var_names[0])

      const qMaxDate = await getDocs(query(predictionResults, orderBy('date', 'desc'), limit(1)))

      if (qMaxDate.docs[0]) {
        const maxDate = moment(qMaxDate.docs[0].data().date)
        const minDate = moment(maxDate).subtract(currentRange, 'hours')

        const data = []
        const scoreData = []
        const q = query(predictionResults, where('date', ">=", minDate.format('YYYY-MM-DD HH:mm:ss')), where('date', '<=', maxDate.format('YYYY-MM-DD HH:mm:ss')))
        const qDocs = await getDocs(q)
        qDocs.forEach(doc => {
          const docData = doc.data()
          for (const name of var_names) {
            data.push({
              date: docData.date,
              name: name,
              value: docData[name],
              score: docData[`score_${name}`],
              label: docData[`label_${name}`]
            })
          }
          scoreData.push({ date: docData.date, score: docData.score })
        })

        setChartData(data)
        setDisplayData(data)
        setScoreChart(scoreData)
        setMinDisplayDate(minDate.format(config.DATE_FORMAT))
        setMaxDisplayDate(maxDate.format(config.DATE_FORMAT))
        setGlobalDates([minDate, maxDate])
        setIsChartLoad(false)

        const length = Number(maxDate.diff(minDate, 'minutes') / 10) // divide by interval of 10 minutes for samsung data sets
        await updateDashboard(length, minDate.format('YYYY-MM-DD HH:mm:ss'), maxDate.format('YYYY-MM-DD HH:mm:ss'))
      } else {
        setIsChartLoad(false)
        await updateDashboard(1, moment().format('YYYY-MM-DD HH:mm:ss'), moment().format('YYYY-MM-DD HH:mm:ss'))
      }
    } catch (error) {
      setErrorMessage(error.message)
      setIsOpenLink(true)
      message.error(error.message);
    }
  }

  const onNormalization = value => {
    setIsNormalized(value)
    if (value) {
      const dates = new Set(chartData.map(d => d.date))
      const datasets = Array.from(dates).map(date => {
        return chartData.filter(d => d.date === date).map(dd => dd.value)
      })

      const df = new dfd.DataFrame(datasets, { columns: chartVariables })
      scaler.fit(df)

      const tempData = JSON.parse(JSON.stringify(chartData)) // nested JSON parsing for deep copying

      const normalizedData = tempData.map(d => {
        chartVariables.map((var_name, var_idx) => {
          if (d.name === var_name) {
            d.value = scaler.transform([d.value])[var_idx]
          }
          return null
        })
        return d
      })

      setDisplayData(normalizedData)
    } else {
      setDisplayData(chartData)
    }
  }


  const fetchDataByRange = async (minDate, maxDate) => {
    // fetch by min display and global max dates
    const data = []
    const scoreData = []
    const q = query(predictionResults, where('date', ">=", minDate.format('YYYY-MM-DD HH:mm:ss')), where('date', '<=', maxDate.format('YYYY-MM-DD HH:mm:ss')))
    const qDocs = await getDocs(q)
    qDocs.forEach(doc => {
      const docData = doc.data()
      for (const name of chartVariables) {
        data.push({
          date: docData.date,
          name: name,
          value: docData[name],
          score: docData[`score_${name}`],
          label: docData[`label_${name}`]
        })
      }
      scoreData.push({ date: docData.date, score: docData.score })
    })

    setChartData(data)
    setDisplayData(data)

    setScoreChart(scoreData)
  }

  const loadByQuery = async value => {
    setIsChartLoad(true)

    let maxDate = globalDates[1]
    let minDate = globalDates[0]
    if (typeof (value) === 'number') { // last n hours

      minDate = moment(maxDate).subtract(value, 'hours')
      if (minDate < globalDates[0]) {
        await fetchDataByRange(minDate, maxDate)
        setGlobalDates([minDate, maxDate]) // update only minDate (min-lower case)
      }

    } else { // selected range

      maxDate = value[1]
      minDate = value[0]

      if (minDate < globalDates[0] && maxDate > globalDates[1]) {
        await fetchDataByRange(minDate, maxDate)
        setGlobalDates([minDate, maxDate])
      } else if (minDate < globalDates[0]) {
        await fetchDataByRange(minDate, globalDates[1])
        setGlobalDates([minDate, globalDates[1]])
      } else if (maxDate > globalDates[1]) {
        await fetchDataByRange(globalDates[0], maxDate)
        setGlobalDates([globalDates[0], maxDate])
      }
    }

    setMinDisplayDate(minDate.format(config.DATE_FORMAT))
    setMaxDisplayDate(maxDate.format(config.DATE_FORMAT))
    setCurrentRange(maxDate.diff(minDate, 'hours'))
    setIsChartLoad(false)

    const length = Number(globalDates[1].diff(minDate, 'minutes') / 10) // divide by interval of 10 minutes
    await updateDashboard(length, minDate.format('YYYY-MM-DD HH:mm:ss'), maxDate.format('YYYY-MM-DD HH:mm:ss'))
  }

  const loadByStream = async value => {
    setIsChartLoad(true)
    let maxDate = globalDates[1]
    let minDate = globalDates[0]

    minDate = moment(maxDate).subtract(value, 'hours')
    if (minDate < globalDates[0]) {
      await fetchDataByRange(minDate, maxDate)
      setGlobalDates([minDate, maxDate]) // update only minDate (min-lower case)
    }

    setMinDisplayDate(minDate.format(config.DATE_FORMAT))
    setMaxDisplayDate(maxDate.format(config.DATE_FORMAT))
    setCurrentRange(value)
    setIsChartLoad(false)

    localStorage.setItem('currentRange', value)

    const length = Number(globalDates[1].diff(minDate, 'minutes') / 10) // divide by interval of 10 minutes
    await updateDashboard(length, minDate.format('YYYY-MM-DD HH:mm:ss'), maxDate.format('YYYY-MM-DD HH:mm:ss'))
  }

  const onChangeRange = async value => {
    if (mode === 'query') {
      await loadByQuery(value)
    } else {
      await loadByStream(value)
    }
  }

  const onClickDetail = async (anomaly_timestamp, interval, count) => {
    stopListenting()
    setIsLoadDetail(true)
    setIsNormalized(false)

    const anomaly = chartData.filter(d => d.date === anomaly_timestamp).sort((a, b) => b.score - a.score)

    setIsLoadVariableChart(true)

    const closePatternQuery = `variable_name=${anomaly[0].name}&anomaly_timestamp=${anomaly_timestamp}&interval=${currentRange}&count=${count}`
    const pastPatternQuery = `anomaly_timestamp=${anomaly_timestamp}&interval=${currentRange}`
    const outlierQuery = `anomaly_timestamp=${anomaly_timestamp}&interval=${currentRange}`
    const heatmapQuery = `anomaly_timestamp=${anomaly_timestamp}&interval=${currentRange}`

    const { data: close_pattern_data } = await axios.get(`${config.SERVER_PATH}/api/close_pattern_chart?${closePatternQuery}`)
    const { data: past_close_patterns } = await axios.get(`${config.SERVER_PATH}/api/past_close_patterns?${pastPatternQuery}`)
    const { data: possible_outliers } = await axios.get(`${config.SERVER_PATH}/api/possible_outliers?${outlierQuery}`)
    const { data: heatmap } = await axios.get(`${config.SERVER_PATH}/api/score_heatmap?${heatmapQuery}`)

    setScoreHeatmap(heatmap.data)
    setOutliers(possible_outliers.data)
    setClosePatternData(close_pattern_data.data)
    setPastClosePatterns(past_close_patterns.data)
    setSelectCloseVar(anomaly[0].name)
    setIsLoadDetail(false)
    setIsLoadVariableChart(false)
    setAnomalyID(anomaly_timestamp)
  }

  const onChangeCurrentVariable = async (value, count) => {
    setIsLoadVariableChart(true)
    const closePatternQuery = `variable_name=${value}&anomaly_timestamp=${anomalyID}&interval=${currentRange}&count=${count}`
    const { data: close_pattern_data } = await axios.get(`${config.SERVER_PATH}/api/close_pattern_chart?${closePatternQuery}`)
    setSelectCloseVar(value)
    setClosePatternData(close_pattern_data.data)
    setIsLoadVariableChart(false)
  }

  const onModeChange = async value => {
    setMode(value)
    if (value === 'stream') {
      await startListening(globalDates[0], globalDates[1])
    } else {
      stopListenting()
      loadByQuery(currentRange)
    }
  }

  const startListening = async (minDate, maxDate) => {
    localStorage.setItem('currentRange', currentRange)

    const data = chartData
    const scoreData = scoreChart

    const unsubscribe = onSnapshot(predictionResults, async (snapshot) => {
      setStatus('online')
      snapshot.docChanges().forEach((change) => {
        if (change.doc.id > globalDates[1].format('YYYY-MM-DD HH:mm:ss') && change.type === "added") {
          setStatus('arriving')
          const docData = change.doc.data()
          for (const name of chartVariables) {
            data.push({
              date: docData.date,
              name: name,
              value: docData[name],
              score: docData[`score_${name}`],
              label: docData[`label_${name}`]
            })
          }
          scoreData.push({ date: docData.date, score: docData.score })

          maxDate = moment(docData.date)
          minDate = moment(maxDate).subtract(localStorage.getItem('currentRange'), 'hours')
        }

      });

      setChartData(data)
      setDisplayData(data)

      setScoreChart(scoreData)

      setMinDisplayDate(minDate.format(config.DATE_FORMAT))
      setMaxDisplayDate(maxDate.format(config.DATE_FORMAT))
      setGlobalDates([globalDates[0], maxDate])
      setStatus('online')
    })

    const length = Number(maxDate.diff(minDate, 'minutes') / 10) // divide by interval of 10 minutes
    await updateDashboard(length, minDate.format('YYYY-MM-DD HH:mm:ss'), maxDate.format('YYYY-MM-DD HH:mm:ss'))

    setListener(() => unsubscribe)
    return () => {
      unsubscribe()
    };
  }

  const stopListenting = () => {
    if (listener) {
      listener()
      localStorage.removeItem('currentRange')
    }
    setStatus('offline')
  }


  const onCancelSetting = () => {
    setIsOpenSetting(false)
    setIsOpenLink(false)
  }

  React.useEffect(() => {
    if (!isFetch) {
      initialFetch().then(() => {
        setIsFetch(true)
      })
    }
  }, [status]);

  return (
    <Layout className="layout">
      <Header style={{ "backgroundColor": "white" }}>
        <Space size='middle'>
          <a href="/" className='menu-url'><div className='logo' />AnoViz</a><span> A Visual Inspection Tool of Anomalies in Multivariate Time Series</span>
          {!anomalyID ? <><Button onClick={() => setIsOpenLink(true)} icon={<QuestionCircleTwoTone />} /><Button onClick={() => setIsOpenSetting(true)} icon={<SettingTwoTone />} /></> : null}
          {<Button icon={<GithubFilled />} href='https://github.com/kaist-dmlab/AnoViz' target='blank'/>}
        </Space>
        <span style={{float: 'right'}}>Supported by <div className='samsung-logo' /></span>
      </Header>

      <Modal title="Stream Simulator Console" open={isOpenSetting} onCancel={onCancelSetting} width={800} footer={null}>
        {
          globalDates.length === 2 ?
            <SimulationConsole minDate={globalDates[0]} maxDate={globalDates[1].format(config.DATE_FORMAT)} setGlobalDates={setGlobalDates} currentRange={currentRange}
              dbRef={collection(db, 'data_streams')} setIsOpenSetting={setIsOpenSetting} onChangeRange={onChangeRange} />
            : null
        }
      </Modal>

      <Modal title='Welcome to AnoViz!' width={720} open={isOpenLink} cancelText='Close' onCancel={onCancelSetting} footer={null}>
        {
          errorMessage ? <Alert message={<span>A <strong style={{ color: 'red' }}>{errorMessage}</strong> occurred while connecting to the server!</span>} type="error" showIcon /> : null
        }
        <p />
        <p><strong>Please kindly refer to the following materials about the AnoViz project.</strong></p>
        <Tabs items={[
          {
            label: 'AAAI-23 Paper', key: 'paper', children: <div>
              <object type="application/pdf" data="files/AnoViz_AAAI23_Paper.pdf#toolbar=0" width="100%" height="480"> </object>
              <Button type="primary" block target='blank' href='files/AnoViz_AAAI23_Paper.pdf'>Download Paper PDF</Button>
            </div>
          },
          {
            label: 'AAAI-23 Poster', key: 'poster', children: <div>
              <object type="application/pdf" data="files/AnoViz_AAAI23_Poster.pdf#toolbar=0" width="100%" height="480"> </object>
              <Button type="primary" block target='blank' href='files/AnoViz_AAAI23_Poster.pdf'>Download Poster PDF</Button>
            </div>
          },
          {
            label: 'Demonstration Video', key: 'video', children: <div style={{ textAlign: 'center' }}>
              <iframe width="100%" height="480" src="https://www.youtube.com/embed/fOHZO3xiMAA" title="[AAAI-23] AnoViz Demonstration Video" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen></iframe>
            </div>
          }
        ]} />
      </Modal>

      <Content style={{ padding: '0 50px' }}>
        <br />
        <div className="site-layout-content">
          {
            !anomalyID ?
              <Spin tip='Aggregating and Loading Anomaly Details' spinning={isLoadDetail} size='large'>
                <AnomalyDetection firebase={firebase} initDates={initDates} currentRange={currentRange} isNormalized={isNormalized}
                  stats={stats} threshold={threshold} displayData={displayData} chartData={chartData} scoreData={scoreChart} chartVariables={chartVariables}
                  variable_chart={varChart} hourly_chart={hourlyChart} weekly_chart={weeklyChart} minDisplayDate={minDisplayDate} maxDisplayDate={maxDisplayDate}
                  setAnomalyID={onClickDetail} setStats={setStats} setVarChart={setVarChart} setHourlyChart={setHourlyChart} setMinDisplayDate={setMinDisplayDate}
                  setWeeklyChart={setWeeklyChart} setCurrentRange={onChangeRange} setMaxDisplayDate={setMaxDisplayDate} setInitDates={setInitDates} setDisplayData={setDisplayData}
                  setChartData={setChartData} setScoreChart={setScoreChart} setMode={({ target: { value } }) => onModeChange(value)} mode={mode} status={status}
                  isStatLoad={isStatLoad} isChartLoad={isChartLoad} onNormalization={value => onNormalization(value)}
                />
              </Spin>
              :
              <AnomalyDetails firebase={firebase} isNormalized={isNormalized} displayData={displayData}
                threshold={threshold} chartData={chartData} scoreData={scoreChart} chartVariables={chartVariables} anomalyID={anomalyID} pastChartData={pastClosePatterns}
                closePatternData={closePatternData} outliers={outliers} heatMapData={scoreHeatmap} minDisplayDate={minDisplayDate} maxDisplayDate={maxDisplayDate}
                setSelectCloseVar={onChangeCurrentVariable} selectCloseVar={selectCloseVar} currentRange={currentRange} onNormalization={value => onNormalization(value)}
                isLoadDetail={isLoadDetail} isLoadVariableChart={isLoadVariableChart} scaler={scaler} setOutliers={setOutliers}
              />
          }
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}><strong style={{ 'fontVariant': 'small-caps' }}>AnoViz</strong> © 2023 Developed by <a target='_blank' rel="noreferrer" href="https://dm.kaist.ac.kr">KAIST Data Mining Lab</a></Footer>
    </Layout>
  );
}

export default App;