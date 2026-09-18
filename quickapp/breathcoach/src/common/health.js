/**
 * 健康数据访问层：统一封装 service.health 的订阅与取值，
 * 页面只关心数据，不关心接口细节。
 */
import health from '@service.health'

const DATA_TYPES = {
  HEART_RATE: 0,
  SPO2: 6,
  STRESS: 9
}

/** 压力值(1~49) -> 等级与文案 */
export function stressLevel(value) {
  if (value == null) {
    return { level: 'unknown', label: '--', color: '#8b95a5' }
  }
  if (value < 15) {
    return { level: 'low', label: '放松', color: '#3ddc97' }
  }
  if (value < 30) {
    return { level: 'mid', label: '平稳', color: '#4fc3f7' }
  }
  if (value < 40) {
    return { level: 'high', label: '偏高', color: '#ffb74d' }
  }
  return { level: 'severe', label: '紧张', color: '#ff6b6b' }
}

/**
 * 订阅一种健康数据。
 * @returns {Function} 反订阅函数
 */
export function subscribe(dataType, onData, onError) {
  health.subscribeSample({
    dataType,
    callback: (sample) => {
      // sample = { timeStamp: <毫秒>, value: <bpm|%|压力值> }
      if (onData) onData(sample.value, sample.timeStamp)
    },
    fail: (data, code) => {
      console.warn(`subscribeSample fail, dataType=${dataType} code=${code}`)
      if (onError) onError(code)
    }
  })
  return () => {
    try {
      health.unsubscribeSample({ dataType })
    } catch (e) {
      console.warn('unsubscribeSample error', e)
    }
  }
}

/** 一次性查询多种数据的最近采样，返回 Promise<{ dataType: value }> */
export function getRecent(dataTypes) {
  return new Promise((resolve) => {
    health.getRecentSamples({
      dataTypes,
      success: (list) => {
        const map = {}
        list.forEach((item) => {
          map[item.dataType] = item.data ? item.data.value : null
        })
        resolve(map)
      },
      fail: (data, code) => {
        console.warn('getRecentSamples fail code=' + code)
        resolve({})
      }
    })
  })
}

export { DATA_TYPES }
