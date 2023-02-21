/* eslint-disable import/no-anonymous-default-export */
import React from 'react'
import { PageHeader, Upload, message } from 'antd';
import { FileAddFilled } from '@ant-design/icons';

import config from './config'

const { Dragger } = Upload;

export default ({ setChartData, setChartVariables, setFileName, setThreshold }) => {
    const acceptableExts = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    const fileProps = {
        name: 'file',
        multiple: false,
        maxCount: 1,
        action: config.SERVER_PATH + '/upload',
        beforeUpload: file => {
            const isCSV = acceptableExts.includes(file.type)
            if (!isCSV) {
                message.error(`${file.name} is not an acceptable file!`);
            }
            return isCSV || Upload.LIST_IGNORE;
        },
        onChange(info) {
            const { status } = info.file;

            if (status === 'done') {
                const response = JSON.parse(info.file.xhr.response)
                if (response.status === 200) {
                    message.success(`${info.file.name} file uploaded successfully.`);
                    setChartData(response.data)
                    setChartVariables(response.columns)
                    setThreshold(response.threshold)
                    setFileName(info.file.name)
                } else {
                    message.error(`${info.file.name} file format is invalid.`)
                }
            } else if (status === 'error') {
                message.error(`${info.file.name} file upload failed.`);
            }
        },
        onDrop(e) {
            const file = e.dataTransfer.files[0]
            const isCSV = acceptableExts.includes(file.type)
            if (!isCSV) {
                message.error(`${file.name} is not an acceptable file!`);
            }
        },
    };

    return (
        <React.Fragment>
            <PageHeader title="File Uploader" />
            <Dragger accept={acceptableExts} {...fileProps}>
                <p className="ant-upload-drag-icon">
                    <FileAddFilled />
                </p>
                <p className="ant-upload-text">Click or Drag a file to this area to upload.</p>
                <p className="ant-upload-hint"><strong>Please upload <u>1 file</u> with <em>.csv</em> extension.</strong></p>
                <p className="ant-upload-hint">Your file will be immediately deleted from the server after preprocessing.</p>
            </Dragger>
        </React.Fragment>
    )
}