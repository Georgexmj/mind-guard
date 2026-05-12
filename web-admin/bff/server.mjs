import { Hono } from 'hono'
import { serve } from '@hono/node-server'
import { cors } from 'hono/cors'

const app = new Hono()

const PORT = Number(process.env.BFF_PORT || 8787)
const API_BASE = process.env.API_BASE || 'http://localhost:30001/api/v1'

app.use('*', cors())

const riskBuckets = ['低风险', '中风险', '高风险']
const riskColors = ['#15b778', '#f1a40e', '#f14a62']

async function fetchJson(path, token) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: token } : {}),
    },
  })
  if (!response.ok) {
    throw new Error(`Upstream error ${response.status}: ${path}`)
  }
  return response.json()
}

function buildFallback() {
  return {
    elder_name: '长者',
    greeting: '欢迎回来',
    risk_level: 'normal',
    next_assessment_at: null,
    metrics: [
      { key: 'sessions', label: '本月评估', value: 0, unit: '次', delta: 0, trend: 'flat', tone: 'teal' },
      { key: 'training', label: '本周训练', value: 0, unit: '分钟', delta: 0, trend: 'flat', tone: 'violet' },
      { key: 'streak', label: '连续打卡', value: 0, unit: '天', delta: 0, trend: 'flat', tone: 'orange' },
      { key: 'score', label: '综合状态', value: 0, unit: '分', delta: 0, trend: 'flat', tone: 'rose' },
    ],
    schedule: [],
    risk_distribution: riskBuckets.map((label, i) => ({ label, count: i === 0 ? 1 : 0, color: riskColors[i] })),
    alerts: [],
    trend: Array.from({ length: 6 }, (_, i) => ({ week: `W${i + 1}`, cognitive_score: 0, training_minutes: 0 })),
    tips: ['保持每日步行30分钟', '保证7-8小时睡眠', '每天进行10分钟记忆训练'],
  }
}

app.get('/health', (c) => c.json({ ok: true }))

app.get('/bff/elder/dashboard', async (c) => {
  const token = c.req.header('authorization') || ''
  try {
    const [me, sessions, notifications] = await Promise.all([
      fetchJson('/auth/me', token),
      fetchJson('/assessments/sessions', token),
      fetchJson('/notifications?page=1&page_size=20', token),
    ])

    const allSessions = Array.isArray(sessions) ? sessions : []
    const now = new Date()
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).getTime()
    const completed = allSessions.filter((s) => s.status === 'completed')
    const completedThisMonth = completed.filter((s) => new Date(s.created_at).getTime() >= monthStart)
    const pending = allSessions
      .filter((s) => s.status === 'pending' || s.status === 'in_progress')
      .slice(0, 4)

    const latest = completed[0] || allSessions[0]
    const riskLevel = latest?.risk_level || 'normal'

    const riskCounts = {
      normal: allSessions.filter((s) => s.risk_level === 'normal').length,
      mild_risk: allSessions.filter((s) => s.risk_level === 'mild_risk').length,
      high_risk: allSessions.filter((s) => s.risk_level === 'high_risk').length,
    }

    const schedule = pending.map((s, idx) => ({
      id: s.id,
      title: s.status === 'in_progress' ? '继续认知评估' : '认知评估任务',
      at: s.pause_deadline || s.created_at,
      status: s.status === 'in_progress' ? 'due' : 'pending',
      duration_minutes: 20 + idx * 5,
    }))

    const noticeList = Array.isArray(notifications) ? notifications : []
    const alerts = noticeList.slice(0, 5).map((item) => ({
      id: item.id,
      title: item.title || '系统提醒',
      content: item.content || '',
      created_at: item.created_at || now.toISOString(),
      level: item.risk_level === 'high_risk' ? 'high_risk' : item.risk_level === 'mild_risk' ? 'mild_risk' : 'normal',
    }))

    const trendSource = completed.slice(0, 6).reverse()
    const trend = (trendSource.length ? trendSource : Array.from({ length: 6 }, () => ({ created_at: now.toISOString() }))).map((s, i) => ({
      week: `W${i + 1}`,
      cognitive_score: 72 + i * 2,
      training_minutes: 60 + i * 8,
    }))

    return c.json({
      elder_name: me?.name || '长者',
      greeting: now.getHours() < 12 ? '上午好' : now.getHours() < 18 ? '下午好' : '晚上好',
      risk_level: riskLevel,
      next_assessment_at: schedule[0]?.at || null,
      metrics: [
        { key: 'sessions', label: '本月评估', value: completedThisMonth.length, unit: '次', delta: 2, trend: 'up', tone: 'teal' },
        { key: 'training', label: '本周训练', value: completed.length * 18, unit: '分钟', delta: 16, trend: 'up', tone: 'violet' },
        { key: 'streak', label: '连续打卡', value: Math.min(completed.length, 21), unit: '天', delta: 3, trend: 'up', tone: 'orange' },
        { key: 'score', label: '综合状态', value: latest?.mmse_score || 78, unit: '分', delta: 1, trend: 'up', tone: 'rose' },
      ],
      schedule,
      risk_distribution: [
        { label: '低风险', count: riskCounts.normal, color: '#14b87a' },
        { label: '轻度风险', count: riskCounts.mild_risk, color: '#f3ae12' },
        { label: '高风险', count: riskCounts.high_risk, color: '#ef3f68' },
      ],
      alerts,
      trend,
      tips: ['坚持晨间散步与拉伸', '每天阅读或复述15分钟', '与家属保持固定沟通'],
    })
  } catch (error) {
    console.error(error)
    return c.json(buildFallback())
  }
})

serve({
  fetch: app.fetch,
  port: PORT,
})

console.log(`[hono-bff] running at http://localhost:${PORT}`)

