import moment from "moment"

const N = 144 * 3
export const threshold = Math.random() * 1
export const variables = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

export const stats = {
    total: { n: 4234, percent: 23 },
    variables: [
        { name: 'A', n: 343, percent: 13 },
        { name: 'B', n: 434, percent: 20 },
        { name: 'C', n: 1, percent: 0 },
        { name: 'D', n: 55, percent: -7 },
        { name: 'E', n: 17, percent: 1 },
        { name: 'F', n: 0, percent: -100 },
        { name: 'G', n: 3, percent: -13 },
    ]
}

export const variable_chart = [
    { name: 'A', value: 60 },
    { name: 'B', value: 30 },
    { name: 'C', value: 10 }
]

export let hourly_chart = []
for (let index = 0; index < 24; index++) {
    hourly_chart.push({ time: index.toString() + ':00', value: Math.floor(Math.random() * 24) })
}

export let weekly_chart = []
for (const day of ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']) {
    weekly_chart.push({ time: day, value: Math.floor(Math.random() * 100) })
}

export let stream_labels = [] // x-axis label i.e., date
for (let index = 0; index < N; index++) {
    let date = moment('2021-01-01 00:00:00').add(index * 10, 'minutes').format('YYYY-MM-DD HH:mm:ss')
    stream_labels.push(date)
}
export let stream_data = [] // variable-wise data i.e., each variable = one dataset
for (const variable of variables) {
    let R = Math.floor(Math.random() * 255)
    let G = Math.floor(Math.random() * 255)
    let B = Math.floor(Math.random() * 255)
    let var_dataset = {
        label: variable,
        data: [],
        // borderColor: `rgb(${R}, ${G}, ${B})`
    }

    for (let index = 0; index < N; index++) {
        var_dataset.data.push(Math.floor(Math.random() * 1000))
    }

    stream_data.push(var_dataset)
}

export const simulate_data = (n_data) => {
    for (const var_dataset of stream_data) {
        for (let index = 0; index < n_data; index++) {
            var_dataset.data.push(Math.floor(Math.random() * 1000))
        }
    }

    for (let index = 1; index < n_data + 1; index++) {
        let date = moment(stream_labels[stream_labels.length-1]).add(index * 10, 'minutes').format('YYYY-MM-DD HH:mm:ss')
        stream_labels.push(date)
    }

    return [stream_data, stream_labels]
}


export let main_chart = []
for (let index = 0; index < N; index++) {
    let date = moment('2021-01-01 00:00:00').add(index * 10, 'minutes').format('YYYY-MM-DD HH:mm:ss')
    for (const variable of variables) {
        let score = Math.random()
        main_chart.push({
            date: date,
            value: Math.floor(Math.random() * 1000),
            name: variable,
            score: score,
            label: Number(score > threshold),
        })
    }
}

export let anomaly_score_chart = []
for (let index = 0; index < N; index++) {
    let date = moment('2021-01-01 00:00:00').add(index * 10, 'minutes').format('YYYY-MM-DD HH:mm:ss')
    let item_date = main_chart.filter(item => item.date === date)
    let sum_scores = 0
    item_date.forEach(item => {
        sum_scores += item.score
    });
    let avg_score = sum_scores / item_date.length
    anomaly_score_chart.push({
        date: date,
        score: avg_score,
    })
}

export const close_pattern_chart = []
for (const variable of variables) {
    for (const range of ['anomaly', '21.05.26 - 21.06.26', '21.04.26 - 21.05.26', '21.03.26 - 21.04.26', '21.02.26 - 21.03.26']) {
        for (let index = 1; index < 31; index++) {
            if (range === 'anomaly') {
                close_pattern_chart.push({
                    date: index.toString(),
                    range: range,
                    name: variable,
                    value: index < 10 || index > 20 ? Math.random() * 100 : 100 + Math.random() * 500,
                    label: index < 10 || index > 20 ? 0 : 1
                })
            } else {
                close_pattern_chart.push({
                    date: index.toString(),
                    range: range,
                    name: variable,
                    value: Math.random() * 100,
                    label: 0
                })
            }
        }
    }
}

export const possible_outliers = []
for (const variable of variables) {
    for (let index = 0; index < 10; index++) {
        possible_outliers.push({
            name: variable,
            value: index % 2 === 0 ? Math.random() * 1000 : Math.random() * -200
        })

    }
}

export let score_heatmap = []
for (let index = 0; index < N; index++) {
    let date = moment('2021-01-01 00:00:00').add(index * 10, 'minutes').format('YYYY-MM-DD HH:mm:ss')
    let rev_vars = variables.slice().reverse()
    rev_vars.push('Overall')
    for (const variable of rev_vars) {
        if (variable === 'Overall') {
            let date_data = main_chart.filter(data => data.date === date)
            let sum_score = 0
            date_data.forEach(item => {
                sum_score += item.score
            })
            let daily_score = sum_score / date_data.length
            score_heatmap.push({
                date: date,
                score: daily_score,
                name: variable
            })
        } else {
            score_heatmap = score_heatmap.concat(main_chart.filter(data => data.date === date && data.name === variable))
        }
    }

}