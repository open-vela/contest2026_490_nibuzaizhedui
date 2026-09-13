/**
 * 端侧 AI 能力封装（@system.velaclaw）。
 *
 * velaclaw 仅在 openvela 真实环境（goldfish 模拟器 / 真机 + ai_agent 进程）可用，
 * AIoT IDE 内置模拟器中可能加载不到。因此这里用 require + try/catch 做软加载：
 * 拿不到模块或调用失败时，返回内置的降级建议，保证任何环境都能完整演示。
 */

const FALLBACK_ADVICE =
  '你的压力值偏高，建议先完成一轮 4-2-6 呼吸训练：用鼻子慢吸 4 秒，屏住 2 秒，' +
  '再用嘴巴缓呼 6 秒。呼气比吸气长，能直接激活放松反应。结束后喝口温水，' +
  '起身活动一下肩颈，看会儿窗外远处。'

const FALLBACK_ANSWERS = [
  {
    keys: ['压力', '紧张', '焦虑'],
    text: '检测到你在问压力管理：短时减压最有效的是拉长呼气的呼吸法（吸4呼6），配合肩颈放松。' +
      '如果压力持续偏高，试着把待办清单拆小，一次只专注一件事。'
  },
  {
    keys: ['心率', '心跳'],
    text: '安静时成人心率正常范围约为 60~100 次/分，长期运动者可能低于 60。' +
      '刚运动完或情绪紧张时心率升高是正常的，休息 5 分钟后再看会更有参考价值。'
  },
  {
    keys: ['睡眠', '睡不着', '失眠'],
    text: '睡前 1 小时建议：调暗灯光、放下手机，做 5 分钟 4-7-8 呼吸（吸4 屏7 呼8）。' +
      '保持卧室安静凉爽，固定起床时间比早点上床更有效。'
  },
  {
    keys: ['呼吸', '放松', '冥想'],
    text: '推荐两种节奏：4-2-6（快速平复，适合白天）和 4-7-8（助眠，适合睡前）。' +
      '呼气阶段想象肩膀下沉，每天 2~3 组，坚持一周会感觉明显不同。'
  }
]

let velaclawModule = undefined
let loadAttempted = false

function loadVelaclaw() {
  if (loadAttempted) {
    return velaclawModule
  }
  loadAttempted = true
  try {
    // eslint-disable-next-line no-undef
    velaclawModule = require('@system.velaclaw')
    console.info('velaclaw loaded')
  } catch (e) {
    console.warn('velaclaw not available, fallback mode: ' + e)
    velaclawModule = null
  }
  return velaclawModule
}

/** 当前环境是否具备端侧 AI 能力 */
export function aiAvailable() {
  const mod = loadVelaclaw()
  // 某些镜像 require 失败不抛异常而是返回残缺模块，需再校验方法存在
  return !!mod && typeof mod.ask === 'function'
}

/**
 * 向端侧 AI 提问（回调风格，规避该运行时 Promise 超时路径的缺陷）。
 * @param {string} query 问题
 * @param {Function} onReply 回复回调；失败/超时返回降级文案，不抛错。
 */
export function ask(query, onReply) {
  let settled = false
  const finish = (txt) => {
    if (!settled) {
      settled = true
      onReply(txt)
    }
  }
  const mod = loadVelaclaw()
  if (!mod || typeof mod.ask !== 'function') {
    finish(fallbackAnswer(query))
    return
  }
  // 残缺模块可能注册了 ask 但回调永不触发，超时强制走降级
  const timer = setTimeout(() => {
    console.warn('velaclaw.ask timeout, fallback')
    finish(fallbackAnswer(query))
  }, 4000)
  mod.ask({
    query,
    success: (res) => {
      if (timer) {
        clearTimeout(timer)
      }
      finish(res && res.reply ? res.reply : fallbackAnswer(query))
    },
    fail: (data, code) => {
      if (timer) {
        clearTimeout(timer)
      }
      console.warn('velaclaw.ask fail code=' + code)
      finish(fallbackAnswer(query))
    }
  })
}

/** 本地降级：按关键词匹配常见问题，兜底返回通用建议 */
function fallbackAnswer(query) {
  const q = (query || '').toString()
  for (let i = 0; i < FALLBACK_ANSWERS.length; i++) {
    const item = FALLBACK_ANSWERS[i]
    for (let j = 0; j < item.keys.length; j++) {
      if (q.indexOf(item.keys[j]) >= 0) {
        return item.text
      }
    }
  }
  return FALLBACK_ADVICE
}

/** 根据训练前后数据生成给 AI 的提问（带上下文，回答更贴合） */
export function buildAdviceQuery(session) {
  const drop = session.beforeStress - session.afterStress
  return (
    '我刚完成了一轮' + session.durationSec + '秒的呼吸训练：' +
    '压力值从 ' + session.beforeStress + ' 变为 ' + session.afterStress +
    '（下降了 ' + drop + '），心率从 ' + session.beforeHr + ' 变为 ' + session.afterHr +
    '。请用不超过 60 个字，给我一句简短的恢复评价和一条下一步放松建议。'
  )
}

export { FALLBACK_ADVICE }
