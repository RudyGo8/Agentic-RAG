<template>
  <div class="chart-display" v-show="_chartDef">
    <div class="chart-header">
      <h4>{{ _chartDef.title }}</h4>
      <span class="chart-summary" v-if="parsed?.summary">{{ parsed.summary }}</span>
    </div>
    <div ref="chartDom" class="chart-box"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  props: { content: { type: String, required: true } },
  data() {
    return { parsed: null, chartInstance: null, _parseTimer: null }
  },
  computed: {
    _chartDef() {
      const p = this.parsed
      if (!p || !p.chart || !Array.isArray(p.data) || !p.data.length) return null
      return { type: p.chart.type || 'bar', title: p.chart.title || '', data: p.data }
    }
  },
  watch: {
    content: {
      immediate: true,
      handler() {
        // 防抖：流式场景下等 300ms 没新内容再解析
        clearTimeout(this._parseTimer)
        this._parseTimer = setTimeout(() => {
          this.parsed = _tryParse(this.content || '')
          this.$nextTick(() => this._render())
        }, 300)
      }
    }
  },
  mounted() { this._render() },
  beforeUnmount() {
    clearTimeout(this._parseTimer)
    this.chartInstance?.dispose()
  },
  methods: {
    _render() {
      const def = this._chartDef
      const dom = this.$refs.chartDom
      if (!def || !dom) return
      if (!this.chartInstance) this.chartInstance = echarts.init(dom)
      this.chartInstance.setOption(_buildOption(def), true)
    }
  }
}

function _tryParse(text) {
  try {
    let t = text || ''
    const code = t.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (code) t = code[1]
    const m = t.match(/\{[\s\S]*"chart"[\s\S]*\}/)
    if (!m) return null
    const p = JSON.parse(m[0])
    return (p.chart && p.data) ? p : null
  } catch { return null }
}

function _buildOption(def) {
  const { type, title, data } = def
  if (type === 'metric') {
    const row = data[0] || {}
    const items = [
      { label: '总任务数', value: row.total ?? '-' },
      { label: '成功', value: row.success ?? '-' },
      { label: '失败', value: row.fail ?? '-' },
      { label: '成功率', value: row.success_rate != null ? row.success_rate + '%' : '-' },
      { label: '平均耗时', value: row.avg_duration_sec != null ? row.avg_duration_sec + 's' : '-' },
    ]
    return {
      title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
      grid: { top: 50, bottom: 10, left: 10, right: 10 },
      xAxis: { show: false, data: items.map(i => i.label) },
      yAxis: { show: false },
      series: [{
        type: 'bar', data: items.map(i => (typeof i.value === 'number' ? i.value : 0)),
        label: { show: true, formatter: (p) => items[p.dataIndex].label + '\n' + items[p.dataIndex].value, fontSize: 12 },
        barWidth: '50%', itemStyle: { borderRadius: 4, color: '#409EFF' },
      }],
    }
  }
  if (type === 'line') {
    const dates = data.map(r => r.date || '')
    return {
      title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { data: ['总量', '成功', '失败'], bottom: 0 },
      grid: { top: 40, bottom: 30, left: 40, right: 10 },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value' },
      series: [
        { name: '总量', type: 'line', data: data.map(r => r.total || 0), smooth: true },
        { name: '成功', type: 'line', data: data.map(r => r.success || 0), smooth: true },
        { name: '失败', type: 'line', data: data.map(r => r.fail || 0), smooth: true },
      ],
    }
  }
  if (type === 'bar') {
    const names = data.map(r => r.site || r.name || '')
    return {
      title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      grid: { top: 40, bottom: 30, left: 40, right: 10 },
      xAxis: { type: 'category', data: names, axisLabel: { rotate: 30 } },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: data.map(r => r.total || r.value || 0), itemStyle: { borderRadius: 4, color: '#409EFF' } }],
    }
  }
  if (type === 'pie') {
    return {
      title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{ type: 'pie', radius: ['30%', '70%'], center: ['55%', '55%'], data: data.map(r => ({ name: r.name || '', value: r.value || 0 })), label: { formatter: '{b}: {c}' } }],
    }
  }
  return { title: { text: title, left: 'center' }, series: [] }
}
</script>

<style scoped>
.chart-display { margin: 12px 0; border: 1px solid var(--el-border-color-light, #e4e7ed); border-radius: 8px; overflow: hidden; background: #fff; }
.chart-header { padding: 10px 14px 0; }
.chart-header h4 { margin: 0 0 2px; font-size: 14px; }
.chart-summary { font-size: 12px; color: #909399; }
.chart-box { width: 100%; height: 240px; }
</style>
