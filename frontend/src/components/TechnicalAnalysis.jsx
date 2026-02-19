import React, { useState } from 'react'

const INDICATOR_HELP = {
  rsi: 'RSI(상대강도지수)는 일정 기간 동안의 가격 상승과 하락의 상대적 강도를 나타냅니다. 30 이하면 과매도(매수 기회), 70 이상이면 과매수(매도 시점) 신호로 해석합니다.',
  macd: 'MACD는 12일 EMA와 26일 EMA의 차이입니다. MACD가 시그널선을 상향 돌파하면 매수 신호, 하향 돌파하면 매도 신호입니다. 히스토그램이 양(+)이면 상승 모멘텀입니다.',
  ma: '이동평균선은 일정 기간의 평균 가격입니다. 주가가 이동평균선 위에 있으면 상승 추세, 아래에 있으면 하락 추세입니다. 단기(20일)가 장기(50일) 위에 있으면 강세입니다.',
  bb: '볼린저밴드는 이동평균에서 표준편차의 2배를 더하고 뺀 밴드입니다. 주가가 상단 밴드 근처면 과매수, 하단 밴드 근처면 과매도 상태로 볼 수 있습니다.',
  candle: '캔들 패턴은 하루의 시가/고가/저가/종가로 형성되는 모양에서 향후 주가 방향을 예측하는 기법입니다. 단일 또는 복수의 캔들 조합으로 상승/하락 반전 신호를 포착합니다.',
  cross: '골든크로스는 단기 이동평균이 장기 이동평균을 상향 돌파하는 것으로 상승 추세 전환 신호입니다. 데드크로스는 반대로 하향 돌파하는 것으로 하락 추세 전환 신호입니다.',
  sr: '지지선은 주가가 하락할 때 반등하는 가격대, 저항선은 상승할 때 눌리는 가격대입니다. 이 수준을 돌파하면 추세가 강화됩니다.',
}

function HelpToggle({ helpKey }) {
  const [show, setShow] = useState(false)
  const text = INDICATOR_HELP[helpKey]
  if (!text) return null

  return (
    <div className="mt-1">
      <button
        onClick={() => setShow(!show)}
        className="text-xs text-blue-500 hover:text-blue-700"
      >
        {show ? '설명 접기' : '이 지표는?'}
      </button>
      {show && (
        <p className="text-xs text-gray-500 mt-1 leading-relaxed">{text}</p>
      )}
    </div>
  )
}

function SignalBadge({ signal }) {
  if (!signal) return null
  const config = {
    BUY: { bg: 'bg-green-100', text: 'text-green-700', label: '매수' },
    SELL: { bg: 'bg-red-100', text: 'text-red-700', label: '매도' },
    NEUTRAL: { bg: 'bg-gray-100', text: 'text-gray-700', label: '중립' },
    bullish: { bg: 'bg-green-100', text: 'text-green-700', label: '상승' },
    bearish: { bg: 'bg-red-100', text: 'text-red-700', label: '하락' },
    reversal: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '반전' },
  }
  const c = config[signal] || config.NEUTRAL
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${c.bg} ${c.text}`}>{c.label}</span>
  )
}

function TechnicalAnalysis({ indicators, signal }) {
  if (!indicators) {
    return <div className="text-center py-8 text-gray-400">종목을 선택하세요</div>
  }

  const { momentum, trend, volatility, volume, price, candle_patterns, crosses, support_resistance, technical_score } = indicators

  return (
    <div className="space-y-4">
      {/* 기술적 분석 점수 */}
      {technical_score && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">기술적 분석 종합 점수</h3>
            <div className={`text-2xl font-bold ${
              technical_score.technical_score >= 70 ? 'text-green-600' :
              technical_score.technical_score >= 50 ? 'text-yellow-600' : 'text-red-600'
            }`}>
              {technical_score.technical_score} / 100
            </div>
          </div>
          {technical_score.details && (
            <div className="grid grid-cols-5 gap-2">
              {[
                { key: 'rsi', label: 'RSI' },
                { key: 'macd', label: 'MACD' },
                { key: 'ma', label: '이동평균' },
                { key: 'bb', label: '볼린저' },
                { key: 'pattern', label: '패턴' },
              ].map(({ key, label }) => (
                <div key={key} className="text-center">
                  <div className="text-xs text-gray-500">{label}</div>
                  <div className="font-bold text-sm">{technical_score.details[key] || 0}/20</div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                    <div
                      className={`h-1.5 rounded-full ${
                        (technical_score.details[key] || 0) >= 15 ? 'bg-green-500' :
                        (technical_score.details[key] || 0) >= 10 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${((technical_score.details[key] || 0) / 20) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 시그널 요약 */}
      {signal && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-800 mb-3">매매 시그널 요약</h3>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-sm text-gray-600">종합 시그널:</span>
            <span className={`text-lg font-bold ${
              signal.overall_signal === 'BUY' ? 'text-green-600' :
              signal.overall_signal === 'SELL' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {signal.overall_signal === 'BUY' ? '매수' : signal.overall_signal === 'SELL' ? '매도' : '중립'}
            </span>
          </div>
          <div className="space-y-2">
            {signal.signals?.map((s, i) => (
              <div key={i} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-700">{s.indicator}</span>
                  <SignalBadge signal={s.signal} />
                </div>
                <span className="text-xs text-gray-500">{s.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 주요 지표 상세 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-4">주요 지표</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* RSI */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">RSI (14)</span>
              <span className={`text-lg font-bold ${
                momentum?.rsi_14 > 70 ? 'text-red-600' :
                momentum?.rsi_14 < 30 ? 'text-green-600' : 'text-gray-900'
              }`}>
                {momentum?.rsi_14?.toFixed(1) || '-'}
              </span>
            </div>
            <div className="relative w-full bg-gray-200 rounded-full h-3">
              <div className="absolute inset-0 flex">
                <div className="w-[30%] bg-green-200 rounded-l-full" />
                <div className="w-[40%] bg-gray-200" />
                <div className="w-[30%] bg-red-200 rounded-r-full" />
              </div>
              {momentum?.rsi_14 != null && (
                <div
                  className="absolute top-0 w-2 h-3 bg-gray-800 rounded"
                  style={{ left: `${Math.min(100, Math.max(0, momentum.rsi_14))}%`, transform: 'translateX(-50%)' }}
                />
              )}
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>과매도 (&lt;30)</span>
              <span>중립</span>
              <span>과매수 (&gt;70)</span>
            </div>
            <HelpToggle helpKey="rsi" />
          </div>

          {/* MACD */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">MACD</span>
              <span className="text-lg font-bold text-gray-900">{trend?.macd?.toFixed(2) || '-'}</span>
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">시그널</span>
                <span>{trend?.macd_signal?.toFixed(2) || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">히스토그램</span>
                <span className={trend?.macd_histogram > 0 ? 'text-green-600' : 'text-red-600'}>
                  {trend?.macd_histogram?.toFixed(2) || '-'}
                </span>
              </div>
            </div>
            <HelpToggle helpKey="macd" />
          </div>

          {/* 이동평균 */}
          <div>
            <span className="text-sm font-medium text-gray-700">이동평균선</span>
            <div className="space-y-1 text-sm mt-2">
              {[
                { label: 'SMA(20)', value: price?.sma_20 },
                { label: 'SMA(50)', value: price?.sma_50 },
                { label: 'SMA(200)', value: price?.sma_200 },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between">
                  <span className="text-gray-500">{label}</span>
                  <span className={`font-medium ${
                    value && price?.close && price.close > value ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {value ? `$${value.toFixed(2)}` : '-'}
                  </span>
                </div>
              ))}
              <div className="flex justify-between pt-1 border-t">
                <span className="text-gray-500">현재가</span>
                <span className="font-bold">${price?.close?.toFixed(2) || '-'}</span>
              </div>
            </div>
            <HelpToggle helpKey="ma" />
          </div>

          {/* 볼린저밴드 */}
          <div>
            <span className="text-sm font-medium text-gray-700">볼린저밴드</span>
            <div className="space-y-1 text-sm mt-2">
              <div className="flex justify-between">
                <span className="text-gray-500">상단</span>
                <span className="text-red-500">${volatility?.bb_upper?.toFixed(2) || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">중간</span>
                <span>${volatility?.bb_middle?.toFixed(2) || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">하단</span>
                <span className="text-green-500">${volatility?.bb_lower?.toFixed(2) || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">ATR(14)</span>
                <span>${volatility?.atr_14?.toFixed(2) || '-'}</span>
              </div>
            </div>
            <HelpToggle helpKey="bb" />
          </div>
        </div>
      </div>

      {/* 캔들 패턴 */}
      {candle_patterns && candle_patterns.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-800 mb-3">캔들 패턴 감지</h3>
          <div className="space-y-2">
            {candle_patterns.map((p, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded">
                <SignalBadge signal={p.signal} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-800">{p.pattern_kr}</span>
                    <span className="text-xs text-gray-400">{p.date}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{p.description}</p>
                </div>
              </div>
            ))}
          </div>
          <HelpToggle helpKey="candle" />
        </div>
      )}

      {/* 크로스 이벤트 */}
      {crosses && crosses.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-800 mb-3">크로스 이벤트</h3>
          <div className="space-y-2">
            {crosses.map((c, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded">
                <SignalBadge signal={c.signal} />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-800">{c.type_kr}</span>
                    <span className="text-xs text-gray-400">{c.date}</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{c.description}</p>
                  <p className="text-xs text-gray-400">SMA(20): ${c.sma_20} / SMA(50): ${c.sma_50}</p>
                </div>
              </div>
            ))}
          </div>
          <HelpToggle helpKey="cross" />
        </div>
      )}

      {/* 지지선/저항선 */}
      {support_resistance && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-800 mb-3">지지선 / 저항선</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-xs text-gray-500 mb-2">저항선 (상방 압력)</div>
              <div className="space-y-1">
                {support_resistance.resistance?.slice(-3).reverse().map((r, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-red-500">R{i + 1}</span>
                    <span className="font-medium">${r}</span>
                  </div>
                ))}
              </div>
              {support_resistance.nearest_resistance && (
                <div className="mt-2 text-xs text-gray-500">
                  가장 가까운 저항선까지 +{support_resistance.resistance_distance_pct}%
                </div>
              )}
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-2">지지선 (하방 지지)</div>
              <div className="space-y-1">
                {support_resistance.support?.slice(-3).reverse().map((s, i) => (
                  <div key={i} className="flex justify-between text-sm">
                    <span className="text-green-500">S{i + 1}</span>
                    <span className="font-medium">${s}</span>
                  </div>
                ))}
              </div>
              {support_resistance.nearest_support && (
                <div className="mt-2 text-xs text-gray-500">
                  가장 가까운 지지선까지 -{support_resistance.support_distance_pct}%
                </div>
              )}
            </div>
          </div>
          <div className="mt-3 pt-3 border-t text-sm">
            <span className="text-gray-500">피봇 포인트: </span>
            <span className="font-medium">${support_resistance.pivot}</span>
            <span className="text-gray-400 mx-2">|</span>
            <span className="text-gray-500">현재가: </span>
            <span className="font-bold">${support_resistance.current_price}</span>
          </div>
          <HelpToggle helpKey="sr" />
        </div>
      )}
    </div>
  )
}

export default TechnicalAnalysis
