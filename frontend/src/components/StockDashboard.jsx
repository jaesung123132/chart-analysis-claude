import React, { useState } from 'react'
import axios from 'axios'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import useFavorites from '../hooks/useFavorites'
import FavoriteGrid from './FavoriteGrid'
import FavoriteButton from './FavoriteButton'
import StockSearch from './StockSearch'
import PredictionAccuracy from './PredictionAccuracy'

function StockDashboard() {
  const [ticker, setTicker] = useState('AAPL')
  const [loading, setLoading] = useState(false)
  const [stockData, setStockData] = useState(null)
  const [indicators, setIndicators] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [signal, setSignal] = useState(null)
  const { favorites, toggleFavorite, isFavorite } = useFavorites()

  const fetchAllData = async (targetTicker = null) => {
    const tickerToFetch = targetTicker || ticker
    if (targetTicker) {
      setTicker(tickerToFetch)
    }
    setLoading(true)
    try {
      const [priceRes, indicatorRes, signalRes, predictionRes] = await Promise.all([
        axios.get(`/api/v1/stocks/${tickerToFetch}/prices?period=3mo`),
        axios.get(`/api/v1/stocks/${tickerToFetch}/indicators?summary=true`),
        axios.get(`/api/v1/stocks/${tickerToFetch}/signals`),
        axios.get(`/api/v1/predictions/${tickerToFetch}?days=7`)
      ])

      setStockData(priceRes.data.data)
      setIndicators(indicatorRes.data.data)
      setSignal(signalRes.data.data)
      setPrediction(predictionRes.data.data)
    } catch (error) {
      console.error('===== 전체 에러 객체 =====', error)
      console.error('에러 응답:', error.response)
      console.error('에러 메시지:', error.message)
      console.error('에러 설정:', error.config)

      let errorMessage = '알 수 없는 오류'
      if (error.response) {
        // 서버 응답 에러
        errorMessage = error.response.data?.detail || error.response.data?.message || `서버 에러 (${error.response.status})`
      } else if (error.request) {
        // 요청은 보냈지만 응답 없음
        errorMessage = '서버 응답 없음 - 백엔드가 실행 중인지 확인하세요'
      } else {
        // 요청 설정 중 에러
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

  const chartData = stockData?.prices?.slice(-30).map(p => ({
    date: new Date(p.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    price: p.close
  })) || []

  const predictionChartData = prediction?.predictions?.map(p => ({
    date: new Date(p.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    predicted: p.predicted_price
  })) || []

  const combinedChartData = [...chartData, ...predictionChartData]

  return (
    <div className="space-y-6">
      {/* 즐겨찾기 그리드 */}
      <FavoriteGrid favorites={favorites} onStockClick={handleFavoriteClick} />

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex gap-4 items-end">
          {/* 한글 자동완성 검색창 */}
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
              {signal?.overall_signal || '-'}
            </div>
          </div>
        </div>
      )}

      {stockData && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">{ticker} 주가 추이 및 AI 예측</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={combinedChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="price" stroke="#3b82f6" name="실제 가격" strokeWidth={2} />
              <Line type="monotone" dataKey="predicted" stroke="#ef4444" name="AI 예측" strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {prediction && (
        <div className="bg-white rounded-lg shadow p-6">
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
              return (
                <div key={idx} className="bg-blue-50 rounded p-3 text-center">
                  <div className="text-xs text-gray-600 mb-1">
                    {new Date(pred.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                  </div>
                  {hasCorrected ? (
                    <>
                      <div className="text-base font-bold text-blue-900">${pred.corrected_price.toFixed(2)}</div>
                      <div className="text-xs text-gray-400 line-through">${pred.predicted_price.toFixed(2)}</div>
                    </>
                  ) : (
                    <div className="text-lg font-bold text-blue-900">${pred.predicted_price.toFixed(2)}</div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 예측 정확도 분석 */}
      {ticker && <PredictionAccuracy ticker={ticker} />}

      {indicators && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">기술적 지표</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">추세</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>SMA(20)</span>
                  <span className="font-medium">${indicators.price.sma_20?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>SMA(50)</span>
                  <span className="font-medium">${indicators.price.sma_50?.toFixed(2)}</span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">변동성</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>BB 상단</span>
                  <span className="font-medium">${indicators.volatility.bb_upper?.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>BB 하단</span>
                  <span className="font-medium">${indicators.volatility.bb_lower?.toFixed(2)}</span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">거래량</h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>VWAP</span>
                  <span className="font-medium">${indicators.volume.vwap?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default StockDashboard
