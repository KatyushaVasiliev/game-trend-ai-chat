from statistics import mean
from ..schemas import Summary


def make_summary(rows: list[dict]) -> Summary:
    if not rows:
        return Summary(count=0, period_start=None, period_end=None, average=0, minimum=0, maximum=0, trend="insufficient", trend_detail="분석할 데이터가 없습니다.")
    values = [float(row["value"]) for row in rows]
    window = min(10, len(values) // 2)
    if window < 2:
        trend, detail = "insufficient", "추세 판단을 위한 데이터가 부족합니다."
    else:
        delta = mean(values[-window:]) - mean(values[:window])
        threshold = max(mean(values) * 0.03, 1)
        trend = "increase" if delta > threshold else "decrease" if delta < -threshold else "steady"
        labels = {"increase": "증가", "decrease": "감소", "steady": "유지"}
        detail = f"초기 {window}개 대비 최근 {window}개 평균이 {delta:+.1f}로 {labels[trend]} 추세입니다."
    return Summary(count=len(rows), period_start=rows[0]["date"], period_end=rows[-1]["date"], average=round(mean(values), 2), minimum=min(values), maximum=max(values), trend=trend, trend_detail=detail)
