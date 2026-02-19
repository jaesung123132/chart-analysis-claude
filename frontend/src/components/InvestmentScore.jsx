import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

function ScoreGauge({ score, size = 'lg' }) {
  const color = score >= 70 ? '#22c55e' : score >= 50 ? '#eab308' : '#ef4444'
  const textColor = score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
  const isLarge = size === 'lg'

  return (
    <div className="flex flex-col items-center">
      <div className={`relative ${isLarge ? 'w-36 h-36' : 'w-20 h-20'}`}>
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none" stroke="#e5e7eb" strokeWidth="3"
          />
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none" stroke={color}
            strokeWidth="3"
            strokeDasharray={`${score}, 100`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`${isLarge ? 'text-3xl' : 'text-lg'} font-bold ${textColor}`}>
            {Math.round(score)}
          </span>
          <span className={`${isLarge ? 'text-xs' : 'text-[10px]'} text-gray-400`}>/ 100</span>
        </div>
      </div>
    </div>
  )
}

function GradeBadge({ grade, label }) {
  const gradeColors = {
    'A+': 'bg-green-600',
    'A': 'bg-green-500',
    'B+': 'bg-blue-500',
    'B': 'bg-gray-500',
    'C': 'bg-orange-500',
    'D': 'bg-red-500',
  }
  const bgColor = gradeColors[grade] || 'bg-gray-500'

  return (
    <div className="flex items-center gap-2">
      <span className={`${bgColor} text-white text-lg font-bold px-3 py-1 rounded`}>{grade}</span>
      <span className="text-sm text-gray-600">{label}</span>
    </div>
  )
}

function InvestmentScore({ ticker }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showDetail, setShowDetail] = useState(false)

  useEffect(() => {
    if (!ticker) return
    fetchData(ticker)
  }, [ticker])

  const fetchData = async (t) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`/api/v1/analysis/${t}/comprehensive`)
      setData(res.data.data)
    } catch (err) {
      setError(err.response?.data?.detail || '종합 분석 데이터 로드 실패')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-2">종합 투자 판단 분석 중...</div>
        <div className="text-xs text-gray-300">기본적 분석 + 기술적 분석 + AI 예측을 통합하고 있습니다</div>
      </div>
    )
  }
  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>
  }
  if (!data) {
    return <div className="text-center py-8 text-gray-400">종목을 선택하세요</div>
  }

  const {
    total_score, grade, grade_label, recommendation,
    fundamental_score, technical_score, prediction_score,
    prediction_trend, contradictions, summary
  } = data

  const recColorMap = {
    green: 'bg-green-50 border-green-200 text-green-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    gray: 'bg-gray-50 border-gray-200 text-gray-800',
    orange: 'bg-orange-50 border-orange-200 text-orange-800',
    red: 'bg-red-50 border-red-200 text-red-800',
  }
  const recClass = recColorMap[recommendation?.color] || recColorMap.gray

  const compareData = [
    { name: '기본적 분석 (40%)', score: fundamental_score || 0, fill: '#3b82f6' },
    { name: '기술적 분석 (30%)', score: technical_score || 0, fill: '#8b5cf6' },
    { name: 'AI 예측 (30%)', score: prediction_score || 0, fill: '#f59e0b' },
  ]

  return (
    <div className="space-y-4">
      {/* 모순 경고 배너 */}
      {contradictions && contradictions.length > 0 && (
        <div className="space-y-2">
          {contradictions.map((c, i) => (
            <div key={i} className={`rounded-lg border p-4 ${
              c.severity === 'high'
                ? 'bg-red-50 border-red-200 text-red-800'
                : 'bg-yellow-50 border-yellow-200 text-yellow-800'
            }`}>
              <div className="flex items-start gap-2">
                <span className="text-lg">{c.severity === 'high' ? '!' : 'i'}</span>
                <div>
                  <p className="text-sm font-medium">{c.message}</p>
                  <p className="text-xs mt-1 opacity-80">{c.advice}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 종합 점수 + 등급 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-2">종합 투자 판단</h3>
            <p className="text-sm text-gray-500 mb-4">{data.company_name}</p>
            <GradeBadge grade={grade} label={grade_label} />
          </div>
          <ScoreGauge score={total_score} size="lg" />
        </div>
      </div>

      {/* 추천 의견 */}
      <div className={`rounded-lg border p-4 ${recClass}`}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg font-bold">{recommendation?.action}</span>
        </div>
        <p className="text-sm">{recommendation?.description}</p>
      </div>

      {/* AI 예측 방향 요약 */}
      {prediction_trend && prediction_trend.direction && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-gray-500">AI 예측 (7일)</span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-lg font-bold">${prediction_trend.current_price}</span>
                <span className="text-gray-400">→</span>
                <span className={`text-lg font-bold ${
                  prediction_trend.direction === 'UP' ? 'text-green-600' :
                  prediction_trend.direction === 'DOWN' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  ${prediction_trend.predicted_7d_price}
                </span>
                <span className={`text-sm font-medium ${
                  prediction_trend.change_pct > 0 ? 'text-green-600' :
                  prediction_trend.change_pct < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  ({prediction_trend.change_pct > 0 ? '+' : ''}{prediction_trend.change_pct}%)
                </span>
              </div>
            </div>
            <div className="text-right">
              <span className="text-xs text-gray-500">예측 신뢰도</span>
              <div className={`text-lg font-bold ${
                prediction_trend.avg_confidence >= 0.6 ? 'text-green-600' :
                prediction_trend.avg_confidence >= 0.3 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {(prediction_trend.avg_confidence * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 3축 분석 점수 비교 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-4">3축 분석 점수 비교</h3>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={compareData} layout="vertical" margin={{ left: 30 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={110} />
            <Tooltip formatter={(val) => [`${val.toFixed(1)}점`, '점수']} />
            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
              {compareData.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="flex justify-between text-xs text-gray-500 mt-2">
          <span>기본적: {fundamental_score?.toFixed(1) || '-'}점</span>
          <span>기술적: {technical_score?.toFixed(1) || '-'}점</span>
          <span>AI예측: {prediction_score?.toFixed(1) || '-'}점</span>
        </div>
      </div>

      {/* AI 요약 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-3">AI 종합 판단</h3>
        <p className="text-sm text-gray-700 leading-relaxed">{summary}</p>
      </div>

      {/* 판단 근거 (접이식) */}
      <div className="bg-white rounded-lg shadow p-4">
        <button
          onClick={() => setShowDetail(!showDetail)}
          className="flex items-center justify-between w-full text-left"
        >
          <span className="text-sm font-semibold text-gray-700">이 판단의 근거는?</span>
          <span className="text-gray-400 text-xs">{showDetail ? '접기' : '펼치기'}</span>
        </button>

        {showDetail && (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-4">
            {/* 기본적 분석 세부 */}
            {data.fundamental_detail && (
              <div>
                <h4 className="text-sm font-medium text-blue-700 mb-2">기본적 분석 ({fundamental_score?.toFixed(1) || '-'}점)</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">가치 평가: </span>
                    <span className="font-medium">{data.fundamental_detail.valuation?.score?.toFixed(0) || '-'}점</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">수익성: </span>
                    <span className="font-medium">{data.fundamental_detail.profitability?.score?.toFixed(0) || '-'}점</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">재무 건전성: </span>
                    <span className="font-medium">{data.fundamental_detail.financial_health?.score?.toFixed(0) || '-'}점</span>
                  </div>
                  <div className="bg-gray-50 p-2 rounded">
                    <span className="text-gray-500">애널리스트: </span>
                    <span className="font-medium">{data.fundamental_detail.analyst?.score?.toFixed(0) || '-'}점</span>
                  </div>
                </div>
              </div>
            )}

            {/* 기술적 분석 세부 */}
            {data.technical_detail?.score_details && (
              <div>
                <h4 className="text-sm font-medium text-purple-700 mb-2">기술적 분석 ({technical_score?.toFixed(1) || '-'}점)</h4>
                <div className="grid grid-cols-5 gap-2 text-xs">
                  {[
                    { key: 'rsi', label: 'RSI' },
                    { key: 'macd', label: 'MACD' },
                    { key: 'ma', label: '이동평균' },
                    { key: 'bb', label: '볼린저' },
                    { key: 'pattern', label: '패턴' },
                  ].map(({ key, label }) => (
                    <div key={key} className="bg-gray-50 p-2 rounded text-center">
                      <div className="text-gray-500">{label}</div>
                      <div className="font-medium">{data.technical_detail.score_details[key] || 0}/20</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI 예측 세부 */}
            {prediction_trend && (
              <div>
                <h4 className="text-sm font-medium text-amber-700 mb-2">AI 예측 ({prediction_score?.toFixed(1) || '-'}점)</h4>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="bg-gray-50 p-2 rounded text-center">
                    <div className="text-gray-500">예측 방향</div>
                    <div className={`font-medium ${
                      prediction_trend.direction === 'UP' ? 'text-green-600' :
                      prediction_trend.direction === 'DOWN' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {prediction_trend.direction === 'UP' ? '상승' :
                       prediction_trend.direction === 'DOWN' ? '하락' : '보합'}
                    </div>
                  </div>
                  <div className="bg-gray-50 p-2 rounded text-center">
                    <div className="text-gray-500">변동률</div>
                    <div className="font-medium">{prediction_trend.change_pct}%</div>
                  </div>
                  <div className="bg-gray-50 p-2 rounded text-center">
                    <div className="text-gray-500">신뢰도</div>
                    <div className="font-medium">{(prediction_trend.avg_confidence * 100).toFixed(0)}%</div>
                  </div>
                </div>
              </div>
            )}

            <p className="text-xs text-gray-400">
              * 종합 점수 = 기본적 분석(40%) + 기술적 분석(30%) + AI 예측(30%)으로 산출됩니다.
              AI 예측 점수는 예측 방향과 신뢰도를 반영하며, 신뢰도가 낮을수록 중립(50점)에 가깝게 조정됩니다.
              이 분석은 참고용이며 투자 결정의 유일한 근거로 사용해서는 안 됩니다.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default InvestmentScore
