/**
 * 呼吸训练引擎：相位推进 + 圆环尺寸计算。
 * 纯函数实现，便于单独测试与复用（后续可加 4-7-8 助眠模式）。
 */

export const PATTERNS = {
  calm: {
    name: '4-2-6 平复',
    desc: '吸气4秒 · 屏息2秒 · 呼气6秒',
    short: '吸 4 · 屏 2 · 呼 6',
    phases: [
      { label: '吸气', ms: 4000, target: 1 },
      { label: '屏息', ms: 2000, target: 1, hold: true },
      { label: '呼气', ms: 6000, target: 0 }
    ]
  },
  sleep: {
    name: '4-7-8 助眠',
    desc: '吸气4秒 · 屏息7秒 · 呼气8秒',
    short: '吸 4 · 屏 7 · 呼 8',
    phases: [
      { label: '吸气', ms: 4000, target: 1 },
      { label: '屏息', ms: 7000, target: 1, hold: true },
      { label: '呼气', ms: 8000, target: 0 }
    ]
  }
}

/** 圆环尺寸范围（designWidth 466 圆屏安全区，上下需留文字行） */
export const SIZE = { min: 190, max: 300 }

/** ease-in-out 曲线，让圆的伸缩有“呼吸感” */
export function easeInOut(t) {
  if (t < 0.5) {
    return 2 * t * t
  }
  return 1 - Math.pow(-2 * t + 2, 2) / 2
}

/**
 * 根据当前相位进度计算圆的尺寸与相位文案。
 * @param {object} pattern PATTERNS 之一
 * @param {number} phaseIdx 当前相位下标
 * @param {number} elapsedMs 在当前相位内已流逝的毫秒
 */
export function frame(pattern, phaseIdx, elapsedMs) {
  const phase = pattern.phases[phaseIdx]
  const p = Math.min(1, elapsedMs / phase.ms)
  let ratio
  if (phase.hold) {
    ratio = phase.target
  } else if (phase.target === 1) {
    ratio = easeInOut(p)
  } else {
    ratio = 1 - easeInOut(p)
  }
  return {
    size: SIZE.min + (SIZE.max - SIZE.min) * ratio,
    label: phase.label,
    phaseDone: p >= 1
  }
}

/** 整轮总时长（毫秒） */
export function cycleMs(pattern) {
  return pattern.phases.reduce((sum, ph) => sum + ph.ms, 0)
}

/** 数组平均值（null 项忽略） */
export function avg(arr) {
  const valid = arr.filter((v) => v != null)
  if (!valid.length) {
    return null
  }
  return Math.round(valid.reduce((a, b) => a + b, 0) / valid.length)
}
