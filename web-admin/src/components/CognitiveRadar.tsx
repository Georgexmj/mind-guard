import ReactECharts from 'echarts-for-react'
import type { DomainScores } from '../types'

interface CognitiveRadarProps {
  domainScores: DomainScores
  height?: number
}

const dimensionLabels: Record<keyof DomainScores, string> = {
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
              (key, index) =>
                `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#0f766e;margin-right:6px"></span>${dimensionLabels[key]}：<b>${params.value[index]}</b> / 10`
            )
            .join('<br/>')
        }
        return params.name
      },
      backgroundColor: 'rgba(15, 35, 52, 0.92)',
      borderColor: '#0f766e',
      textStyle: { color: '#fff', fontSize: 13 },
      padding: [10, 14],
    },
    legend: {
      data: ['认知评分', '正常参考线', '风险阈值'],
      bottom: 0,
      textStyle: { color: '#667f91', fontSize: 12 },
      itemGap: 20,
    },
    radar: {
      indicator: indicators,
      center: ['50%', '48%'],
      radius: '62%',
      startAngle: 90,
      splitNumber: 5,
      axisName: {
        color: '#29475a',
        fontSize: 13,
        fontWeight: 600,
      },
      splitArea: {
        areaStyle: {
          color: [
            'rgba(15, 118, 110, 0.02)',
            'rgba(15, 118, 110, 0.05)',
            'rgba(15, 118, 110, 0.08)',
            'rgba(15, 118, 110, 0.11)',
            'rgba(15, 118, 110, 0.14)',
          ],
        },
      },
      axisLine: {
        lineStyle: { color: 'rgba(15, 118, 110, 0.2)' },
      },
      splitLine: {
        lineStyle: { color: 'rgba(15, 118, 110, 0.16)', width: 1 },
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
              color: '#0f766e',
              width: 2.5,
            },
            areaStyle: {
              color: {
                type: 'radial',
                x: 0.5,
                y: 0.5,
                r: 0.5,
                colorStops: [
                  { offset: 0, color: 'rgba(15, 118, 110, 0.46)' },
                  { offset: 1, color: 'rgba(15, 118, 110, 0.08)' },
                ],
              },
            },
            itemStyle: {
              color: '#0f766e',
              borderColor: '#ffffff',
              borderWidth: 2,
            },
          },
          {
            value: normalRef,
            name: '正常参考线',
            symbol: 'none',
            lineStyle: {
              color: '#16a34a',
              width: 1.5,
              type: 'dashed',
            },
            areaStyle: {
              color: 'rgba(22, 163, 74, 0.04)',
            },
            itemStyle: { color: '#16a34a' },
          },
          {
            value: warningRef,
            name: '风险阈值',
            symbol: 'none',
            lineStyle: {
              color: '#d97706',
              width: 1.5,
              type: 'dotted',
            },
            areaStyle: {
              color: 'rgba(0,0,0,0)',
            },
            itemStyle: { color: '#d97706' },
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
