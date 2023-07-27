import io
import locale
import os

import datetime
import streamlit as st
import pandas as pd
import zipfile
import tempfile
import shutil

from PackedMail import PackedMail
from TextRefiner import TextRefiner
from TextAnalyzer import TextAnalyzer

def create_session_state(key,default_value):
    assert default_value is not None
    # exec(f"st.session_state.{key} = st.session_state.get('{key}',default_value)")
    st.session_state[key] = st.session_state.get(key,default_value)
    if st.session_state.get(key) is None:
        # exec(f"st.session_state.{key} = default_value")
        st.session_state[key] = default_value

@st.cache_data
def packed_mails_from_zip(file):
    if file is not None:
        encodings = ('gbk','utf-8','gb2312')
        for encoding in encodings:
            try:
                with zipfile.ZipFile(file,metadata_encoding=encoding) as zf:
                    file_names = zf.namelist()
                    temp_dir = tempfile.mkdtemp()
                    zf.extractall(temp_dir)
                    break
            except UnicodeDecodeError as e:
                st.write(e)
        else:
            raise Exception(f"All decoding tries with {','.join(encodings)} failed.")

        mail_list = []
        for name in file_names:
            if name:
                packed = PackedMail(os.path.join(temp_dir,name))
                mail_list.append(packed)
        shutil.rmtree(temp_dir)
        mail_list.sort(key=lambda x: x.date)
        return mail_list

def render_display():
    mail = st.session_state.mail_list[st.session_state.current_page-1]
    st.write(str(mail),unsafe_allow_html=True)

def render_note():
    for key in st.session_state.result_dict:
        st.session_state.result_dict[key][st.session_state.current_page - 1] = \
        st.text_input(f"填写{key}的值#{key}{st.session_state.current_page}",
        key=f"{key}{st.session_state.current_page}",
        value=st.session_state.result_dict[key][st.session_state.current_page - 1])

def render_settings():
    st.title("配置界面")
    st.session_state.settings['escape'] = st.text_input("需转义",value=st.session_state.settings['escape']).strip()
    st.session_state.settings['filter_string'] = st.text_area("过滤信息",value=st.session_state.settings['filter_string']).strip()
    st.session_state.settings["stop_at"] = st.text_area("截断词",value=st.session_state.settings['stop_at']).strip()
    st.session_state.settings['replacement'] = st.text_area("替换用词",value=st.session_state.settings["replacement"]).strip()
    st.session_state.settings["keyword"] = st.text_area("统计词",value=st.session_state.settings["keyword"]).strip()
    st.session_state.settings["keyword_threshold"] = int(st.number_input('统计词阈值',min_value=1,format='%d',value=st.session_state.settings['keyword_threshold']))
    st.session_state.settings['note_keys'] = st.text_area('笔记栏目',value=st.session_state.settings['note_keys']).strip()

def render_page_btn(total_pages,key):
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        try:
            st.session_state.current_page = int(st.text_input('输入跳转',value=st.session_state.current_page,key=key))
        except ValueError:
            st.session_state.current_page = 1

        st.write(f'{st.session_state.current_page}/{total_pages}')
    with col1:
        if st.session_state.current_page > 1:
            if st.button("上一页",key=f'up{key}'):
                st.session_state.current_page -= 1
                st.experimental_rerun() # This is Magic
    with col3:
        if st.session_state.current_page < total_pages:
            if st.button("下一页",key=f'down{key}'):
                st.session_state.current_page += 1
                st.experimental_rerun() # This is also Magic

def setting_page():
    create_session_state('settings', {
        'escape': '',
        'filter_string': '',
        'stop_at': '',
        'replacement': '[OMITTED]',
        'keyword': '',
        'keyword_threshold': 1,
        'note_keys': 'A,B,C,D'
    })
    render_settings()
    # set result_dict to None to trigger a resetting
    # if st.session_state.get('result_dict'):
    st.session_state.result_dict = None
    #if st.session_state.get():
    st.session_state.mail_list = None

def reading_page():
    st.title('在线处理EML文件并导出笔记')
    uploaded = st.file_uploader("请选择要上传的ZIP文件", type=["zip"])
    if uploaded is not None:
        def generate_default_result_dict(total):
            result = {'File Name': [mail.file_name for mail in st.session_state.mail_list]}
            note_keys = st.session_state.settings['note_keys'].split(',')
            for key in note_keys:
                result[key] = [''] * total
            return result

        def download_btn(_total_pages):
            if True:
                if st.button("下载目前的进度"):
                    df = pd.DataFrame(st.session_state.result_dict)
                    st.dataframe(df)
                    st.download_button(
                        label="点击下载CSV文件",
                        data=df.to_csv(index=False,encoding=locale.getpreferredencoding()),
                        file_name=f"EML_Notes_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
                        mime="text/csv")
                if st.button("清除所有记录"):
                    st.session_state.result_dict = generate_default_result_dict(_total_pages)

        def process_mail_list(mail_list:list[PackedMail],_refiner:TextRefiner,_analyzer:TextAnalyzer):
            for mail in mail_list:
                mail.use_refiner(_refiner)
                mail.use_analyzer(_analyzer)

        refiner = TextRefiner()
        refiner.update_settings(st.session_state.settings)
        analyzer = TextAnalyzer()
        analyzer.update_settings(st.session_state.settings)
        create_session_state('mail_list', packed_mails_from_zip(uploaded))
        process_mail_list(st.session_state.mail_list,refiner,analyzer)

        total_pages = len(st.session_state.mail_list)
        create_session_state('current_page', 1)
        create_session_state('result_dict', generate_default_result_dict(total_pages))
        col1, col2 = st.columns([4,1])
        with col1:
            render_page_btn(total_pages, 1)
            render_display()
            render_page_btn(total_pages, 2)
        with col2:
            render_note()
        download_btn(total_pages)

def app():
    selected_page = st.sidebar.radio("Select Page", ["setting", "reading"])
    if selected_page == "setting":
        setting_page()
    else:
        st.empty()
        reading_page()

if __name__ == '__main__':
    app()