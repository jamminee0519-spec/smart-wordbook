import streamlit as st
import json
import os
import re

# 로컬 저장용 JSON 파일 설정
DB_FILE = "vocabulary.json"

# [시스템] 앱 시작 시 데이터 불러오기 (세션 상태 관리)
if "vocab_data" not in st.session_state:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                st.session_state.vocab_data = json.load(f)
            except:
                st.session_state.vocab_data = []
    else:
        st.session_state.vocab_data = []

# [시스템] 데이터 저장 함수
def save_data():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.vocab_data, f, ensure_ascii=False, indent=4)

# --- UI 시작 ---
st.set_page_config(page_title="AI 스마트 단어장", page_icon="📝", layout="centered")
st.title("🤖 AI 자동 인식 스마트 단어장")
st.caption("찍거나 입력하면 자동으로 채워지고, 똑똑하게 외워지는 단어장")

# 기획서 우선순위 기반 탭 구성
tab1, tab2 = st.tabs(["📝 단어 추출 및 저장", "📚 내 단어장 관리"])

# --- [탭 1] 단어 추출 및 저장 ---
with tab1:
    st.subheader("1. 입력 소스 선택")
    source_type = st.radio("원하는 입력 방식을 선택하세요:", ["텍스트 직접 입력", "이미지 파일 업로드 (.jpg, .png)"])
    
    # 텍스트 입력 처리 (기획서 2.①.1단계 및 2단계 구현)
    if source_type == "텍스트 직접 입력":
        user_input = st.text_area("영어 문장이나 본문을 입력하면 단어를 자동으로 분리합니다.", 
                                  placeholder="Example: Artificial Intelligence is changing the world.")
        if st.button("🚀 단어 자동 인식 및 추출"):
            if user_input.strip():
                # 특수문자 제거 및 토큰화 (기획서 2.①.3단계 단어 정제 구현)
                clean_text = re.sub(r'[^\w\s]', '', user_input)
                raw_words = set(clean_text.lower().split())
                words_to_show = sorted([w for w in raw_words if w.isalpha()])
                
                # 임시 리스트 생성 (기획서 2.①.4단계 구현)
                st.session_state.temp_words = [{"word": w, "meaning": ""} for w in words_to_show]
            else:
                st.warning("텍스트를 입력해주세요!")
                
    # 이미지 업로드 처리 (OCR 데모 인터페이스 구현)
    elif source_type == "이미지 파일 업로드 (.jpg, .png)":
        uploaded_file = st.file_uploader("단어를 추출할 이미지를 업로드하세요", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            st.image(uploaded_file, caption="업로드된 이미지", use_container_width=True)
            if st.button("🔍 이미지에서 글자 추출 (OCR)"):
                st.info("💡 외부 유료 OCR API 연결 전 데모 모드: 이미지 내 주요 단어를 추출했습니다!")
                st.session_state.temp_words = [
                    {"word": "artificial", "meaning": "인공적인"},
                    {"word": "intelligence", "meaning": "지능"},
                    {"word": "vocabulary", "meaning": "단어장"}
                ]

    # [중요] 추출된 단어 선별 및 뜻 매칭 화면 (기획서 2.② 단어 선별 및 저장 기능 구현)
    if "temp_words" in st.session_state and st.session_state.temp_words:
        st.write("---")
        st.subheader("2. 임시 리스트 (저장할 단어 선택 및 뜻 수정)")
        st.caption("체크박스를 선택하고, 비어있는 뜻을 입력한 뒤 저장하세요.")
        
        updated_temp = []
        for i, item in enumerate(st.session_state.temp_words):
            col1, col2, col3 = st.columns([1, 2, 3])
            with col1:
                # 사용자 필터링 체크박스 (기획서 2.②.[1단계] 체크박스 배치 구현)
                is_checked = st.checkbox("선택", value=True, key=f"chk_{i}")
            with col2:
                st.write(f"**{item['word']}**")
            with col3:
                # 사전 API 대용 자동 추천 뜻 매칭 및 직접 수정 칸 (기획서 2.②.[1단계] 수정 칸 구현)
                mock_dict = {"artificial": "인공적인", "intelligence": "지능", "vocabulary": "단어장", "changing": "변화하는", "world": "세계", "example": "예시"}
                default_val = item['meaning'] if item['meaning'] else mock_dict.get(item['word'], "")
                meaning = st.text_input("뜻 수정/입력", value=default_val, key=f"mean_{i}")
            
            if is_checked:
                updated_temp.append({"word": item['word'], "meaning": meaning, "status": "미암기"})
        
        # 데이터베이스(JSON) 저장 버튼 (기획서 2.②.[2단계] DB 저장 구현)
        if st.button("💾 선택한 단어를 '내 단어장'에 저장하기"):
            existing_words = {x['word'] for x in st.session_state.vocab_data}
            added_count = 0
            for item in updated_temp:
                if item['word'] not in existing_words and item['meaning'].strip():
                    st.session_state.vocab_data.append(item)
                    added_count += 1
            save_data()
            st.success(f"🎉 {added_count}개의 새로운 단어가 내 단어장에 저장되었습니다!")
            del st.session_state.temp_words
            st.rerun()

# --- [탭 2] 내 단어장 관리 (기획서 2.③ 암기 여부 표시 및 상태 관리 구현) ---
with tab2:
    st.subheader("📚 내 단어장 목록 조회")
    
    if not st.session_state.vocab_data:
        st.info("아직 저장된 단어가 없습니다. 첫 번째 탭에서 단어를 추출하고 저장해 보세요!")
    else:
        # 필터링 보기 버튼 (기획서 2.③.[3단계] 필터링 보기 구현)
        filter_status = st.radio("필터링 보기:", ["전체 보기", "미암기 단어만 보기", "외운 단어만 보기"], horizontal=True)
        
        filtered_data = st.session_state.vocab_data
        if filter_status == "미암기 단어만 보기":
            filtered_data = [x for x in st.session_state.vocab_data if x['status'] == "미암기"]
        elif filter_status == "외운 단어만 보기":
            filtered_data = [x for x in st.session_state.vocab_data if x['status'] == "암기완료"]
            
        st.write("---")
        
        # 리스트 출력 및 토글 기능 (기획서 2.③.[1단계/2단계] 리스트 출력 및 토글 버튼 구현)
        for idx, item in enumerate(filtered_data):
            col1, col2, col3 = st.columns([2, 3, 2])
            orig_idx = st.session_state.vocab_data.index(item)
            
            with col1:
                if item['status'] == "암기완료":
                    st.write(f"~~{item['word']}~~")
                else:
                    st.write(f"**{item['word']}**")
            with col2:
                st.write(item['meaning'])
            with col3:
                # 암기완료 여부 상태 전환 버튼
                btn_label = "✅ 외웠어요" if item['status'] == "미암기" else "🔄 미암기 처리"
                if st.button(btn_label, key=f"toggle_{idx}_{orig_idx}"):
                    if item['status'] == "미amm기" or item['status'] == "미암기":
                        st.session_state.vocab_data[orig_idx]['status'] = "암기완료"
                    else:
                        st.session_state.vocab_data[orig_idx]['status'] = "미암기"
                    save_data()
                    st.rerun()
