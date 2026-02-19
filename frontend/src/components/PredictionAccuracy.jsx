import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

// 메트릭 설명 상수
const METRIC_INFO = {
  mae: {
    label: 'MAE (평균 절대 오차)',
    description: '예측 가격과 실제 가격의 차이를 절대값으로 평균한 것입니다. 예를 들어 MAE가 $5이면, 평균적으로 예측이 $5 정도 벗어난다는 의미입니다.',
    interpretation: '값이 낮을수록 예측이 정확합니다. 주가 수준에 따라 해석이 달라지므로, MAPE와 함께 봐야 합니다.',
    thresholds: [
      { max: 5, grade: '매우 정확', color: 'text-green-600' },
      { max: 15, grade: '양호', color: 'text-blue-600' },
      { max: Infinity, grade: '개선 필요', color: 'text-red-600' },
    ],
  },
  mape: {
    label: 'MAPE (평균 절대 오차율)',
    description: '예측 오차를 백분율로 나타낸 것입니다. 주가 수준과 관계없이 예측 정확도를 비교할 수 있는 지표입니다.',
    interpretation: '5% 미만이면 매우 정확, 10% 미만이면 양호, 10% 이상이면 개선이 필요합니다.',
    thresholds: [
      { max: 5, grade: '매우 정확', color: 'text-green-600' },
      { max: 10, grade: '양호', color: 'text-yellow-600' },
      { max: Infinity, grade: '개선 필요', color: 'text-red-600' },
    ],
  },
  rmse: {
    label: 'RMSE (평균 제곱근 오차)',
    description: '오차를 제곱하여 평균한 뒤 제곱근을 취한 값입니다. 큰 오차에 더 높은 가중치를 부여하므로, 이상치에 민감합니다.',
    interpretation: 'MAE보다 RMSE가 훨씬 크면, 일부 예측에서 큰 오차가 발생했다는 의미입니다.',
    thresholds: [
      { max: 8, grade: '매우 정확', color: 'text-green-600' },
      { max: 20, grade: '양호', color: 'text-blue-600' },
      { max: Infinity, grade: '개선 필요', color: 'text-red-600' },
    ],
  },
  direction_accuracy: {
    label: '방향 정확도',
    description: '주가가 상승할지 하락할지의 방향을 맞춘 비율입니다. 가격 정확도와 별개로, 추세 예측 능력을 평가합니다.',
    interpretation: '60% 이상이면 유의미한 예측, 50%는 동전 던지기 수준입니다.',
    thresholds: [
      { min: 60, grade: '우수', color: 'text-green-600' },
      { min: 50, grade: '보통', color: 'text-yellow-600' },
      { min: 0, grade: '미흡', color: 'text-red-600' },
    ],
  },
}

function getGrade(metricKey, value) {
  const info = METRIC_INFO[metricKey]
  if (!info || value == null) return null

  if (metricKey === 'direction_accuracy') {
    for (const t of info.thresholds) {
      if (value >= t.min) return { grade: t.grade, color: t.color }
    }
  } else {
    for (const t of info.thresholds) {
      if (value < t.max) return { grade: t.grade, color: t.color }
    }
  }
  return null
}

function MetricCard({ metricKey, value, unit = '' }) {
  const [showDetail, setShowDetail] = useState(false)
  const info = METRIC_INFO[metricKey]
  const gradeInfo = getGrade(metricKey, value)

  return (
    <div
      className="bg-gray-50 rounded-lg p-4 text-center cursor-pointer hover:bg-gray-100 transition-colors"
      onClick={() => setShowDetail(!showDetail)}
    >
      <div className="text-xs text-gray-500 mb-1">{info.label}</div>
      {value !== null && value !== undefined ? (
        <div className={`text-xl font-bold ${gradeInfo?.color || 'text-gray-900'}`}>
          {typeof value === 'number' ? value.toFixed(2) : value}{unit}
        </div>
      ) : (
        <div className="text-xl font-bold text-gray-400">-</div>
      )}
      {gradeInfo && (
        <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${
          gradeInfo.color === 'text-green-600' ? 'bg-green-100 text-green-700' :
          gradeInfo.color === 'text-yellow-600' ? 'bg-yellow-100 text-yellow-700' :
          gradeInfo.color === 'text-blue-600' ? 'bg-blue-100 text-blue-700' :
          'bg-red-100 text-red-700'
        }`}>
          {gradeInfo.grade}
        </span>
      )}
      <div className="text-xs text-blue-500 mt-1">
        {showDetail ? '접기' : '자세히 보기'}
      </div>

      {showDetail && (
        <div className="text-left mt-3 pt-3 border-t border-gray-200 space-y-2">
          <p className="text-xs text-gray-600">{info.description}</p>
          <p className="text-xs text-gray-500 italic">{info.interpretation}</p>
        </div>
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
  const [showMethodology, setShowMethodology] = useState(false)

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
      await loadData(ticker)
    } catch (err) {
      alert('업데이트 실패: ' + (err.response?.data?.detail || err.message))
    } finally {
      setUpdating(false)
    }
  }

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
    <div className="space-y-4">
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
              <MetricCard metricKey="mae" value={metrics?.mae} unit="$" />
              <MetricCard metricKey="mape" value={metrics?.mape} unit="%" />
              <MetricCard metricKey="rmse" value={metrics?.rmse} unit="$" />
              <MetricCard metricKey="direction_accuracy" value={metrics?.direction_accuracy} unit="%" />
            </div>

            {/* 오차 보정 정보 */}
            {correctionInfo && (
              <div className={`rounded-lg p-3 mb-4 text-sm ${
                correctionInfo.is_corrected ? 'bg-blue-50 text-blue-700' : 'bg-gray-50 text-gray-500'
              }`}>
                <div className="flex items-center gap-2">
                  <span>{correctionInfo.is_corrected ? '✓' : '○'}</span>
                  <span>
                    오차 보정: {correctionInfo.is_corrected
                      ? `적용 중 (계수: ${correctionInfo.factor > 0 ? '+' : ''}${(correctionInfo.factor * 100).toFixed(2)}%, 평균 오차 ${correctionInfo.avg_error_pct}%)`
                      : `비활성 (${correctionInfo.data_count}건 / 최소 5건 필요)`
                    }
                  </span>
                </div>
                {correctionInfo.is_corrected && (
                  <div className="mt-2 text-xs text-blue-600">
                    오차 보정은 과거 예측과 실제 가격의 차이를 분석하여 체계적인 편향을 보정합니다.
                    최근 예측에 더 높은 가중치를 부여하는 가중 이동평균 방식을 사용합니다.
                    최소 5건의 평가된 예측이 필요하며, 데이터가 쌓일수록 보정 정확도가 향상됩니다.
                  </div>
                )}
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
                    <Line type="monotone" dataKey="예측가" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                    <Line type="monotone" dataKey="실제가" stroke="#22c55e" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </>
        )}
      </div>

      {/* 분석 방법론 (접이식) */}
      <div className="bg-white rounded-lg shadow p-4">
        <button
          onClick={() => setShowMethodology(!showMethodology)}
          className="flex items-center justify-between w-full text-left"
        >
          <span className="text-sm font-semibold text-gray-700">분석 방법론</span>
          <span className="text-gray-400 text-xs">{showMethodology ? '접기' : '펼치기'}</span>
        </button>

        {showMethodology && (
          <div className="mt-3 pt-3 border-t border-gray-100 space-y-3 text-xs text-gray-600">
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">LSTM 예측 모델</h4>
              <p>LSTM(Long Short-Term Memory)은 시계열 데이터의 장기 패턴을 학습하는 딥러닝 모델입니다.
              과거 60일간의 데이터 패턴을 분석하여 미래 주가를 예측합니다.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">입력 데이터 (8개 특성)</h4>
              <p>거래량, RSI(14), MACD, 볼린저밴드(상단/하단), SMA(20), EMA(12), 종가를 사용합니다.
              이 지표들은 시장의 추세, 모멘텀, 변동성을 종합적으로 반영합니다.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">자동회귀 예측</h4>
              <p>각 예측 스텝에서 예측된 종가를 바탕으로 기술적 지표를 재계산하고,
              이를 다음 예측의 입력으로 사용하는 자동회귀(Autoregressive) 방식입니다.
              이를 통해 각 예측일의 값이 독립적으로 산출됩니다.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-700 mb-1">오차 보정 알고리즘</h4>
              <p>과거 예측과 실제 가격의 오차율을 분석하여 체계적 편향을 보정합니다.
              최소 5건의 평가된 예측이 필요하며, 최근 예측에 더 높은 가중치를 부여하는
              가중 이동평균(Weighted Moving Average) 방식을 사용합니다.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PredictionAccuracy
