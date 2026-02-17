import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

function MetricCard({ label, value, unit = '', color = 'text-gray-900', description }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 text-center">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      {value !== null && value !== undefined ? (
        <div className={`text-xl font-bold ${color}`}>
          {typeof value === 'number' ? value.toFixed(2) : value}{unit}
        </div>
      ) : (
        <div className="text-xl font-bold text-gray-400">-</div>
      )}
      {description && (
        <div className="text-xs text-gray-400 mt-1">{description}</div>
      )}
    </div>
  )
}

function PredictionAccuracy({ ticker }) {
  const [accuracy, setAccuracy] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!ticker) return
    loadData(ticker)
  }, [ticker])

  const loadData = async (t) => {
    setLoading(true)
    setError(null)
    try {
      const [accuracyRes, historyRes] = await Promise.all([
        axios.get(`/api/v1/predictions/${t}/accuracy`),
        axios.get(`/api/v1/predictions/${t}/history?limit=30`)
      ])
      setAccuracy(accuracyRes.data.data)
      setHistory(historyRes.data.data?.history || [])
    } catch (err) {
      // 종목이 DB에 없으면 404 (예측 기록 없음) - 에러로 처리하지 않음
      if (err.response?.status === 404) {
        setAccuracy(null)
        setHistory([])
      } else {
        setError('정확도 데이터 로드 실패')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateActuals = async () => {
    setUpdating(true)
    try {
      const res = await axios.post(`/api/v1/predictions/${ticker}/update-actuals`)
      const updated = res.data.data?.updated_count || 0
      alert(`실제 가격 ${updated}건 업데이트 완료`)
      // 데이터 새로고침
      await loadData(ticker)
    } catch (err) {
      alert('업데이트 실패: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUpdating(false)
    }
  }

  // 차트 데이터: 예측가와 실제가를 날짜 기준으로 매핑
  const chartData = history
    .filter(h => h.actual_price !== null)
    .map(h => ({
      date: new Date(h.target_date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
      예측가: Number(h.predicted_price.toFixed(2)),
      실제가: Number(h.actual_price.toFixed(2))
    }))
    .reverse()

  const metrics = accuracy?.metrics
  const isInsufficient = !accuracy || accuracy.evaluated_count < 2
  const correctionInfo = accuracy?.correction_info

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">예측 정확도 분석</h2>
        <div className="flex items-center gap-2">
          {accuracy && (
            <span className="text-sm text-gray-500">
              총 {accuracy.total_predictions}건 예측 / {accuracy.evaluated_count}건 평가 완료
            </span>
          )}
          <button
            onClick={handleUpdateActuals}
            disabled={updating || !ticker}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            {updating ? '업데이트 중...' : '실제가 업데이트'}
          </button>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8 text-gray-400">분석 중...</div>
      )}

      {error && (
        <div className="text-center py-4 text-red-500">{error}</div>
      )}

      {!loading && !error && isInsufficient && (
        <div className="text-center py-8">
          <div className="text-gray-400 text-4xl mb-3">📊</div>
          <div className="text-gray-500 font-medium">
            예측 기록이 쌓이면 정확도를 분석할 수 있습니다
          </div>
          <div className="text-gray-400 text-sm mt-1">
            현재 {accuracy?.evaluated_count || 0}건 / 최소 2건 필요
          </div>
          {correctionInfo && !correctionInfo.is_corrected && (
            <div className="text-gray-400 text-sm mt-1">
              오차 보정 비활성 (최소 5건 필요)
            </div>
          )}
        </div>
      )}

      {!loading && !error && !isInsufficient && (
        <>
          {/* 정확도 지표 카드 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <MetricCard
              label="MAE (평균 절대 오차)"
              value={metrics?.mae}
              unit="$"
              description="낮을수록 정확"
            />
            <MetricCard
              label="MAPE (평균 절대 오차율)"
              value={metrics?.mape}
              unit="%"
              color={
                metrics?.mape < 5 ? 'text-green-600' :
                metrics?.mape < 10 ? 'text-yellow-600' : 'text-red-600'
              }
              description="낮을수록 정확"
            />
            <MetricCard
              label="RMSE"
              value={metrics?.rmse}
              unit="$"
              description="이상치에 민감"
            />
            <MetricCard
              label="방향 정확도"
              value={metrics?.direction_accuracy}
              unit="%"
              color={
                metrics?.direction_accuracy >= 60 ? 'text-green-600' :
                metrics?.direction_accuracy >= 50 ? 'text-yellow-600' : 'text-red-600'
              }
              description="상승/하락 방향 예측"
            />
          </div>

          {/* 오차 보정 정보 */}
          {correctionInfo && (
            <div className={`rounded-lg p-3 mb-4 text-sm flex items-center gap-2 ${
              correctionInfo.is_corrected ? 'bg-blue-50 text-blue-700' : 'bg-gray-50 text-gray-500'
            }`}>
              <span>{correctionInfo.is_corrected ? '✓' : '○'}</span>
              <span>
                오차 보정: {correctionInfo.is_corrected
                  ? `적용 중 (계수: ${correctionInfo.factor > 0 ? '+' : ''}${(correctionInfo.factor * 100).toFixed(2)}%, 평균 오차 ${correctionInfo.avg_error_pct}%)`
                  : `비활성 (${correctionInfo.data_count}건 / 최소 5건 필요)`
                }
              </span>
            </div>
          )}

          {/* 예측 vs 실제 차트 */}
          {chartData.length >= 2 && (
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-2">예측가 vs 실제가</h3>
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="예측가"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="실제가"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default PredictionAccuracy
