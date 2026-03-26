import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linear_sum_assignment
import time

st.set_page_config(page_title="HANEUL: 예외대응 관제 시스템", layout="wide")

# --- [1. DB 및 프로필 관리 (소프트웨어학과: API/DB 모사)] ---
if 'workers' not in st.session_state:
    st.session_state.workers = pd.DataFrame({
        'ID': [f'Worker_{i+1}' for i in range(6)],
        'Level': ['숙련공', '신입', '숙련공', '신입', '전문가', '숙련공'],
        'Skill_Weight': [1.0, 0.7, 1.0, 0.7, 1.2, 1.0], # 산업공학: 숙련도 가중치
        'Safety_Margin': [1.0, 0.5, 1.0, 0.5, 1.0, 1.0], # 화학과: 신입 보호 마진(50%)
        'Color': ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3'],
        'Cum_Exp': [0.0] * 6,
        'is_present': [True] * 6 # 출근 여부
    })

# --- [2. 사이드바: 출근 및 가용성 관리 (소프트웨어학과: 키오스크 모듈)] ---
st.sidebar.header("🏢 현장 가용 인원 관리")
for i, row in st.session_state.workers.iterrows():
    st.session_state.workers.at[i, 'is_present'] = st.sidebar.checkbox(f"{row['ID']} ({row['Level']}) 출근", value=row['is_present'])

present_workers = st.session_state.workers[st.session_state.workers['is_present']].copy()
num_present = len(present_workers)

st.title("🛡️ 도장공정 예외대응 AI 배치 시스템")
st.info(f"현재 가용 인원: {num_present}명 / 부족 인원 발생 시 AI가 긴급 백업 플랜을 가동합니다.")

if num_present < 3:
    st.error("🚨 비상 모드: 최소 가동 인력 부족! 공정 중단을 검토하십시오.")
    st.stop()

# --- [3. 실시간 최적화 루프] ---
placeholder = st.empty()

while True:
    with placeholder.container():
        # 환경 데이터 생성 (2x3 부스)
        voc_matrix = np.random.randint(5, 100, (2, 3))
        booth_list = []
        for r in range(2):
            for c in range(3):
                booth_list.append({'ID': f'B_{len(booth_list)+1}', 'X': c+1, 'Y': 2-r, 'VOC': voc_matrix[r, c]})
        booths = pd.DataFrame(booth_list)

        # 4. 알고리즘 설계 (산업공학 + 화학 융합)
        # 인원 부족 시 상위 위험 부스부터 폐쇄하거나 멀티태스킹 적용
        active_booths = booths.iloc[:num_present] 
        
        cost_matrix = np.zeros((num_present, num_present))
        for i in range(num_present):
            for j in range(num_present):
                w = present_workers.iloc[i]
                b = active_booths.iloc[j]
                
                # [화학과 로직] 신입은 VOC 농도에 2배 더 민감하게 반응하도록 가중치 부여
                env_sensitivity = 2.0 if w['Level'] == '신입' else 1.0
                
                # [산업공학 로직] 숙련도(Skill_Weight)가 높을수록 고위험군 배정 효율 증가
                # 비용함수 = (개인민감도 * 환경농도) / 숙련도
                cost_matrix[i, j] = (env_sensitivity * b['VOC'] + w['Cum_Exp']) / w['Skill_Weight']

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # 5. UI 시각화 (소프트웨어학과: 긴급 알림 UI)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🌐 실시간 공정 디지털 트윈")
            fig = go.Figure()
            fig.add_trace(go.Heatmap(z=voc_matrix, x=[1,2,3], y=[1,2], colorscale='RdYlGn_r', zmin=0, zmax=100, opacity=0.5, showscale=True))
            
            for r, c in zip(row_ind, col_ind):
                w = present_workers.iloc[r]
                b = active_booths.iloc[c]
                # 실시간 노출량 업데이트
                st.session_state.workers.loc[st.session_state.workers['ID'] == w['ID'], 'Cum_Exp'] += b['VOC'] * 0.05
                
                fig.add_trace(go.Scatter(
                    x=[b['X']], y=[b['Y']], mode="markers+text",
                    marker=dict(size=45, color=w['Color'], line=dict(width=4, color='white')),
                    text=[f"<b>{w['ID']}</b><br>{w['Level']}"], textposition="middle center", showlegend=False
                ))
            fig.update_layout(width=700, height=450, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("⚠️ 실시간 안전 마진 모니터링")
            # [화학과: 안전 마진 체크] 신입은 50, 숙련공은 100이 한계
            status_data = []
            for i, w in present_workers.iterrows():
                # 실제 세션 상태의 최신 누적치 가져오기
                curr_exp = st.session_state.workers.loc[st.session_state.workers['ID'] == w['ID'], 'Cum_Exp'].values[0]
                limit = 100 * w['Safety_Margin']
                usage = (curr_exp / limit) * 100
                
                status_data.append({"작업자": w['ID'], "숙련도": w['Level'], "노출량": round(curr_exp, 1), "한도비율": f"{usage:.1f}%"})
                
                if usage > 80:
                    st.warning(f"❗ {w['ID']} ({w['Level']}): 안전 마진 80% 도달! 교대 준비")
            
            st.table(pd.DataFrame(status_data))

        time.sleep(2)
        st.rerun()
