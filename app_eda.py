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
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 지역별 인구 분석 EDA")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **Population Trends 데이터셋**  
        - 파일명: population_trends.csv  
        - 컬럼: 연도, 지역, 인구, 출생아수(명), 사망자수(명)  
        - 설명: 대한민국 각 시도별 연도별 인구 변화를 기록한 데이터
        ---
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
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        # 기본 전처리 및 변환
        mask = df['지역'] == '세종'
        df.loc[mask] = df.loc[mask].replace('-', 0)
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 지역명 영문 매핑
        eng_map = {
            '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
            '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi-do', '강원': 'Gangwon-do',
            '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
            '경남': 'Gyeongnam', '제주': 'Jeju'
        }
        df['Region_EN'] = df['지역'].map(eng_map).fillna(df['지역'])

        # 탭 구성
        tabs = st.tabs(["Basic Stats", "Time Trend", "Region Analysis", "Change Rate", "Visualization"])

        # 1) Basic Stats
        with tabs[0]:
            st.header("Data Preprocessing & Summary")
            st.subheader("Missing Values & Duplicates")
            st.write(df.isnull().sum())
            st.write(f"Duplicates: {df.duplicated().sum()}")
            st.subheader("Descriptive Statistics")
            st.write(df.describe())
            st.subheader("DataFrame Info")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())

        # 2) Time Trend
        with tabs[1]:
            st.header("National Population Trend & Forecast")
            national = df[df['지역'] == '전국'].groupby('연도')['인구'].sum().reset_index()
            last_year = national['연도'].max()
            recent = df[(df['지역'] == '전국') & (df['연도'].isin([last_year-2, last_year-1, last_year]))]
            avg_births = recent['출생아수(명)'].mean()
            avg_deaths = recent['사망자수(명)'].mean()
            avg_change = avg_births - avg_deaths
            forecast_years = list(range(last_year+1, 2036))
            forecast_vals = [national.loc[national['연도']==last_year, '인구'].values[0] + avg_change*(y-last_year) for y in forecast_years]
            forecast_df = pd.DataFrame({'연도': forecast_years, '인구': forecast_vals, 'Type': 'Forecast'})
            national['Type'] = 'Actual'
            plot_df = pd.concat([national, forecast_df], ignore_index=True)
            fig, ax = plt.subplots()
            for t, grp in plot_df.groupby('Type'):
                ax.plot(grp['연도'], grp['인구'], marker='o', label=t)
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.set_title('National Population Trend')
            ax.legend()
            st.pyplot(fig)

        # 3) Region Analysis
        with tabs[2]:
            st.header("5-Year Population Change by Region")
            recent_year = df['연도'].max()
            prev_year = recent_year - 5
            sel = df[df['연도'].isin([prev_year, recent_year])]
            pivot = sel.pivot(index='Region_EN', columns='연도', values='인구').drop('전국', errors=True)
            pivot['Change'] = pivot[recent_year] - pivot[prev_year]
            pivot['Change_k'] = pivot['Change']/1000
            pivot = pivot.sort_values('Change', ascending=False)
            fig2, ax2 = plt.subplots()
            sns.barplot(x='Change_k', y=pivot.index, data=pivot, ax=ax2)
            ax2.set_xlabel('Change (Thousands)')
            ax2.set_ylabel('Region')
            ax2.set_title('5-Year Population Change by Region')
            for i, (val,) in enumerate(pivot['Change_k'].items()):
                ax2.text(val, i, f"{val:.1f}", va='center')
            st.pyplot(fig2)
            st.markdown("This chart shows the 5-year population change for each region. Positive = growth, Negative = decline.")

        # 4) Change Rate
        with tabs[3]:
            st.header("Top 100 Population Changes")
            df_s = df[df['지역']!='전국'].sort_values(['Region_EN','연도'])
            df_s['diff'] = df_s.groupby('Region_EN')['인구'].diff()
            df_s['rate'] = df_s.groupby('Region_EN')['인구'].pct_change()
            top100 = df_s.dropna(subset=['diff']).nlargest(100, 'diff')[['Region_EN','연도','diff','rate']]
            def color_diff(val): return 'background-color: lightblue' if val>0 else 'background-color: lightcoral'
            styled = top100.style.applymap(color_diff, subset=['diff']).format({'diff':'{:,}','rate':'{:.2%}'})
            st.dataframe(styled)

        # 5) Visualization
        with tabs[4]:
            st.header("Population by Region Over Time (Area Chart)")
            pv = df.pivot_table(index='Region_EN', columns='연도', values='인구')
            fig3, ax3 = plt.subplots(figsize=(12,8))
            pv.T.plot.area(ax=ax3)
            ax3.set_xlabel('Year')
            ax3.set_ylabel('Population')
            ax3.set_title('Population by Region Over Time')
            st.pyplot(fig3)



# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()