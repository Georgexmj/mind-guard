import ReactECharts from 'echarts-for-react'
import type { DomainScores } from '../types'

interface CognitiveRadarProps {
  domainScores: DomainScores
  height?: number
}

const dimensionLabels = {
  memory: '记忆力',
  orientation: '定向力',
  language: '语言能力',
  attention: '注意力',
  visuospatial: '视空间',
  executive: '执行功能',
}

export default function CognitiveRadar({ domainScores, height = 380 }: CognitiveRadarProps) {
  const indicators = [
    { name: '记忆力', max: 10 },
    { name: '定向力', max: 10 },
    { name: '语言能力', max: 10 },
    { name: '注意力', max: 10 },
    { name: '视空间', max: 10 },
    { name: '执行功能', max: 10 },
  ]

  const scoreValues = [
    domainScores.memory,
    domainScores.orientation,
    domainScores.language,
    domainScores.attention,
    domainScores.visuospatial,
    domainScores.executive,
  ]

  // Reference values (normal range = 8, warning = 5)
  const normalRef = [8, 8, 8, 8, 8, 8]
  const warningRef = [5, 5, 5, 5, 5, 5]

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: { name: string; value: number[] }) => {
        if (params.name === '认知评分') {
          const keys: (keyof DomainScores)[] = [
            'memory',
            'orientation',
            'language',
            'attention',
            'visuospatial',
            'executive',
          ]
          return keys
            .map(
              (k, i) =>
                `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#1677ff;margin-right:6px"></span>${dimensionLabels[k]}: <b>${params.value[i]}</b> / 10`
            )
            .join('<br/>')
        }
        return params.name
      },
      backgroundColor: 'rgba(0,21,41,0.85)',
      borderColor: '#1677ff',
      textStyle: { color: '#fff', fontSize: 13 },
      padding: [10, 14],
    },
    legend: {
      data: ['认知评分', '正常参考线', '风险阈值'],
      bottom: 0,
      textStyle: { color: '#666', fontSize: 12 },
      itemGap: 20,
    },
    radar: {
      indicator: indicators,
      center: ['50%', '48%'],
      radius: '62%',
      startAngle: 90,
      splitNumber: 5,
      axisName: {
        color: '#334155',
        fontSize: 13,
        fontWeight: 600,
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(22,119,255,0.02)', 'rgba(22,119,255,0.05)', 'rgba(22,119,255,0.08)', 'rgba(22,119,255,0.11)', 'rgba(22,119,255,0.14)'],
        },
      },
      axisLine: {
        lineStyle: { color: 'rgba(22,119,255,0.2)' },
      },
      splitLine: {
        lineStyle: { color: 'rgba(22,119,255,0.15)', width: 1 },
      },
    },
    series: [
      {
        name: '认知评分',
        type: 'radar',
        data: [
          {
            value: scoreValues,
            name: '认知评分',
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: {
              color: '#1677ff',
              width: 2.5,
            },
            areaStyle: {
              color: {
                type: 'radial',
                x: 0.5,
                y: 0.5,
                r: 0.5,
                colorStops: [
                  { offset: 0, color: 'rgba(22,119,255,0.5)' },
                  { offset: 1, color: 'rgba(22,119,255,0.1)' },
                ],
              },
            },
            itemStyle: {
              color: '#1677ff',
              borderColor: '#fff',
              borderWidth: 2,
            },
          },
          {
            value: normalRef,
            name: '正常参考线',
            symbol: 'none',
            lineStyle: {
              color: '#52c41a',
              width: 1.5,
              type: 'dashed',
            },
            areaStyle: {
              color: 'rgba(82,196,26,0.04)',
            },
            itemStyle: { color: '#52c41a' },
          },
          {
            value: warningRef,
            name: '风险阈值',
            symbol: 'none',
            lineStyle: {
              color: '#faad14',
              width: 1.5,
              type: 'dotted',
            },
            areaStyle: {
              color: 'rgba(0,0,0,0)',
            },
            itemStyle: { color: '#faad14' },
          },
        ],
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height, width: '100%' }}
      opts={{ renderer: 'svg' }}
      notMerge
      lazyUpdate
    />
  )
}
