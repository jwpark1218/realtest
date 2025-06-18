import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self):
        st.title("🏠 Home")
        if st.session_state.logged_in:
            st.success("Population Trends EDA에 오신 것을 환영합니다.")
        st.markdown("""
        **Population Trends 데이터셋**  
        - 설명: 연도별 지역별 인구, 출생아수, 사망자수 데이터를 포함합니다.  
        - 분석: EDA 페이지에서 `population_trends.csv` 파일을 업로드하여 다양한 인구 분석을 수행할 수 있습니다.
        """)


# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
# ---------------------
# EDA 페이지 클래스: 탭 기반 분석 구조
# ---------------------
class EDA:
    def __init__(self):
        st.title("Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv to proceed.")
            return

        # CSV 읽기
        df = pd.read_csv(uploaded)

        # 전처리: '세종' 결측치 교체 및 숫자형 변환
        mask_sejong = df['지역'] == '세종'
        cols = ['인구', '출생아수(명)', '사망자수(명)']
        df.loc[mask_sejong, cols] = df.loc[mask_sejong, cols].replace('-', 0)
        df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
        df['출생아수(명)'] = pd.to_numeric(df['출생아수(명)'], errors='coerce')
        df['사망자수(명)'] = pd.to_numeric(df['사망자수(명)'], errors='coerce')

        # 탭 설정
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Basic Stats", "Yearly Trend", "Regional Analysis", "Change Analysis", "Visualization"
        ])

        # 1) Basic Stats
        with tab1:
            st.subheader("DataFrame Info")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())
            st.subheader("Summary Statistics")
            st.dataframe(df.describe())

        # 2) Yearly Trend
        with tab2:
            st.subheader("Yearly National Population Trend")
            df_nat = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            ax.plot(df_nat['연도'], df_nat['인구'], marker='o')
            ax.set_title("Yearly Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            # 2035 예측
            recent = df_nat.sort_values('연도').tail(3)
            avg_net = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
            last_pop = recent['인구'].iloc[-1]
            last_year = recent['연도'].iloc[-1]
            pop_2035 = last_pop + avg_net * (2035 - last_year)
            ax.scatter(2035, pop_2035, color='red')
            ax.annotate(f"{int(pop_2035):,}", (2035, pop_2035), textcoords="offset points", xytext=(0,10), ha='center')
            st.pyplot(fig)

        # 3) Regional Analysis
        with tab3:
            st.subheader("5-Year Population Change by Region")
            last_year = df['연도'].max()
            df5 = df[df['연도'].isin([last_year-4, last_year])]
            pivot5 = df5.pivot(index='지역', columns='연도', values='인구')
            diff5 = (pivot5[last_year] - pivot5[last_year-4]).drop('전국').sort_values(ascending=False)

            region_map = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju',
                '대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon',
                '충북':'Chungbuk','충남':'Chungnam','전북':'Jeonbuk','전남':'Jeonnam',
                '경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
            }
            names_en = [region_map[r] for r in diff5.index]
            diff5_k = diff5 / 1000

            fig2, ax2 = plt.subplots()
            sns.barplot(x=diff5_k, y=names_en, ax=ax2)
            ax2.set_title("5-Year Population Change")
            ax2.set_xlabel("Change (thousands)")
            ax2.set_ylabel("Region")
            for i, v in enumerate(diff5_k): ax2.text(v, i, f"{v:.1f}")
            st.pyplot(fig2)

            st.subheader("5-Year Population Change Rate by Region")
            rate5 = (diff5 / pivot5[last_year-4] * 100).sort_values(ascending=False)
            names_rate = [region_map[r] for r in rate5.index]
            fig2b, ax2b = plt.subplots()
            sns.barplot(x=rate5, y=names_rate, ax=ax2b)
            ax2b.set_title("5-Year Change Rate (%)")
            ax2b.set_xlabel("Rate (%)")
            ax2b.set_ylabel("Region")
            for i, v in enumerate(rate5): ax2b.text(v, i, f"{v:.1f}%")
            st.pyplot(fig2b)

        # 4) Change Analysis
        with tab4:
            st.subheader("Top 100 Year-over-Year Changes")
            df_sorted = df.sort_values(['지역','연도'])
            df_sorted['diff'] = df_sorted.groupby('지역')['인구'].diff()
            top100 = df_sorted[df_sorted['지역']!='전국'].nlargest(100, 'diff').dropna()
            top100['diff_fmt'] = top100['diff'].map(lambda x: f"{int(x):,}")
            top100['인구_fmt'] = top100['인구'].map(lambda x: f"{int(x):,}")
            styled = top100[['연도','지역','인구_fmt','diff_fmt']].style.applymap(
                lambda v: 'background-color: lightblue' if float(v.replace(',',''))>0 else 'background-color: lightcoral',
                subset=['diff_fmt']
            )
            st.dataframe(styled)

        # 5) Visualization
        with tab5:
            st.subheader("Population Distribution Over Time")
            pivot_full = df.pivot(index='연도', columns='지역', values='인구').drop(columns='전국')
            pivot_full = pivot_full.rename(columns=region_map)
            fig3, ax3 = plt.subplots(figsize=(10,6))
            pivot_full.plot.area(ax=ax3)
            ax3.set_title("Population by Region (Stacked Area)")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population")
            ax3.legend(title='Region', bbox_to_anchor=(1.05,1), loc='upper left')
            st.pyplot(fig3)

# 앱 실행
if __name__ == "__main__":
    st.set_page_config(page_title="Population Trends EDA")
    EDA()

# ---------------------
# 페이지 네비게이션
# ---------------------
PAGES = {
    "Home": Home,
    "Login": Login,
    "Register": lambda: Register("login"),
    "Find Password": FindPassword,
    "My Info": UserInfo,
    "Logout": Logout,
    "EDA": EDA
}

def main():
    st.sidebar.title("Navigation")
    if st.session_state.logged_in:
        choices = ["Home", "My Info", "Logout", "EDA"]
    else:
        choices = ["Home", "Login", "Register", "Find Password"]
    choice = st.sidebar.radio("Go to", choices)

    # 선택된 페이지 클래스 호출
    page = PAGES[choice]
    page()

if __name__ == "__main__":
    st.set_page_config(page_title="Population Trends EDA")
    main()
