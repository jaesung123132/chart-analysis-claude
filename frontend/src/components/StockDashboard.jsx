import React, { useState } from 'react'
import axios from 'axios'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, Cell
} from 'recharts'
import useFavorites from '../hooks/useFavorites'
import FavoriteGrid from './FavoriteGrid'
import FavoriteButton from './FavoriteButton'
import StockSearch from './StockSearch'
import PredictionAccuracy from './PredictionAccuracy'
import FundamentalAnalysis from './FundamentalAnalysis'
import TechnicalAnalysis from './TechnicalAnalysis'
import InvestmentScore from './InvestmentScore'

// 날짜 포맷 유틸
const formatDate = (dateStr) =>
  new Date(dateStr).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })

// 탭 정의
const TABS = [
  { key: 'comprehensive', label: '종합 판단' },
  { key: 'fundamental', label: '기본적 분석' },
  { key: 'technical', label: '기술적 분석' },
  { key: 'prediction', label: 'AI 예측' },
  { key: 'accuracy', label: '정확도' },
]

function StockDashboard() {
  const [ticker, setTicker] = useState('AAPL')
  const [loading, setLoading] = useState(false)
  const [stockData, setStockData] = useState(null)
  const [indicators, setIndicators] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [signal, setSignal] = useState(null)
  const [predictionHistory, setPredictionHistory] = useState([])
  const [activeTab, setActiveTab] = useState('comprehensive')
  const { favorites, toggleFavorite, isFavorite } = useFavorites()

  const fetchAllData = async (targetTicker = null) => {
    const tickerToFetch = targetTicker || ticker
    if (targetTicker) {
      setTicker(tickerToFetch)
    }
    setLoading(true)
    try {
      const [priceRes, indicatorRes, signalRes, predictionRes, historyRes] = await Promise.all([
        axios.get(`/api/v1/stocks/${tickerToFetch}/prices?period=3mo`),
        axios.get(`/api/v1/stocks/${tickerToFetch}/indicators?summary=true`),
        axios.get(`/api/v1/stocks/${tickerToFetch}/signals`),
        axios.get(`/api/v1/predictions/${tickerToFetch}?days=7`),
        axios.get(`/api/v1/predictions/${tickerToFetch}/history?limit=30`).catch(() => ({ data: { data: { history: [] } } }))
      ])

      setStockData(priceRes.data.data)
      setIndicators(indicatorRes.data.data)
      setSignal(signalRes.data.data)
      setPrediction(predictionRes.data.data)
      setPredictionHistory(historyRes.data.data?.history || [])
    } catch (error) {
      console.error('데이터 조회 실패:', error)
      let errorMessage = '알 수 없는 오류'
      if (error.response) {
        errorMessage = error.response.data?.detail || error.response.data?.message || `서버 에러 (${error.response.status})`
      } else if (error.request) {
        errorMessage = '서버 응답 없음 - 백엔드가 실행 중인지 확인하세요'
      } else {
        errorMessage = error.message
      }
      alert('데이터 조회 실패: ' + errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleFavoriteClick = (selectedTicker) => {
    fetchAllData(selectedTicker)
  }

  // ========== 차트 데이터 병합 (개선) ==========
  const buildChartData = () => {
    if (!stockData?.prices) return []

    // 실제 가격을 Map에 저장
    const dataMap = new Map()
    const prices = stockData.prices.slice(-30)
    prices.forEach(p => {
      const date = formatDate(p.date)
      dataMap.set(date, { date, price: p.close })
    })

    // history API에서 평가 완료된 예측값을 같은 날짜에 병합
    predictionHistory
      .filter(h => h.actual_price !== null)
      .forEach(h => {
        const date = formatDate(h.target_date)
        if (dataMap.has(date)) {
          dataMap.get(date).predicted = h.predicted_price
        }
      })

    // 기존 데이터를 배열로 변환
    const result = Array.from(dataMap.values())

    // 미래 예측값 추가 (마지막 실제가 이후)
    if (prediction?.predictions) {
      // 마지막 실제가 포인트에 predicted = price 설정 (연결점)
      if (result.length > 0) {
        const lastPoint = result[result.length - 1]
        lastPoint.predicted = lastPoint.price
      }

      prediction.predictions.forEach(p => {
        const date = formatDate(p.date)
        result.push({
          date,
          predicted: p.corrected_price || p.predicted_price,
        })
      })
    }

    return result
  }

  const combinedChartData = buildChartData()

  // Feature importance 데이터
  const featureImportance = prediction?.feature_importance || []

  // 종합 등급 배지 (상단 표시용)
  const comprehensiveGrade = indicators ? (
    signal?.overall_signal === 'BUY' ? { label: '매수', color: 'bg-green-500' } :
    signal?.overall_signal === 'SELL' ? { label: '매도', color: 'bg-red-500' } :
    { label: '중립', color: 'bg-gray-500' }
  ) : null

  return (
    <div className="space-y-6">
      {/* 즐겨찾기 그리드 */}
      <FavoriteGrid favorites={favorites} onStockClick={handleFavoriteClick} />

      {/* 검색 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex gap-4 items-end">
          <StockSearch
            onSelect={(selectedTicker) => fetchAllData(selectedTicker)}
            initialValue={ticker}
          />
          <button
            onClick={() => fetchAllData()}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium whitespace-nowrap"
          >
            {loading ? '조회 중...' : '분석하기'}
          </button>
        </div>
      </div>

      {/* 상단 요약 (항상 표시) */}
      {indicators && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-500">현재가</div>
              <FavoriteButton
                ticker={ticker}
                isFavorite={isFavorite(ticker)}
                onToggle={toggleFavorite}
              />
            </div>
            <div className="text-2xl font-bold text-gray-900">${indicators.price.close.toFixed(2)}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">RSI (14)</div>
            <div className={`text-2xl font-bold ${indicators.momentum.rsi_14 > 70 ? 'text-red-600' : indicators.momentum.rsi_14 < 30 ? 'text-green-600' : 'text-gray-900'}`}>
              {indicators.momentum.rsi_14.toFixed(1)}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">MACD</div>
            <div className="text-2xl font-bold text-gray-900">{indicators.trend.macd.toFixed(2)}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">매매 시그널</div>
            <div className={`text-2xl font-bold ${signal?.overall_signal === 'BUY' ? 'text-green-600' : signal?.overall_signal === 'SELL' ? 'text-red-600' : 'text-gray-600'}`}>
              {signal?.overall_signal === 'BUY' ? '매수' : signal?.overall_signal === 'SELL' ? '매도' : '중립'}
            </div>
          </div>
        </div>
      )}

      {/* 탭 네비게이션 */}
      {indicators && (
        <div className="bg-white rounded-lg shadow">
          <div className="flex border-b overflow-x-auto">
            {TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-6 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.key
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="p-6">
            {/* 종합 판단 탭 */}
            {activeTab === 'comprehensive' && (
              <InvestmentScore ticker={ticker} />
            )}

            {/* 기본적 분석 탭 */}
            {activeTab === 'fundamental' && (
              <FundamentalAnalysis ticker={ticker} />
            )}

            {/* 기술적 분석 탭 */}
            {activeTab === 'technical' && (
              <TechnicalAnalysis indicators={indicators} signal={signal} />
            )}

            {/* AI 예측 탭 */}
            {activeTab === 'prediction' && (
              <div className="space-y-6">
                {/* 주가 추이 + AI 예측 차트 (병합) */}
                {stockData && (
                  <div>
                    <h2 className="text-lg font-bold text-gray-900 mb-4">{ticker} 주가 추이 및 AI 예측</h2>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={combinedChartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="price" stroke="#3b82f6" name="실제 가격" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="predicted" stroke="#ef4444" name="AI 예측" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* 7일 AI 예측 카드 */}
                {prediction && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-lg font-bold text-gray-900">7일 AI 예측 (LSTM 모델)</h2>
                      {prediction.correction_info?.is_corrected && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                          오차 보정 적용 중
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-7 gap-2">
                      {prediction.predictions.map((pred, idx) => {
                        const hasCorrected = pred.corrected_price && pred.corrected_price !== pred.predicted_price
                        const confidence = pred.confidence
                        const confColor = confidence >= 0.7 ? 'bg-green-100 text-green-700' :
                          confidence >= 0.4 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'

                        return (
                          <div key={idx} className="bg-blue-50 rounded p-3 text-center">
                            <div className="text-xs text-gray-600 mb-1">{formatDate(pred.date)}</div>
                            {hasCorrected ? (
                              <>
                                <div className="text-base font-bold text-blue-900">${pred.corrected_price.toFixed(2)}</div>
                                <div className="text-xs text-gray-400 line-through">${pred.predicted_price.toFixed(2)}</div>
                              </>
                            ) : (
                              <div className="text-lg font-bold text-blue-900">${pred.predicted_price.toFixed(2)}</div>
                            )}
                            {confidence != null && (
                              <span className={`text-xs px-1.5 py-0.5 rounded-full mt-1 inline-block ${confColor}`}>
                                {(confidence * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* 예측 근거: Feature Importance */}
                {featureImportance.length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-gray-800 mb-3">예측 근거 (Feature Importance)</h3>
                    <div className="space-y-2">
                      {featureImportance.map((fi, idx) => {
                        const isTop3 = idx < 3
                        const barColor = isTop3 ? 'bg-blue-500' : 'bg-gray-300'
                        const textColor = isTop3 ? 'text-gray-900' : 'text-gray-500'
                        return (
                          <div key={fi.feature} className="flex items-center gap-3">
                            <div className={`w-24 text-xs text-right ${textColor} font-medium`}>
                              {fi.feature}
                            </div>
                            <div className="flex-1 bg-gray-100 rounded-full h-4 relative">
                              <div
                                className={`h-4 rounded-full ${barColor} transition-all`}
                                style={{ width: `${Math.max(2, fi.importance * 100)}%` }}
                              />
                            </div>
                            <div className={`w-14 text-xs text-right ${textColor}`}>
                              {(fi.importance * 100).toFixed(1)}%
                            </div>
                          </div>
                        )
                      })}
                    </div>
                    <div className="mt-3 space-y-1">
                      {featureImportance.slice(0, 3).map(fi => (
                        <p key={fi.feature} className="text-xs text-gray-500">
                          <span className="font-medium text-gray-700">{fi.feature}</span>: {fi.description}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 정확도 탭 */}
            {activeTab === 'accuracy' && (
              <PredictionAccuracy ticker={ticker} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default StockDashboard
