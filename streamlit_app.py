import streamlit as st
import itertools
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from sympy import Rational, sqrt, simplify, latex
import pandas as pd
import os
import platform
import requests  # 추가
import tempfile  # 추가

st.title("확률분포 계산기")

# 한글 폰트 설정 시작

# 폰트 파일 다운로드 및 설정
@st.cache_data  # Streamlit 캐싱 데코레이터
def get_font():
    url = 'https://github.com/team-monolith-product/korean-font-collection/raw/master/NanumGothic.ttf'
    response = requests.get(url)
    # 임시 파일에 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ttf') as f:
        f.write(response.content)
        font_path = f.name
    # 폰트 매니저에 폰트 추가
    font_manager.fontManager.addfont(font_path)
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    return font_name

font_name = get_font()
plt.rcParams['font.family'] = font_name

# 마이너스 폰트 설정
plt.rcParams['axes.unicode_minus'] = False

# LaTeX 수식 렌더링 설정 (MathText 사용)
plt.rcParams['mathtext.fontset'] = 'dejavusans'

# 한글 폰트 설정 끝

# 사용자 입력
values_input = st.text_input("확률변수 값을 쉼표로 구분하여 입력하세요 (예: 1,2,3,4,5):")
probabilities_input = st.text_input("각 값에 대한 확률을 쉼표로 구분하여 입력하세요 (예: 4/15,3/15,1/15,3/15,4/15):")
n = st.number_input("표본의 크기를 입력하세요:", min_value=1, value=9, step=1)

if st.button("계산하기"):
    # 입력 값 처리
    try:
        values = [int(v.strip()) for v in values_input.split(',')]
        probabilities = [Rational(p.strip()) for p in probabilities_input.split(',')]

        # 입력된 값과 확률의 개수가 일치하는지 확인
        if len(values) != len(probabilities):
            st.error("오류: 값의 개수와 확률의 개수가 일치하지 않습니다.")
            st.stop()

        # 확률의 합이 1인지 확인
        if sum(probabilities) != 1:
            st.error("오류: 확률의 합이 1이 아닙니다.")
            st.stop()

        # 모평균 계산
        population_mean = sum(v * p for v, p in zip(values, probabilities))

        # 모분산 계산
        population_variance = sum(v**2 * p for v, p in zip(values, probabilities)) - population_mean**2

        # 모표준편차 계산
        population_std = simplify(sqrt(population_variance))

        st.subheader("모집단 특성")
        st.markdown(f"**모평균:** $\\displaystyle {latex(population_mean)}$")
        st.markdown(f"**모분산:** $\\displaystyle {latex(population_variance)}$")
        st.markdown(f"**모표준편차:** $\\displaystyle {latex(population_std)}$")

        # 모든 가능한 표본 생성 (중복 허용)
        all_samples = list(itertools.product(values, repeat=int(n)))

        # 표본평균과 그 확률 계산
        sample_mean_probs = {}
        for sample in all_samples:
            # 각 표본의 확률 계산
            sample_prob = 1
            for x in sample:
                idx = values.index(x)
                sample_prob *= probabilities[idx]
            # 표본평균 계산
            sample_mean = Rational(sum(sample), n)
            # 표본평균에 대한 확률 누적
            if sample_mean in sample_mean_probs:
                sample_mean_probs[sample_mean] += sample_prob
            else:
                sample_mean_probs[sample_mean] = sample_prob

        # 표본평균 분포 출력
        sample_means = sorted(sample_mean_probs.keys())
        sample_probs = [sample_mean_probs[mean] for mean in sample_means]

        # 표본평균의 평균, 분산, 표준편차 계산
        sample_mean_mean = sum(mean * prob for mean, prob in zip(sample_means, sample_probs))
        sample_mean_variance = sum(mean**2 * prob for mean, prob in zip(sample_means, sample_probs)) - sample_mean_mean**2
        sample_mean_std = simplify(sqrt(sample_mean_variance))

        st.subheader("표본평균의 특성")
        st.markdown(f"**평균:** $\\displaystyle {latex(sample_mean_mean)}$")
        st.markdown(f"**분산:** $\\displaystyle {latex(sample_mean_variance)}$")
        st.markdown(f"**표준편차:** $\\displaystyle {latex(sample_mean_std)}$")

        # 표본평균의 분포 그래프 그리기
        sample_means_float = [float(mean) for mean in sample_means]
        sample_probs_float = [float(prob) for prob in sample_probs]

        # x축 눈금 레이블용 LaTeX 수식 생성 (\\displaystyle 제거)
        sample_means_latex_labels = [f"${latex(mean)}$" for mean in sample_means]

        fig, ax = plt.subplots()
        ax.bar(sample_means_float, sample_probs_float, width=0.1, align='center', alpha=0.7)

        # x축 눈금 설정
        ax.set_xticks(sample_means_float)
        ax.set_xticklabels(sample_means_latex_labels, rotation=45, ha='right', fontsize=10)

        ax.set_xlabel("표본평균")
        ax.set_ylabel("확률")
        ax.set_title("표본평균의 분포")
        st.pyplot(fig)

        # 표본평균의 확률분포표 생성 및 출력
        st.subheader("표본평균의 확률분포표")

        # 테이블 생성 (\\displaystyle 유지)
        sample_means_latex = [f"$\\displaystyle {latex(mean)}$" for mean in sample_means]
        sample_probs_latex = [f"$\\displaystyle {latex(simplify(prob))}$" for prob in sample_probs]

        header_row = "| 표본평균 | " + " | ".join(sample_means_latex) + " |\n"
        separator_row = "|---" * (len(sample_means_latex) + 1) + "|\n"
        prob_row = "| 확률 | " + " | ".join(sample_probs_latex) + " |\n"

        table_md = header_row + separator_row + prob_row

        st.markdown(table_md)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
