import React, { useState, useEffect } from 'react'
import axios from 'axios'

// 지표 설명 상수
const INDICATOR_HELP = {
  per: 'PER(주가수익비율)은 주가를 주당순이익(EPS)으로 나눈 값입니다. 낮을수록 현재 이익 대비 주가가 저평가되어 있다고 볼 수 있습니다. 다만 업종마다 적정 PER이 다르므로 동종업계 비교가 중요합니다.',
  pbr: 'PBR(주가순자산비율)은 주가를 주당순자산으로 나눈 값입니다. 1 미만이면 자산가치보다 주가가 낮아 저평가 가능성이 있으며, 높을수록 시장의 기대가 크다는 의미입니다.',
  peg: 'PEG는 PER을 이익성장률로 나눈 값입니다. 1 미만이면 성장성 대비 저평가, 1 이상이면 고평가 가능성이 있습니다. 성장주 평가에 유용한 지표입니다.',
  margin: '이익률은 매출 대비 순이익의 비율입니다. 높을수록 수익성이 좋다는 의미이며, 업종별 차이가 크므로 동종업계 비교가 필요합니다.',
  revenue_growth: '매출 성장률은 전년 대비 매출이 얼마나 증가했는지를 나타냅니다. 양(+)이면 성장, 음(-)이면 역성장을 의미합니다.',
  debt_to_equity: '부채비율은 총부채를 자기자본으로 나눈 값입니다. 100% 이하가 일반적으로 양호하며, 200% 이상이면 재무 리스크가 높습니다.',
  current_ratio: '유동비율은 유동자산을 유동부채로 나눈 값입니다. 1.5 이상이면 단기 지급 능력이 양호하며, 1 미만이면 유동성 위험이 있습니다.',
  roe: 'ROE(자기자본이익률)는 자기자본 대비 순이익을 나타냅니다. 15% 이상이면 우수하며, 경영진의 자본 활용 효율성을 보여줍니다.',
  analyst: '애널리스트 목표가는 증권사 전문가들이 산출한 적정 주가 평균입니다. 현재가 대비 괴리율이 클수록 상승/하락 여력이 크다고 판단합니다.',
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

function ScoreGauge({ score, label }) {
  const color = score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
  const bgColor = score >= 70 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 36 36">
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none" stroke="#e5e7eb" strokeWidth="3"
          />
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none" stroke="currentColor"
            className={color}
            strokeWidth="3"
            strokeDasharray={`${score}, 100`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-xl font-bold ${color}`}>{score}</span>
          <span className="text-xs text-gray-400">/ 100</span>
        </div>
      </div>
      {label && <span className="text-xs text-gray-600 mt-1">{label}</span>}
    </div>
  )
}

function formatNumber(num) {
  if (num == null) return '-'
  if (num >= 1e12) return `${(num / 1e12).toFixed(1)}조`
  if (num >= 1e8) return `${(num / 1e8).toFixed(1)}억`
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
  return num.toLocaleString()
}

function formatPercent(val) {
  if (val == null) return '-'
  return `${(val * 100).toFixed(1)}%`
}

function AssessmentBadge({ text }) {
  if (!text || text === '정보 없음') return <span className="text-xs text-gray-400">{text}</span>

  const colorMap = {
    '저평가 가능성': 'bg-green-100 text-green-700',
    '자산가치 대비 저평가': 'bg-green-100 text-green-700',
    '성장성 대비 저평가': 'bg-green-100 text-green-700',
    '적정 수준': 'bg-blue-100 text-blue-700',
    '우수한 수익성': 'bg-green-100 text-green-700',
    '양호한 수익성': 'bg-blue-100 text-blue-700',
    '고성장': 'bg-green-100 text-green-700',
    '양호한 성장': 'bg-blue-100 text-blue-700',
    '매우 건전': 'bg-green-100 text-green-700',
    '양호': 'bg-blue-100 text-blue-700',
    '우수': 'bg-green-100 text-green-700',
    '강한 상승 여력': 'bg-green-100 text-green-700',
    '상승 여력 있음': 'bg-blue-100 text-blue-700',
    '다소 고평가': 'bg-yellow-100 text-yellow-700',
    '주의': 'bg-yellow-100 text-yellow-700',
    '보통': 'bg-gray-100 text-gray-700',
    '낮은 수익성': 'bg-yellow-100 text-yellow-700',
    '저성장': 'bg-yellow-100 text-yellow-700',
    '고평가 (높은 성장 기대)': 'bg-red-100 text-red-700',
    '자산가치 대비 고평가': 'bg-red-100 text-red-700',
    '성장성 대비 고평가': 'bg-red-100 text-red-700',
    '적자': 'bg-red-100 text-red-700',
    '역성장': 'bg-red-100 text-red-700',
    '위험 (고부채)': 'bg-red-100 text-red-700',
    '유동성 위험': 'bg-red-100 text-red-700',
    '하락 위험': 'bg-red-100 text-red-700',
  }

  const className = colorMap[text] || 'bg-gray-100 text-gray-700'

  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${className}`}>{text}</span>
  )
}

function FundamentalAnalysis({ ticker }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!ticker) return
    fetchData(ticker)
  }, [ticker])

  const fetchData = async (t) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get(`/api/v1/analysis/${t}/fundamental`)
      setData(res.data.data)
    } catch (err) {
      setError(err.response?.data?.detail || '기본적 분석 데이터 로드 실패')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-400">기본적 분석 중...</div>
  }
  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>
  }
  if (!data) {
    return <div className="text-center py-8 text-gray-400">종목을 선택하세요</div>
  }

  const { valuation, profitability, financial_health, analyst, fundamental_score } = data

  return (
    <div className="space-y-4">
      {/* 기본적 분석 종합 점수 */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">기본적 분석 종합</h3>
            <p className="text-sm text-gray-500">{data.company_name} ({data.sector})</p>
          </div>
          <ScoreGauge score={Math.round(fundamental_score)} label="기본적 점수" />
        </div>
      </div>

      {/* 가치 평가 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-4">가치 평가</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-xs text-gray-500">PER (후행)</div>
            <div className="text-lg font-bold text-gray-900">
              {valuation.trailing_pe != null ? valuation.trailing_pe.toFixed(1) : '-'}
            </div>
            <AssessmentBadge text={valuation.pe_assessment} />
            <HelpToggle helpKey="per" />
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">PER (선행)</div>
            <div className="text-lg font-bold text-gray-900">
              {valuation.forward_pe != null ? valuation.forward_pe.toFixed(1) : '-'}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">PBR</div>
            <div className="text-lg font-bold text-gray-900">
              {valuation.price_to_book != null ? valuation.price_to_book.toFixed(2) : '-'}
            </div>
            <AssessmentBadge text={valuation.pbr_assessment} />
            <HelpToggle helpKey="pbr" />
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">PEG</div>
            <div className="text-lg font-bold text-gray-900">
              {valuation.peg_ratio != null ? valuation.peg_ratio.toFixed(2) : '-'}
            </div>
            <AssessmentBadge text={valuation.peg_assessment} />
            <HelpToggle helpKey="peg" />
          </div>
        </div>
        <div className="mt-3 text-xs text-gray-500">
          시가총액: {formatNumber(valuation.market_cap)} ({valuation.cap_category})
        </div>
      </div>

      {/* 수익성 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-4">수익성</h3>
        <div className="space-y-3">
          {/* 마진율 바 */}
          {[
            { label: '영업이익률', value: profitability.operating_margins },
            { label: '순이익률', value: profitability.profit_margins },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">{label}</span>
                <span className="font-medium">{formatPercent(value)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${value != null && value > 0 ? 'bg-blue-500' : 'bg-red-400'}`}
                  style={{ width: `${Math.min(100, Math.max(0, (value || 0) * 100 + 10))}%` }}
                />
              </div>
            </div>
          ))}
          <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t">
            <div>
              <div className="text-xs text-gray-500">매출 성장률</div>
              <div className="text-base font-bold">{formatPercent(profitability.revenue_growth)}</div>
              <AssessmentBadge text={profitability.growth_assessment} />
            </div>
            <div>
              <div className="text-xs text-gray-500">EPS (주당순이익)</div>
              <div className="text-base font-bold">
                {profitability.trailing_eps != null ? `$${profitability.trailing_eps.toFixed(2)}` : '-'}
              </div>
            </div>
          </div>
          <AssessmentBadge text={profitability.margin_assessment} />
          <HelpToggle helpKey="margin" />
          <HelpToggle helpKey="revenue_growth" />
        </div>
      </div>

      {/* 재무 건전성 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-4">재무 건전성</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-xs text-gray-500">부채비율</div>
            <div className="text-lg font-bold text-gray-900">
              {financial_health.debt_to_equity != null ? `${financial_health.debt_to_equity.toFixed(0)}%` : '-'}
            </div>
            <AssessmentBadge text={financial_health.debt_assessment} />
            <HelpToggle helpKey="debt_to_equity" />
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">유동비율</div>
            <div className="text-lg font-bold text-gray-900">
              {financial_health.current_ratio != null ? financial_health.current_ratio.toFixed(2) : '-'}
            </div>
            <AssessmentBadge text={financial_health.liquidity_assessment} />
            <HelpToggle helpKey="current_ratio" />
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500">ROE</div>
            <div className="text-lg font-bold text-gray-900">
              {financial_health.return_on_equity != null ? `${(financial_health.return_on_equity * 100).toFixed(1)}%` : '-'}
            </div>
            <AssessmentBadge text={financial_health.roe_assessment} />
            <HelpToggle helpKey="roe" />
          </div>
        </div>
      </div>

      {/* 애널리스트 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-800 mb-4">애널리스트 의견</h3>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="text-xs text-gray-500 mb-2">목표가 vs 현재가</div>
            <div className="flex items-end gap-3">
              <div>
                <div className="text-xs text-gray-400">현재가</div>
                <div className="text-lg font-bold">${analyst.current_price?.toFixed(2) || '-'}</div>
              </div>
              <div className="text-gray-300 text-lg">→</div>
              <div>
                <div className="text-xs text-gray-400">목표가 (평균)</div>
                <div className="text-lg font-bold text-blue-600">${analyst.target_mean_price?.toFixed(2) || '-'}</div>
              </div>
            </div>
            {analyst.target_gap_pct != null && (
              <div className={`text-sm font-medium mt-1 ${analyst.target_gap_pct > 0 ? 'text-green-600' : 'text-red-600'}`}>
                괴리율: {analyst.target_gap_pct > 0 ? '+' : ''}{analyst.target_gap_pct}%
              </div>
            )}
            <AssessmentBadge text={analyst.target_assessment} />
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-2">추천 의견</div>
            <div className="text-lg font-bold text-gray-900">{analyst.recommendation_kr}</div>
            <div className="text-xs text-gray-400 mt-1">분석가 {analyst.num_analysts || 0}명</div>
            {analyst.target_low_price && analyst.target_high_price && (
              <div className="text-xs text-gray-500 mt-2">
                목표가 범위: ${analyst.target_low_price.toFixed(0)} ~ ${analyst.target_high_price.toFixed(0)}
              </div>
            )}
          </div>
        </div>
        <HelpToggle helpKey="analyst" />
      </div>
    </div>
  )
}

export default FundamentalAnalysis
